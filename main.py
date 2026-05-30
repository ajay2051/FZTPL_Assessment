import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.custom_exceptions import register_all_errors
from app.db_connection import startup, shutdown
from config import MODE

version = "v1"


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Server Starting.....")
    await startup()
    yield
    await shutdown()
    print("Server Stopped.....")



app = FastAPI(
    title="Task Management API",
    description=f"{version} - Task Management REST API",
    version=version,
    lifespan=lifespan,
    docs_url=f"/api/{version}/docs",
    redoc_url=f"/api/{version}/redoc",
    contact={
        "name": "Task Management Pvt. Ltd.",
        "url": "http://127.0.0.1:8000/",
        "phone": "+977 9864915625",
        "email": "ajaythk.94@gmail.com",

    }
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def welcome_to_task_management():
    return {"message": "Welcome to Task Management API... 🙏🙏"}


register_all_errors(app)


if __name__ == "__main__":
    if MODE == "development":
        uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
    else:
        # For production, let the platform set the port
        port = int(os.getenv("PORT", 8000))
        uvicorn.run("main:app", host="127.0.0.1", port=port, reload=False)
