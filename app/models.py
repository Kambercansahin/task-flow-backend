from __future__ import annotations
from sqlalchemy import DateTime,ForeignKey,Integer,String,Text
from sqlalchemy.orm import Mapped,mapped_column,relationship

from app.database import  Base
from datetime import UTC,datetime


class User(Base):
    __tablename__ = "users"

    id:Mapped[int] = mapped_column(Integer,primary_key=True,index=True)
    name:Mapped[str] = mapped_column(String(50),nullable=False)
    email:Mapped[str] = mapped_column(String(200),unique=True,nullable=False)
    created_at : Mapped[datetime] = mapped_column(DateTime(timezone=True),default=lambda:datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    projects:Mapped[list[Projects]] = relationship(back_populates="owners",cascade="all,delete-orphan")


class Projects(Base):
    __tablename__ = "projects"

    id:Mapped[int] = mapped_column(Integer,primary_key=True,index=True)
    # ForeignKey with user id
    owner_id:Mapped[int] = mapped_column(Integer,ForeignKey("users.id"),nullable=False,index=True)
    name:Mapped[str] = mapped_column(String(75),nullable=False)
    description:Mapped[str|None] = mapped_column(String(200),nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),default=lambda:datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    #Relation with user
    owners: Mapped[User] = relationship(back_populates="projects")
    # Relation with tasks
    tasks: Mapped[list[Tasks]] = relationship(back_populates="owner_tasks",cascade="all,delete-orphan")


class Tasks(Base):
    __tablename__ = "tasks"

    id:Mapped[int] = mapped_column(Integer,index=True,primary_key=True)
    #ForeignKeywith projects id
    project_id:Mapped[int] = mapped_column(Integer,ForeignKey("projects.id"),nullable=False,index=True)
    title:Mapped[str] = mapped_column(String(50),nullable=False)
    description:Mapped[str |None] = mapped_column(String(200),nullable=True)
    status:Mapped[str] = mapped_column(String(30),nullable=False,default="in_progress")
    priority:Mapped[str | None] = mapped_column(String(30),nullable=True)
    due_date:Mapped[datetime] = mapped_column(DateTime(timezone=True),default=lambda:datetime.now(UTC))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    # Relation with projects
    owner_tasks:Mapped[Projects] = relationship(back_populates="tasks")




