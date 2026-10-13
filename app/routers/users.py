from fastapi import APIRouter,HTTPException,status,Depends
from app.schemas import  Created_User,UpdateUser,UserWithProject,ResponseProjects
from app import models
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import Base,engine,get_db
from typing import Annotated


router = APIRouter()

mydb = Annotated[AsyncSession,Depends(get_db)]
#api  get -------------
@router.get("/",response_model=list[UserWithProject])
async def get_users(db:mydb):
    result = await db.execute(select(models.User).options(selectinload(models.User.projects)))
    existing = result.scalars().all()
    return existing


@router.get("/{user_id}/",response_model=UserWithProject)
async def get_unique_users(user_id:int,db:mydb):
    result = await db.execute(select(models.User)
                              .options(selectinload(models.User.projects))
                              .where(models.User.id == user_id))
    existing = result.scalars().first()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Böyle bir kullanıcı yok")

    return existing

@router.get("/{user_id}/projects/",response_model=list[ResponseProjects])
async def get_unique_users_projects(user_id:int,db:mydb):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    existing = result.scalars().first()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Böyle bir kullanıcı yok")

    result_project = await db.execute(select(models.Projects)
                                      .options(selectinload(models.Projects.owners),selectinload(models.Projects.tasks))
                                      .where(models.Projects.owner_id == user_id))
    existing_project = result_project.scalars().all()

    if not existing_project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Bu kullanıcıya ait projeler bulunmamaktadır")

    return existing_project


#api  post -------------
@router.post("/",response_model=UserWithProject,status_code=status.HTTP_201_CREATED)
async def created_user(user:Created_User,db:mydb):
    result = await db.execute(select(models.User).where(models.User.email == user.email))
    existing = result.scalars().first()

    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Böyle bir email var")

    new_user = models.User(
        name=user.name,
        email= user.email
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user,attribute_names=["projects"])
    return new_user

#api update
@router.patch("/{user_id}/",response_model=UserWithProject)
async def users_patch(user_id:int,db:mydb,user:UpdateUser):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    existing = result.scalars().first()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Güncellemek istediğiniz user_id sistemde bulunmamaktadır!!")

    if user.name is not None and user.name != existing.name:
        result_name = await db.execute(select(models.User).where(models.User.name == user.name))
        existing_name = result_name.scalars().first()
        if existing_name:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Böyle bir kullanıcı adı var")

    if user.email is not None and user.email != existing.email:
        result_email = await db.execute(select(models.User).where(models.User.email == user.email))
        existing_email = result_email.scalars().first()
        if existing_email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Böyle bir email adresi  var")

    if user.name is not None:
        existing.name = user.name
    if user.email is not None:
        existing.email = user.email

    await db.commit()
    await db.refresh(existing,attribute_names=["projects","updated_at"])
    return existing

#delete
@router.delete("/{user_id}/",status_code=status.HTTP_204_NO_CONTENT)
async def delete_users(user_id:int,db:mydb):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    existing = result.scalars().first()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Böyle bir user sistemde yok!")
    await db.delete(existing)
    await db.commit()
