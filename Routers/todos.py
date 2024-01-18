import sys
sys.path.append("..")

from starlette import status
from starlette.responses import RedirectResponse
from fastapi import Depends, HTTPException, APIRouter, Request, Form
import model
from db import engine, SessionLocal
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel, Field
from .auth import get_current_user, get_user_exceptions
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


router = APIRouter(
    prefix="/todos",
    tags=["Todos"],
    responses={404: {"description": "Not Found"}}
)

model.Base.metadata.create_all(bind=engine)

templates = Jinja2Templates("templates")

 
def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

@router.get("/", response_class=HTMLResponse)
async def read_all_user(request: Request, db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)
    
    todos = db.query(model.Todos).filter(model.Todos.owner_id == user.get("id")).all()

    return templates.TemplateResponse("home.html", {"request":request, "todos":todos, "user":user})

@router.get("/add-todo", response_class=HTMLResponse)
async def add_new_todo(request: Request):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("add-todo.html", {"request":request, "user":user})

@router.post("/add-todo", response_class=HTMLResponse)
async def create_todo(request:Request, title: str = Form(...), description: str = Form(...), 
                      priority: int = Form(...), db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)
    todo_model = model.Todos()
    todo_model.title = title
    todo_model.description = description
    todo_model.priority = priority
    todo_model.complete = False
    todo_model.owner_id = user.get("id")

    db.add(todo_model)
    db.commit()
    return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)

@router.get("/edit-todo/{todo_id}", response_class=HTMLResponse)
async def edit_todo(request: Request, todo_id: int, db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)
    todo = db.query(model.Todos).filter(model.Todos.id == todo_id).first()

    return templates.TemplateResponse("edit-todo.html", {"request": request, "todo":todo, "user":user})

@router.post("/edit-todo/{todo_id}", response_class=HTMLResponse)
async def edit_todo_commit(request:Request, todo_id: int, title: str = Form(...), description: str = Form(...),
                           priority: int = Form(...), db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)
    todo_model = db.query(model.Todos).filter(model.Todos.id == todo_id).first()
    todo_model.title = title
    todo_model.description = description
    todo_model.priority = priority

    db.add(todo_model)
    db.commit()
    
    return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)

@router.get("/delete/{todo_id}")
async def delete_todo(request: Request, todo_id: int, db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)
    todo_model = db.query(model.Todos).filter(model.Todos.id == todo_id)\
    .filter(model.Todos.owner_id == user.get("id")).first()

    if todo_model is None:
        return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)
    
    db.query(model.Todos).filter(model.Todos.id == todo_id).delete()
    db.commit()

    return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)

@router.get("/complete/{todo_id}", response_class=HTMLResponse)
async def complete_todo(request: Request, todo_id: int, db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)
    todo = db.query(model.Todos).filter(model.Todos.id == todo_id).first()
    todo.complete = not todo.complete

    db.add(todo)
    db.commit()

    return RedirectResponse("/todos", status_code=status.HTTP_302_FOUND )
