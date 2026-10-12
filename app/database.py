from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase,sessionmaker

SQL_DATABASE_URL = "sqlite:///./task_flow.db"

engine = create_engine(url=SQL_DATABASE_URL,connect_args={"check_same_thread":False})

local_session = sessionmaker(bind=engine,autocommit =False,autoflush=False)

class Base(DeclarativeBase):
    pass

def get_db():
    with local_session() as db:
        yield db