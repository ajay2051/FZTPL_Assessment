import enum


class UserRole(enum.Enum):
    ADMIN = 'admin'
    MANAGER = 'manager'
    VENDOR = 'vendor'
    CUSTOMER = 'customer'