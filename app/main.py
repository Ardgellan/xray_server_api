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

# Эндпоинт для удаления пользователя (тестовый)
@app.delete("/delete_user/{target_server}/")
def delete_user(target_server: str):
    # Проверка, есть ли сервер в любом из списков
    for country, data in server_data.items():
        if target_server in data["servers"]:
            return {"message": f"User deleted successfully from {target_server} in {country}!"}

    # Если сервер не найден
    raise HTTPException(status_code=404, detail="Server not found")
