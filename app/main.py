from fastapi import FastAPI,Request,HTTPException,status
from app.temp_info import mock_database

from fastapi.templating import Jinja2Templates
from pathlib import Path
from fastapi.exceptions import StarletteHTTPException
from fastapi.responses import JSONResponse

from app.schemas import UserResponse,Created_User,Created_Projects,ResponseProjects,CreateTasks,ResponseTasks


app = FastAPI()
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

@app.get("/",include_in_schema=False,name="home")
@app.get("/home/",include_in_schema=False)
def home(request:Request):
    users_dict = {"users":mock_database["users"]}
    return templates.TemplateResponse(request,"home.html",context=users_dict)


#USERS -----------

#api  get -------------
@app.get("/api/users/",response_model=list[UserResponse])
def get_users():
    return mock_database["users"]

@app.get("/api/users/{user_id}/",response_model=UserResponse)
def get_unique_users(user_id:int):
    for user in mock_database["users"]:
        if user.get("id") == user_id:
            return user

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Böyle bir kullanıcı yok")

#api  post -------------
@app.post("/api/users/",response_model=UserResponse)
def created_user(user:Created_User):
    new_user = {
        "id":user.id,
        "name":user.name,
        "email":user.email,
        "created_at":"10-10-26"
    }
    mock_database["users"].append(new_user)
    return new_user


#html----------
@app.get("/users/{user_id}",include_in_schema=False,name="users")
def get_unique_users_html(request:Request,user_id:int):
    for user in mock_database["users"]:
        if user.get("id") == user_id:
            user_dict = {"users":user}
            return templates.TemplateResponse(request,"users.html",context=user_dict)

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Böyle bir kullanıcı yok")


#PROJECTS-----------
@app.get("/api/projects/",response_model=list[ResponseProjects])
def get_projects():
    return mock_database["projects"]

@app.get("/api/projects/{project_id}/",response_model=ResponseProjects)
def get_unique_projects(project_id:int):
    for project in mock_database["projects"]:
        if project.get("id") == project_id:
            return project
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Böyle bir proje yok")

@app.post("/api/projects/",response_model=ResponseProjects)
def  created_projects(projects:Created_Projects):
    new_projects = {
        "id":projects.id,
        "owner_id":projects.owner_id,
        "name":projects.name,
    }
    mock_database["projects"].append(new_projects)
    return new_projects


#html-----
@app.get("/projects/",include_in_schema=False,name="projects")
def get_projects_html(request:Request):
    projects_dict = {"projects":mock_database["projects"]}
    return templates.TemplateResponse(request,"projects.html",context=projects_dict)

@app.get("/projects/{project_id}/",name="project",include_in_schema=False)
def get_unique_project_html(request:Request,project_id:int):
    for project in mock_database["projects"]:
        if project.get("id") == project_id:
            project_dict = {"project_unique":project}
            return templates.TemplateResponse(request,"project.html",context=project_dict)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Böyle bir proje yok")

#TASKS-----------
@app.get("/api/tasks/",response_model=list[ResponseTasks])
def get_tasks():
    return mock_database["tasks"]

@app.get("/api/tasks/{tasks_id}/",response_model=ResponseTasks)
def get_unique_tasks(tasks_id:int):
    for task in mock_database["tasks"]:
        if task.get("id") == tasks_id:
            return task

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Böyle bir task id yoktur!")

#post
@app.post("/api/tasks/",response_model=ResponseTasks)
def created_tasks(tasks:CreateTasks):
    new_tasks = {
        "id":tasks.id,
        "project_id":tasks.project_id,
        "title":tasks.title,

    }
    mock_database["tasks"].append(new_tasks)
    return new_tasks

#html
@app.get("/tasks/",include_in_schema=False,name="tasks")
def get_tasks_html(request:Request):
    tasks_dict = {"tasks":mock_database["tasks"]}
    return templates.TemplateResponse(request,"tasks.html",context=tasks_dict)

@app.get("/tasks/{tasks_id}/",include_in_schema=False,name="task")
def get_unique_task_html(tasks_id:int,request:Request):
    for task in mock_database["tasks"]:
        if task.get("id") == tasks_id:
            task_dict = {"task":task}
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



