from pydantic import BaseModel, Field, EmailStr, ConfigDict

#USERS
class Users(BaseModel):
    id:int
    name:str = Field(min_length=1,max_length=50)
    email: EmailStr = Field(min_length=1, max_length=200)

class UserResponse(Users):
    model_config = ConfigDict(from_attributes=True)
    created_at:str

class Created_User(Users):
    pass

#PROJECTS
class Projects(BaseModel):
    id:int
    owner_id:int
    name: str = Field(min_length=1, max_length=200)
class ResponseProjects(Projects):
    description: str = Field(default=None,min_length=1, max_length=500)

class Created_Projects(Projects):
    pass


#TASKS
class Tasks(BaseModel):
    id:int
    project_id:int
    title:str = Field(min_length=1,max_length=75)

class ResponseTasks(Tasks):
    description:str = Field(default=None,min_length=1,max_length=200)
    status:str =Field(default="in_progress",min_length=1,max_length=20)
    priority:str = Field(default=None, min_length=1,max_length=20)

class CreateTasks(Tasks):
    pass
