from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# Проверочный эндпоинт
@app.get("/")
def read_root():
    return {"message": "API is working!"}

# Эндпоинт для добавления пользователя (тестовый)
@app.post("/add_user/")
def add_user():
    return {"message": "User added successfully!"}

# Эндпоинт для удаления пользователя (тестовый)
@app.delete("/delete_user/{target_server}/")
def delete_user(target_server: str):
    return {"message": f"User deleted successfully from {target_server}!"}
