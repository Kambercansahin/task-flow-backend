from fastapi import APIRouter,HTTPException,status,Depends
from app.schemas import  CreateTasks, UpdateTasks,UserWithProject,ResponseTasksWithProject
from app import models

#SQLALCHEMY
#from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import Base,engine,get_db
from typing import Annotated

mydb = Annotated[AsyncSession,Depends(get_db)]

router = APIRouter()

@router.get("/",response_model=list[ResponseTasksWithProject])
async def get_tasks(db:mydb):
    result = await db.execute(select(models.Tasks).options(selectinload(models.Tasks.owner_tasks)))
    existing = result.scalars().all()
    return existing

@router.get("/{tasks_id}/",response_model=ResponseTasksWithProject)
async def get_unique_tasks(tasks_id:int,db:mydb):
    result = await db.execute(select(models.Tasks)
                              .options(selectinload(models.Tasks.owner_tasks))
                              .where(models.Tasks.id == tasks_id))
    existing = result.scalars().first()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Böyle bir task id yok!")
    return existing

#post
@router.post("/",response_model=ResponseTasksWithProject,status_code=status.HTTP_201_CREATED)
async def created_tasks(tasks:CreateTasks,db:mydb):
    result = await db.execute(select(models.Tasks)
                              .options(selectinload(models.Tasks.owner_tasks))
                              .where(models.Tasks.title == tasks.title))
    existing = result.scalars().first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Böyle bir task title var!")

    result_project = await db.execute(select(models.Projects).where(models.Projects.id == tasks.project_id))
    existing_project =result_project.scalars().first()

    if not existing_project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Böyle bir project_id yok")
    new_tasks = models.Tasks(
        project_id = tasks.project_id,
        title = tasks.title
    )
    db.add(new_tasks)
    await db.commit()
    await db.refresh(new_tasks,attribute_names=["owner_tasks"])
    return new_tasks

#Update put
@router.put("/{tasks_id}/",response_model=ResponseTasksWithProject)
async def put_tasks(tasks_id:int,db:mydb,tasks:CreateTasks):
    result = await db.execute(select(models.Tasks)
                              .options(selectinload(models.Tasks.owner_tasks))
                              .where(models.Tasks.id == tasks_id))
    existing = result.scalars().first()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Değiştirmek istedğiniz tasks id sistemde mevcut değil")

    if existing.project_id != tasks.project_id:
        result_project_id = await db.execute(select(models.Projects).where(models.Projects.id == tasks.project_id))
        existing_project_id = result_project_id.scalars().first()
        if not existing_project_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Değiştirmek istediğiniz project_id sistemde bulunmuyor")

    if tasks.project_id is not None:
        existing.project_id = tasks.project_id
    if tasks.title is not None:
        existing.title = tasks.title

    await db.commit()
    await db.refresh(existing,attribute_names=["owner_tasks","updated_at"])
    return existing


#update with patch
@router.patch("/{task_id}/",response_model=ResponseTasksWithProject)
async def patch_tasks(task_id:int,db:mydb,tasks:UpdateTasks):
    result = await db.execute(select(models.Tasks)
                              .options(selectinload(models.Tasks.owner_tasks))
                              .where(models.Tasks.id == task_id))
    existing = result.scalars().first()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Böyle bir task id yok!")

    if tasks.title is not None and tasks.title != existing.title:
        result_title = await db.execute(select(models.Tasks).where(models.Tasks.title == tasks.title))
        existing_title = result_title.scalars().first()
        if existing_title:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Bu title kullanılmaktadır")

    if tasks.title is not None:
        existing.title = tasks.title

    if tasks.description is not None:
        existing.description = tasks.description
    if tasks.status is not None:
        existing.status = tasks.status

    await db.commit()
    await db.refresh(existing,attribute_names=["owner_tasks","updated_at"])
    return existing

#delete ----
@router.delete("/{tasks_id}/",status_code=status.HTTP_204_NO_CONTENT)
async def delete_tasks(db:mydb,tasks_id:int):
    result = await db.execute(select(models.Tasks).where(models.Tasks.id == tasks_id))
    existing = result.scalars().first()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Böyle bir task yok")
    await db.delete(existing)
    await db.commit()