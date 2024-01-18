from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import model
from starlette.responses import RedirectResponse
from starlette import status
from db import engine
from Routers import auth, todos, users
from starlette.staticfiles import StaticFiles

app = FastAPI() 

model.Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return RedirectResponse(url="/auth/register", status_code=status.HTTP_302_FOUND)

app.include_router(auth.router)
app.include_router(todos.router)
app.include_router(users.router)