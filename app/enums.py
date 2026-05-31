import enum


class UserRole(enum.Enum):
    ADMIN = 'admin'
    MANAGER = 'manager'
    USER = 'user'


class TaskStatus(enum.Enum):
    PENDING = 'pending'
    COMPLETED = 'completed'
    IN_PROGRESS = 'in_progress'
