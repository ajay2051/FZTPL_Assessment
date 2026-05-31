from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator, Field


class UserResponse(BaseModel):
    id: int
    first_name: str
    last_name: str

    class Config:
        from_attributes = True


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=100)
    description: str = Field(..., min_length=5, max_length=500)
    status: str
    due_date: datetime

    @field_validator("status")
    @classmethod
    def validate_status(cls, value):
        allowed_statuses = ["pending", "in_progress", "completed"]

        if value.lower() not in allowed_statuses:
            raise ValueError(f"Status must be one of: {', '.join(allowed_statuses)}")

        return value.lower()

    @field_validator("due_date")
    @classmethod
    def validate_due_date(cls, value):
        if value < datetime.now():
            raise ValueError("Due date cannot be in the past")
        return value

    class Config:
        from_attributes = True


class TaskResponse(BaseModel):
    id: int
    title: str
    description: str
    status: str
    due_date: datetime
    assigned_to: int | None = None

    creator: UserResponse

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CreateTaskResponse(BaseModel):
    message: str = "Task Created Successfully! 👍👍."
    task: TaskResponse


class TaskStatusUpdate(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def validate_status(cls, value):
        allowed = ["pending", "in_progress", "completed"]

        value = value.lower()

        if value not in allowed:
            raise ValueError("Invalid status")

        return value
