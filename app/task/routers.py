from fastapi import APIRouter, Depends, HTTPException
from fastapi.params import Query
from sqlalchemy.orm import Session
from starlette import status
from starlette.requests import Request

from app.auth.dependencies import AllowedUsers
from app.auth.get_create_user import get_user_by_id
from app.auth.jwt_token import get_current_user
from app.custom_exceptions import TaskNotFound, TaskAlreadyExists, UserNotFound
from app.db_connection import get_db
from app.models import Task, User
from app.pagination import paginate
from app.task.get_create_tasks import create_task, get_tasks_by_id, update_task, get_tasks_by_title
from app.task.schemas import CreateTaskResponse, TaskCreate, TaskResponse, TaskStatusUpdate

task_router = APIRouter(tags=["task"])


@task_router.post("/create-tasks/", response_model=CreateTaskResponse)
async def create_tasks(request: Request, task: TaskCreate, db: Session = Depends(get_db), current_user: int = Depends(get_current_user),
                       _: bool = Depends(AllowedUsers(['admin', 'manager']))):
    try:
        task_data = TaskCreate(
            title=task.title,
            description=task.description,
            status=task.status,
            due_date=task.due_date,
        )
        existing_task = get_tasks_by_title(db, task.title)
        if existing_task:
            raise HTTPException(detail="Task with this title Already Exists!", status_code=status.HTTP_400_BAD_REQUEST)
        db_task = await create_task(request, db, task_data, current_user.id)
        return CreateTaskResponse(task=db_task)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error: {str(e)}")


@task_router.get("/tasks/")
async def get_tasks(
        request: Request,
        page: int = Query(1, ge=1, description="Page number"),
        per_page: int = Query(10, ge=1, le=100, description="Items per page"),
        title: str = Query(None, description="Filter by title"),
        status: str = Query(None, description="Filter by status type"),
        db: Session = Depends(get_db),
        current_user: int = Depends(get_current_user),
        _: bool = Depends(AllowedUsers(['admin', 'manager']))):
    query = db.query(Task)

    if title:
        query = query.filter(Task.title.ilike(f"%{title}%"))
    if status:
        query = query.filter(Task.status == status)
    total_objects = query.count()
    paginated_query = query.offset((page - 1) * per_page).limit(per_page)
    data = await paginate(model=Task, db=db, query=paginated_query, page=page, per_page=per_page, request=request, response_model_schema=TaskResponse, objects=total_objects)
    return {"message": "Task listed successfully...👍🔥", "data": data}


@task_router.get("/task/{id}/")
async def get_task(id: int, db: Session = Depends(get_db), current_user: int = Depends(get_current_user), _: bool = Depends(AllowedUsers(['admin', 'manager'])
                                                                                                                            )):
    task = get_tasks_by_id(db=db, task_id=id)
    if not task:
        raise TaskNotFound
    return {"message": "Task retrieved successfully...👍🔥", "data": task}


@task_router.get("/task-assigned-user/")
async def get_task_assigned_user(request: Request,
                                 page: int = Query(1, ge=1, description="Page number"),
                                 per_page: int = Query(10, ge=1, le=100, description="Items per page"),
                                 db: Session = Depends(get_db),
                                 current_user: int = Depends(get_current_user),
                                 _: bool = Depends(AllowedUsers(['user']))):
    query = db.query(Task).filter(Task.assigned_to == current_user.id)
    if not query:
        return {"message": "No Task Allocated"}
    total_objects = query.count()
    paginated_query = query.offset((page - 1) * per_page).limit(per_page)
    data = await paginate(model=Task, db=db, query=paginated_query, page=page, per_page=per_page, request=request, response_model_schema=TaskResponse, objects=total_objects)
    return {"message": "Task listed successfully...👍🔥", "data": data}


@task_router.patch("/task/{task_id}/{user_id}/")
async def assign_tasks(task_id: int, user_id: int, request: Request, db: Session = Depends(get_db), current_user: int = Depends(get_current_user),
                       _: bool = Depends(AllowedUsers(['admin', 'manager']))):
    task = get_tasks_by_id(db, task_id=task_id)
    if not task:
        raise TaskNotFound
    user = get_user_by_id(db, user_id=user_id)
    if not user:
        raise UserNotFound
    if user.role in ['admin', 'manager']:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Task Cannot be assigned to Admin/Manager")
    await update_task(request, db, task, {"assigned_to": user_id})
    return {"message": "Task assigned successfully...", "data": task}


@task_router.delete("/task/{task_id}/")
def delete_tasks(request: Request, task_id: int, db: Session = Depends(get_db), _: bool = Depends(AllowedUsers(['admin', 'manager']))):
    task = get_tasks_by_id(db, task_id=task_id)
    if not task:
        raise TaskNotFound
    db.delete(task)
    db.commit()
    return {"message": "Task deleted successfully...", }


SUPPORTED_STATUSES = ["pending", "in_progress", "completed"]


@task_router.patch("/status-update/{task_id}/")
def update_task_status(task_id: int, payload: TaskStatusUpdate, db: Session = Depends(get_db), _: bool = Depends(AllowedUsers(["user"]))):
    task = get_tasks_by_id(db, task_id=task_id)

    if not task:
        raise TaskNotFound

    new_status = payload.status.lower()
    current_status = task.status.lower()

    if new_status not in SUPPORTED_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status")

    if current_status == "completed" and new_status == "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Completed tasks cannot be moved back to pending")

    if current_status == new_status:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Task already has this status")

    task.status = new_status
    db.commit()
    db.refresh(task)

    return {
        "message": "Task status updated successfully",
        "task_id": task.id,
        "old_status": current_status,
        "new_status": new_status
    }
