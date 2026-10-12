from fastapi import FastAPI,Request,HTTPException,status,Depends
from app.temp_info import mock_database

from fastapi.templating import Jinja2Templates
from pathlib import Path
from fastapi.exceptions import StarletteHTTPException
from fastapi.responses import JSONResponse

from app.schemas import UserResponse, Created_User, Created_Projects, ResponseProjects, CreateTasks, ResponseTasks, \
    UpdateUser,UpdateProjects,UpdateTasks
from app import models
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.database import Base,engine,get_db
from typing import Annotated

Base.metadata.create_all(bind=engine)

app = FastAPI()
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


mydb = Annotated[Session,Depends(get_db)]

@app.get("/",include_in_schema=False,name="home")
@app.get("/home/",include_in_schema=False)
def home(request:Request,db:mydb):
    result = db.execute(select(models.User))
    existing = result.scalars().all()
    users_dict = {"users":existing}
    return templates.TemplateResponse(request,"home.html",context=users_dict)


#USERS -----------

#api  get -------------
@app.get("/api/users/",response_model=list[UserResponse])
def get_users(db:mydb):
    result = db.execute(select(models.User))
    existing = result.scalars().all()
    return existing


@app.get("/api/users/{user_id}/",response_model=UserResponse)
def get_unique_users(user_id:int,db:mydb):
    result = db.execute(select(models.User).where(models.User.id == user_id))
    existing = result.scalars().first()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Böyle bir kullanıcı yok")

    return existing

@app.get("/api/users/{user_id}/projects/",response_model=list[ResponseProjects])
def get_unique_users_projects(user_id:int,db:mydb):
    result = db.execute(select(models.User).where(models.User.id == user_id))
    existing = result.scalars().first()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Böyle bir kullanıcı yok")

    result_project = db.execute(select(models.Projects).where(models.Projects.owner_id == user_id))
    existing_project = result_project.scalars().all()

    if not existing_project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Bu kullanıcıya ait projeler bulunmamaktadır")

    return existing_project


