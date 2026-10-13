from fastapi import FastAPI,Request,HTTPException,status,Depends
from app.temp_info import mock_database

from fastapi.templating import Jinja2Templates
from pathlib import Path
from fastapi.exceptions import StarletteHTTPException
from fastapi.responses import JSONResponse

from app import models

#SQLALCHEMY
#from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from contextlib import asynccontextmanager

from app.database import Base,engine,get_db
from typing import Annotated
#Routers
from app.routers import users,projects,tasks

#Base.metadata.create_all(bind=engine) We are deleting for use async

@asynccontextmanager
async def life_span(_app:FastAPI):
    #startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    #shutdown
    await engine.dispose()

app = FastAPI(lifespan=life_span)
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
#api router
app.include_router(router=users.router,prefix="/api/users",tags=["USERS"])
app.include_router(router=projects.router,prefix="/api/projects",tags=["PROJECTS"])
app.include_router(router=tasks.router,prefix="/api/tasks",tags=["TASKS"])

mydb = Annotated[AsyncSession,Depends(get_db)]

@app.get("/",include_in_schema=False,name="home")
@app.get("/home/",include_in_schema=False)
async def home(request:Request,db:mydb):
    result = await db.execute(select(models.User).options(selectinload(models.User.projects)))
    existing = result.scalars().all()
    users_dict = {"users":existing}
    return templates.TemplateResponse(request,"home.html",context=users_dict)


#USERS -----------
#html----------
@app.get("/users/{user_id}/",include_in_schema=False,name="users")
async def get_unique_users_html(request:Request,user_id:int,db:mydb):
    result = await db.execute(select(models.User)
                              .options(selectinload(models.User.projects))
                              .where(models.User.id == user_id))
    existing = result.scalars().first()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Böyle bir kullanıcı yoktur")

    user_dict = {"users":existing}
    return templates.TemplateResponse(request, "users.html", context=user_dict)

@app.get("/users/{users_id}/projects/",include_in_schema=False,name="user_project")
async  def get_unique_users_projects_html(request:Request,users_id:int,db:mydb):
    result = await db.execute(select(models.User)
                              .options(selectinload(models.User.projects))
                              .where(models.User.id == users_id))
    existing = result.scalars().first()

    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Böyle bir kullanıcı bulunmamaktadır")

    result_projects = await db.execute(select(models.Projects).where(models.Projects.owner_id == users_id))
    existing_projects = result_projects.scalars().first()
    if not existing_projects:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Kullanıcıya ait projeler yok!")

    return templates.TemplateResponse(request,"project.html",context={"project_unique":existing_projects})

#PROJECTS-----------

#html-----
@app.get("/projects/",include_in_schema=False,name="projects")
async def get_projects_html(request:Request,db:mydb):
    result = await db.execute(select(models.Projects).options(selectinload(models.Projects.owners),
                                                              selectinload(models.Projects.tasks)))
    existing = result.scalars().all()
    projects_dict = {"projects":existing}
    return templates.TemplateResponse(request,"projects.html",context=projects_dict)

@app.get("/projects/{project_id}/",name="project",include_in_schema=False)
async def get_unique_project_html(request:Request,project_id:int,db:mydb):
    result = await db.execute(select(models.Projects)
                              .options(selectinload(models.Projects.tasks),
                              selectinload(models.Projects.owners))
                              .where(models.Projects.id == project_id))
    existing = result.scalars().first()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Böyle bir proje yok")

    project_dict = {"project_unique":existing}
    return templates.TemplateResponse(request,"project.html",context=project_dict)

@app.get("/projects/{projects_id}/tasks/",name="project_tasks",include_in_schema=False)
async def get_unique_project_tasks_html(request:Request,projects_id:int,db:mydb):
    result = await db.execute(select(models.Projects).where(models.Projects.id == projects_id))
    existing = result.scalars().first()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Böyle bir proje yok")

    result_tasks = await db.execute(select(models.Tasks).where(models.Tasks.project_id == projects_id))
    existing_task = result_tasks.scalars().all()
    return templates.TemplateResponse(request,"task.html",context={"tasks":existing_task,"project":existing})

#TASKS-----------

#html
@app.get("/tasks/",include_in_schema=False,name="tasks")
async def get_tasks_html(request:Request,db:mydb):
    result = await db.execute(select(models.Tasks).options(selectinload(models.Tasks.owner_tasks)))
    existing = result.scalars().all()
    tasks_dict = {"tasks":existing}
    return templates.TemplateResponse(request,"tasks.html",context=tasks_dict)

@app.get("/tasks/{tasks_id}/",include_in_schema=False,name="task")
async def get_unique_task_html(tasks_id:int,request:Request,db:mydb):
    result = await db.execute(select(models.Tasks).where(models.Tasks.id ==tasks_id))
    existing = result.scalars().first()
    if existing:
        task_dict = {"tasks":[existing]}
        return templates.TemplateResponse(request,"task.html",context=task_dict)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Böyle bir tasks id bulunamadı!")


#error
@app.exception_handler(StarletteHTTPException)
async def general_http_exception_handler(request: Request, exception: StarletteHTTPException):
    message = (
        exception.detail
        if exception.detail
        else "ERROR "
    )

    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=exception.status_code,
            content={"detail": message},
        )

    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": exception.status_code,
            "title": exception.status_code,
            "message": message,
        },
        status_code=exception.status_code,
    )



