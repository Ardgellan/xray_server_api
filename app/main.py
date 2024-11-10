from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict

app = FastAPI()

# Данные для каждого сервера по стране
server_data: Dict[str, Dict[str, str]] = {
    "estonia": {"message": "User added successfully from Estonia!", "servers": ["estoniatest1", "estoniatest2"]},
    "germany": {"message": "User added successfully from Germany!", "servers": ["germanytest"]},
    "japan": {"message": "User added successfully from Japan!", "servers": ["japantest"]}
}

# Эндпоинт для добавления пользователя (тестовый)
@app.post("/add_user/{country}/")
def add_user(country: str):
    if country in server_data:
        return {"message": server_data[country]["message"]}
    raise HTTPException(status_code=404, detail="Country not supported")

# Упрощенный эндпоинт для удаления пользователя
@app.delete("/delete_user/{target_server}/")
def delete_user(target_server: str):
    # Простое подтверждение удаления без привязки к стране
    return {"message": f"User deleted successfully from {target_server}!"}