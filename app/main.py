from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict

app = FastAPI()

# Данные для каждого сервера по стране
server_data: Dict[str, Dict[str, str]] = {
    "estonia": {"message": "User added successfully from Estonia!"},
    "germany": {"message": "User added successfully from Germany!"},
    "japan": {"message": "User added successfully from Japan!"}
}

# Проверочный эндпоинт
@app.get("/")
def read_root():
    return {"message": "API is working!"}

# Эндпоинт для добавления пользователя (тестовый)
@app.post("/add_user/{country}/")
def add_user(country: str):
    if country in server_data:
        return {"message": server_data[country]["message"]}
    return {"message": "Country not supported!"}

# Эндпоинт для удаления пользователя (тестовый)
@app.delete("/delete_user/{country}/{target_server}/")
def delete_user(country: str, target_server: str):
    return {"message": f"User deleted successfully from {target_server} in {country}!"}