#api  post -------------
@app.post("/api/users/",response_model=UserResponse,status_code=status.HTTP_201_CREATED)
def created_user(user:Created_User,db:mydb):
    result = db.execute(select(models.User).where(models.User.email == user.email))
    existing = result.scalars().first()

    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Böyle bir email var")

    new_user = models.User(
        name=user.name,
        email= user.email
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

#api update
@app.patch("/api/users/{user_id}/",response_model=UserResponse)
def users_put(user_id:int,db:mydb,user:UpdateUser):
    result = db.execute(select(models.User).where(models.User.id == user_id))
    existing = result.scalars().first()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Güncellemek istediğiniz user_id sistemde bulunmamaktadır!!")

    if user.name is not None and user.name != existing.name:
        result_name = db.execute(select(models.User).where(models.User.name == user.name))
        existing_name = result_name.scalars().first()
        if existing_name:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Böyle bir kullanıcı adı var")

    if user.email is not None and user.email != existing.email:
        result_email = db.execute(select(models.User).where(models.User.email == user.email))
        existing_email = result_email.scalars().first()
        if existing_email:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Böyle bir email adresi  var")

    if user.name is not None:
        existing.name = user.name
    if user.email is not None:
        existing.email = user.email

    db.commit()
    db.refresh(existing)
    return existing

#delete
@app.delete("/api/users/{user_id}/",status_code=status.HTTP_204_NO_CONTENT)
def delete_users(user_id:int,db:mydb):
    result = db.execute(select(models.User).where(models.User.id == user_id))
    existing = result.scalars().first()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Böyle bir user sistemde yok!")
    db.delete(existing)
    db.commit()

#html----------
@app.get("/users/{user_id}/",include_in_schema=False,name="users")
def get_unique_users_html(request:Request,user_id:int,db:mydb):
    result = db.execute(select(models.User).where(models.User.id == user_id))
    existing = result.scalars().first()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Böyle bir kullanıcı yoktur")

    user_dict = {"users":existing}
    return templates.TemplateResponse(request, "users.html", context=user_dict)


#PROJECTS-----------
@app.get("/api/projects/",response_model=list[ResponseProjects])
def get_projects(db:mydb):
    result = db.execute(select(models.Projects))
    existing = result.scalars().all()
    return existing

@app.get("/api/projects/{project_id}/",response_model=ResponseProjects)
def get_unique_projects(project_id:int,db:mydb):
    result = db.execute(select(models.Projects).where(models.Projects.id == project_id))
    existing = result.scalars().first()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Böyle bir project id bulunmamaktadır")
    return existing

@app.get("/api/projects/{projects_id}/tasks/",response_model=list[ResponseTasks])
def get_unique_projects_tasks(projects_id:int,db:mydb):
    result = db.execute(select(models.Projects).where(models.Projects.id == projects_id))
    existing = result.scalars().first()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Böyle bir project id bulunmamaktadır!")

    result_task = db.execute(select(models.Tasks).where(models.Tasks.project_id == projects_id))
    existing_task = result_task.scalars().all()
    if not existing_task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Bu project id'ye ait tasks bulunmamaktadır!")

    return  existing_task

@app.post("/api/projects/",response_model=ResponseProjects,status_code=status.HTTP_201_CREATED)
def  created_projects(projects:Created_Projects,db:mydb):
    result = db.execute(select(models.Projects).where(models.Projects.name == projects.name))
    existing = result.scalars().first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Böyle bir proje adı bulunmamaktadır")

    result_owner_id = db.execute(select(models.User).where(models.User.id == projects.owner_id))
    existing_owner_id = result_owner_id.scalars().first()
    if not existing_owner_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Böyle bir Owner bilgisi bulunmamaktadır")


    new_projects = models.Projects(
        owner_id=projects.owner_id,
        name = projects.name,
        description = projects.description
    )
    db.add(new_projects)
    db.commit()
    db.refresh(new_projects)
    return new_projects

#api update with put
@app.put("/api/projects/{projects_id}/",response_model=ResponseProjects)
def put_projects(projects_id:int,db:mydb,projects:Created_Projects):
    result = db.execute(select(models.Projects).where(models.Projects.id == projects_id))
    existing = result.scalars().first()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Böyle bir project id yok")

    if projects.name != existing.name:
        result_name = db.execute(select(models.Projects).where(models.Projects.name == projects.name))
        existing_name = result_name.scalars().first()
        if existing_name:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bu proje adı kullanılmaktadır!")

    if projects.owner_id != existing.owner_id:
        result_id = db.execute(select(models.Projects).where(models.Projects.owner_id == projects.owner_id))
        existing_id = result_id.scalars().first()
        if not existing_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Böyle bir owner yok!!")

    existing.owner_id = projects.owner_id
    existing.name = projects.name
    existing.description = projects.description

    db.commit()
    db.refresh(existing)
    return existing

#app update with patch
@app.patch("/api/projects/{projects_id}/",response_model=ResponseProjects)
def patch_projects(projects_id:int,db:mydb,projects:UpdateProjects):
    result = db.execute(select(models.Projects).where(models.Projects.id == projects_id))
    existing = result.scalars().first()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Böyle bir proje yoK!")

    if projects.name is not None and projects.name != existing.name:
        result_name = db.execute(select(models.Projects).where(models.Projects.name == projects.name))
        existing_name = result_name.scalars().first()
        if existing_name:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Bu proje adı kullanılmaktadır!")

    if projects.name is not None:
        existing.name = projects.name

    if projects.description is not None:
        existing.description = projects.description
    db.commit()
    db.refresh(existing)
    return existing

#delete---
@app.delete("/api/projects/{projects_id}/",status_code=status.HTTP_204_NO_CONTENT)
def delete_projects(projects_id:int,db:mydb):
    result = db.execute(select(models.Projects).where(models.Projects.id == projects_id))
    existing = result.scalars().first()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Böyle bir project id yok!!")

    db.delete(existing)
    db.commit()

#html-----
@app.get("/projects/",include_in_schema=False,name="projects")
def get_projects_html(request:Request,db:mydb):
    result = db.execute(select(models.Projects))
    existing = result.scalars().all()
    projects_dict = {"projects":existing}
    return templates.TemplateResponse(request,"projects.html",context=projects_dict)

@app.get("/projects/{project_id}/",name="project",include_in_schema=False)
def get_unique_project_html(request:Request,project_id:int,db:mydb):
    result = db.execute(select(models.Projects).where(models.Projects.id == project_id))
    existing = result.scalars().first()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Böyle bir proje yok")

    project_dict = {"project_unique":existing}
    return templates.TemplateResponse(request,"project.html",context=project_dict)

@app.get("/projects/{project_id}/tasks/",name="project",include_in_schema=False)
def get_unique_project_html(request:Request,project_id:int,db:mydb):
    result = db.execute(select(models.Projects).where(models.Projects.id == project_id))
    existing = result.scalars().first()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Böyle bir proje yok")

    result_tasks = db.execute(select(models.Tasks).where(models.Tasks.project_id == project_id))
    existing_task = result_tasks.scalars().all()
    project_dict = {"task":existing_task}
    return templates.TemplateResponse(request,"task.html",context=project_dict)

#TASKS-----------
@app.get("/api/tasks/",response_model=list[ResponseTasks])
def get_tasks(db:mydb):
    result = db.execute(select(models.Tasks))
    existing = result.scalars().all()
    return existing

@app.get("/api/tasks/{tasks_id}/",response_model=ResponseTasks)
def get_unique_tasks(tasks_id:int,db:mydb):
    result = db.execute(select(models.Tasks).where(models.Tasks.id == tasks_id))
    existing = result.scalars().first()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Böyle bir task id yok!")
    return existing

#post
@app.post("/api/tasks/",response_model=ResponseTasks,status_code=status.HTTP_201_CREATED)
def created_tasks(tasks:CreateTasks,db:mydb):
    result = db.execute(select(models.Tasks).where(models.Tasks.title == tasks.title))
    existing = result.scalars().first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Böyle bir task title var!")

    new_tasks = models.Tasks(
        project_id = tasks.project_id,
        title = tasks.title
    )
    db.add(new_tasks)
    db.commit()
    db.refresh(new_tasks)
    return new_tasks

#Update put
@app.put("/api/tasks/{tasks_id}",response_model=ResponseTasks)
def put_tasks(tasks_id:int,db:mydb,tasks:CreateTasks):
    result = db.execute(select(models.Tasks).where(models.Tasks.id == tasks_id))
    existing = result.scalars().first()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Değiştirmek istedğiniz tasks id sistemde mevcut değil")

    if existing.project_id != tasks.project_id:
        result_project_id = db.execute(select(models.Tasks).where(models.Tasks.project_id == tasks.project_id))
        existing_project_id = result_project_id.scalars().first()
        if not existing_project_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Değiştirmek istediğiniz project_id sistemde bulunmuyor")

    if tasks.project_id is not None:
        existing.project_id = tasks.project_id
    if tasks.title is not None:
        existing.title = tasks.title

    db.commit()
    db.refresh(existing)
    return existing


#update with patch
@app.patch("/api/tasks/{task_id}/",response_model=ResponseTasks)
def patch_tasks(task_id:int,db:mydb,tasks:UpdateTasks):
    result = db.execute(select(models.Tasks).where(models.Tasks.id == task_id))
    existing = result.scalars().first()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Böyle bir task id yok!")

    if existing.title is not None and tasks.title != existing.title:
        result_title = db.execute(select(models.Tasks).where(models.Tasks.id == task_id))
        existing = result_title.scalars().first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Bu title kullanılmaktadır")

    if tasks.title is not None:
        existing.title = tasks.title

    if tasks.description is not None:
        existing.description = tasks.description
    if tasks.status is not None:
        existing.status = tasks.status

    db.commit()
    db.refresh(existing)
    return existing

#delete ----
@app.delete("/api/tasks/{tasks_id}/",status_code=status.HTTP_204_NO_CONTENT)
def delete_tasks(db:mydb,tasks_id:int):
    result = db.execute(select(models.Tasks).where(models.Tasks.id == tasks_id))
    existing = result.scalars().first()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Böyle bir kullanıcı yok")
    db.delete(existing)
    db.commit()
#html
@app.get("/tasks/",include_in_schema=False,name="tasks")
def get_tasks_html(request:Request,db:mydb):
    result = db.execute(select(models.Tasks))
    existing = result.scalars().all()
    tasks_dict = {"tasks":existing}
    return templates.TemplateResponse(request,"tasks.html",context=tasks_dict)

@app.get("/tasks/{tasks_id}/",include_in_schema=False,name="task")
def get_unique_task_html(tasks_id:int,request:Request,db:mydb):
    result = db.execute(select(models.Tasks).where(models.Tasks.id ==tasks_id))
    existing = result.scalars().first()
    if existing:
        task_dict = {"task":existing}
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



