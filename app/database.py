from sqlalchemy.ext.asyncio import create_async_engine,async_sessionmaker,AsyncSession
from sqlalchemy.orm import DeclarativeBase

SQL_DATABASE_URL = "sqlite+aiosqlite:///./task_flow.db"

engine = create_async_engine(url=SQL_DATABASE_URL,connect_args={"check_same_thread":False})

local_session = async_sessionmaker(bind=engine,class_=AsyncSession,expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with local_session() as db:
        yield db