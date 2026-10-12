from __future__ import annotations
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from datetime import UTC,datetime

#USERS
class Users(BaseModel):

    name:str = Field(min_length=1,max_length=50)
    email: EmailStr = Field(min_length=1, max_length=200)

class UserResponse(Users):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime

class Created_User(Users):
    pass

class UpdateUser(BaseModel):
    name: str |None = Field(default=None,min_length=1, max_length=50)
    email: EmailStr | None = Field(default=None,min_length=1, max_length=200)

#PROJECTS
class Projects(BaseModel):

    owner_id:int
    name: str = Field(min_length=1, max_length=200)
class ResponseProjects(Projects):
    model_config = ConfigDict(from_attributes=True)
    id:int
    description: str |None = Field(default=None,min_length=1, max_length=500)
    created_at: datetime
    updated_at: datetime
    owners:UserResponse
    tasks: list[ResponseTasks] = []

class Created_Projects(Projects):
    description: str | None = Field(default=None, min_length=1, max_length=500)

class UpdateProjects(BaseModel):
    name: str|None = Field(default=None,min_length=1, max_length=200)
    description: str | None = Field(default=None, min_length=1, max_length=500)


#TASKS
class Tasks(BaseModel):

    project_id:int
    title:str = Field(min_length=1,max_length=75)

class ProjectSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id:int
    name:str
class ResponseTasks(Tasks):
    model_config = ConfigDict(from_attributes=True)
    id:int
    description:str|None = Field(default=None,min_length=1,max_length=200)
    status:str =Field(default="in_progress",min_length=1,max_length=30)
    priority:str |None = Field(default=None, min_length=1,max_length=20)
    created_at:datetime
    updated_at:datetime
    owner_tasks:ProjectSummary

class CreateTasks(Tasks):
    pass

class UpdateTasks(BaseModel):
    title: str |None = Field(default=None,min_length=1, max_length=75)
    description: str | None = Field(default=None, min_length=1, max_length=200)
    status: str| None = Field(default="in_progress", min_length=1, max_length=20)