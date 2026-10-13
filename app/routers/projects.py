from fastapi import APIRouter,HTTPException,status,Depends

from app.schemas import Created_Projects, ResponseProjects,UpdateProjects,ResponseTasks
from app import models

#SQLALCHEMY
#from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import Base,engine,get_db
from typing import Annotated

router = APIRouter()
mydb = Annotated[AsyncSession,Depends(get_db)]

@router.get("/",response_model=list[ResponseProjects])
async def get_projects(db:mydb):
    result = await db.execute(select(models.Projects).options(selectinload(models.Projects.tasks),
                                                              selectinload(models.Projects.owners)))
    existing = result.scalars().all()
    return existing

@router.get("/{project_id}/",response_model=ResponseProjects)
async def get_unique_projects(project_id:int,db:mydb):
    result = await db.execute(select(models.Projects)
                              .options(selectinload(models.Projects.owners),
                              selectinload(models.Projects.tasks)).where(models.Projects.id == project_id))
    existing = result.scalars().first()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Böyle bir project id bulunmamaktadır")
    return existing

@router.get("/{projects_id}/tasks/",response_model=list[ResponseTasks])
async def get_unique_projects_tasks(projects_id:int,db:mydb):
    result = await db.execute(select(models.Projects).where(models.Projects.id == projects_id))
    existing = result.scalars().first()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Böyle bir project id bulunmamaktadır!")

    result_task = await db.execute(select(models.Tasks).options(selectinload(models.Tasks.owner_tasks))
                                   .where(models.Tasks.project_id == projects_id))
    existing_task = result_task.scalars().all()
    if not existing_task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Bu project id'ye ait tasks bulunmamaktadır!")

    return  existing_task

@router.post("/",response_model=ResponseProjects,status_code=status.HTTP_201_CREATED)
async def  created_projects(projects:Created_Projects,db:mydb):
    result = await db.execute(select(models.Projects).where(models.Projects.name == projects.name))
    existing = result.scalars().first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Böyle bir proje adı bulunmaktadır")

    result_owner_id = await db.execute(select(models.User).where(models.User.id == projects.owner_id))
    existing_owner_id = result_owner_id.scalars().first()
    if not existing_owner_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Böyle bir Owner bilgisi bulunmamaktadır")


    new_projects = models.Projects(
        owner_id=projects.owner_id,
        name = projects.name,
        description = projects.description
    )
    db.add(new_projects)
    await db.commit()
    await db.refresh(new_projects,attribute_names=["tasks","owners"])
    return new_projects

#api update with put
@router.put("/{projects_id}/",response_model=ResponseProjects)
async def put_projects(projects_id:int,db:mydb,projects:Created_Projects):
    result = await db.execute(select(models.Projects).where(models.Projects.id == projects_id))
    existing = result.scalars().first()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Böyle bir project id yok")

    if projects.name != existing.name:
        result_name = await db.execute(select(models.Projects).where(models.Projects.name == projects.name))
        existing_name = result_name.scalars().first()
        if existing_name:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bu proje adı kullanılmaktadır!")

    if projects.owner_id != existing.owner_id:
        result_id = await db.execute(select(models.User).where(models.User.id == projects.owner_id))
        existing_id = result_id.scalars().first()
        if not existing_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Böyle bir owner yok!!")

    existing.owner_id = projects.owner_id
    existing.name = projects.name
    existing.description = projects.description

    await db.commit()
    await db.refresh(existing,attribute_names=["tasks","owners","updated_at"])
    return existing

#app update with patch
@router.patch("/{projects_id}/",response_model=ResponseProjects)
async def patch_projects(projects_id:int,db:mydb,projects:UpdateProjects):
    result = await db.execute(select(models.Projects).where(models.Projects.id == projects_id))
    existing = result.scalars().first()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Böyle bir proje yoK!")

    if projects.name is not None and projects.name != existing.name:
        result_name = await db.execute(select(models.Projects).where(models.Projects.name == projects.name))
        existing_name = result_name.scalars().first()
        if existing_name:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Bu proje adı kullanılmaktadır!")

    if projects.name is not None:
        existing.name = projects.name

    if projects.description is not None:
        existing.description = projects.description
    await db.commit()
    await db.refresh(existing,attribute_names=["tasks","owners","updated_at"])
    return existing

#delete---
@router.delete("/{projects_id}/",status_code=status.HTTP_204_NO_CONTENT)
async def delete_projects(projects_id:int,db:mydb):
    result = await db.execute(select(models.Projects).where(models.Projects.id == projects_id))
    existing = result.scalars().first()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Böyle bir project id yok!!")

    await db.delete(existing)
    await db.commit()
