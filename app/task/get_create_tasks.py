from sqlalchemy.orm import Session
from starlette.requests import Request

from app import models
from app.models import Task
from app.task import schemas


def get_tasks_by_id(db: Session, task_id: int):
    return db.query(models.Task).filter(models.Task.id == task_id).first()


def get_tasks_by_title(db: Session, task_title: str):
    return db.query(models.Task).filter(models.Task.title == task_title).first()


def get_tasks_by_assigned_to(db: Session, user_id: int):
    return db.query(models.Task).filter(models.Task.assigned_to == user_id).first()


async def create_task(request: Request, db: Session, tasks: schemas.TaskCreate, created_by: int):
    tasks = Task(
        title=tasks.title,
        description=tasks.description,
        status=tasks.status,
        due_date=tasks.due_date,
        created_by=created_by
    )
    db.add(tasks)
    db.commit()
    db.refresh(tasks)
    return tasks


async def update_task(request: Request, db: Session, task: models.Task, task_data: dict):
    for key, value in task_data.items():
        setattr(task, key, value)
    db.commit()
    db.refresh(task)
    return task
