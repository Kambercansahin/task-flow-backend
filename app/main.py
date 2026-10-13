from fastapi import FastAPI,Request,HTTPException,status,Depends
from app.temp_info import mock_database

from fastapi.templating import Jinja2Templates
from pathlib import Path
from fastapi.exceptions import StarletteHTTPException
from fastapi.responses import JSONResponse

from app.schemas import UserResponse, Created_User, Created_Projects, ResponseProjects, CreateTasks, ResponseTasks, \
    UpdateUser,UpdateProjects,UpdateTasks,UserWithProject,ResponseTasksWithProject
from app import models

#SQLALCHEMY
#from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from contextlib import asynccontextmanager

from app.database import Base,engine,get_db
from typing import Annotated

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


mydb = Annotated[AsyncSession,Depends(get_db)]

@app.get("/",include_in_schema=False,name="home")
@app.get("/home/",include_in_schema=False)
async def home(request:Request,db:mydb):
    result = await db.execute(select(models.User).options(selectinload(models.User.projects)))
    existing = result.scalars().all()
    users_dict = {"users":existing}
    return templates.TemplateResponse(request,"home.html",context=users_dict)


#USERS -----------

#api  get -------------
@app.get("/api/users/",response_model=list[UserWithProject])
async def get_users(db:mydb):
    result = await db.execute(select(models.User).options(selectinload(models.User.projects)))
    existing = result.scalars().all()
    return existing


@app.get("/api/users/{user_id}/",response_model=UserWithProject)
async def get_unique_users(user_id:int,db:mydb):
    result = await db.execute(select(models.User)
                              .options(selectinload(models.User.projects))
                              .where(models.User.id == user_id))
    existing = result.scalars().first()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Böyle bir kullanıcı yok")

    return existing

@app.get("/api/users/{user_id}/projects/",response_model=list[ResponseProjects])
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
@app.post("/api/users/",response_model=UserWithProject,status_code=status.HTTP_201_CREATED)
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
@app.patch("/api/users/{user_id}/",response_model=UserWithProject)
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
@app.delete("/api/users/{user_id}/",status_code=status.HTTP_204_NO_CONTENT)
async def delete_users(user_id:int,db:mydb):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    existing = result.scalars().first()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Böyle bir user sistemde yok!")
    await db.delete(existing)
    await db.commit()

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
@app.get("/api/projects/",response_model=list[ResponseProjects])
async def get_projects(db:mydb):
    result = await db.execute(select(models.Projects).options(selectinload(models.Projects.tasks),
                                                              selectinload(models.Projects.owners)))
    existing = result.scalars().all()
    return existing

@app.get("/api/projects/{project_id}/",response_model=ResponseProjects)
async def get_unique_projects(project_id:int,db:mydb):
    result = await db.execute(select(models.Projects)
                              .options(selectinload(models.Projects.owners),
                              selectinload(models.Projects.tasks)).where(models.Projects.id == project_id))
    existing = result.scalars().first()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Böyle bir project id bulunmamaktadır")
    return existing

@app.get("/api/projects/{projects_id}/tasks/",response_model=list[ResponseTasks])
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

@app.post("/api/projects/",response_model=ResponseProjects,status_code=status.HTTP_201_CREATED)
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
@app.put("/api/projects/{projects_id}/",response_model=ResponseProjects)
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
@app.patch("/api/projects/{projects_id}/",response_model=ResponseProjects)
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
@app.delete("/api/projects/{projects_id}/",status_code=status.HTTP_204_NO_CONTENT)
async def delete_projects(projects_id:int,db:mydb):
    result = await db.execute(select(models.Projects).where(models.Projects.id == projects_id))
    existing = result.scalars().first()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Böyle bir project id yok!!")

    await db.delete(existing)
    await db.commit()

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
@app.get("/api/tasks/",response_model=list[ResponseTasksWithProject])
async def get_tasks(db:mydb):
    result = await db.execute(select(models.Tasks).options(selectinload(models.Tasks.owner_tasks)))
    existing = result.scalars().all()
    return existing

@app.get("/api/tasks/{tasks_id}/",response_model=ResponseTasksWithProject)
async def get_unique_tasks(tasks_id:int,db:mydb):
    result = await db.execute(select(models.Tasks)
                              .options(selectinload(models.Tasks.owner_tasks))
                              .where(models.Tasks.id == tasks_id))
    existing = result.scalars().first()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Böyle bir task id yok!")
    return existing

#post
@app.post("/api/tasks/",response_model=ResponseTasksWithProject,status_code=status.HTTP_201_CREATED)
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
@app.put("/api/tasks/{tasks_id}/",response_model=ResponseTasksWithProject)
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
@app.patch("/api/tasks/{task_id}/",response_model=ResponseTasksWithProject)
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
@app.delete("/api/tasks/{tasks_id}/",status_code=status.HTTP_204_NO_CONTENT)
async def delete_tasks(db:mydb,tasks_id:int):
    result = await db.execute(select(models.Tasks).where(models.Tasks.id == tasks_id))
    existing = result.scalars().first()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Böyle bir task yok")
    await db.delete(existing)
    await db.commit()
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



