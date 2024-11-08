from fastapi import FastAPI

# Создаем экземпляр FastAPI
app = FastAPI()

# Простой эндпоинт для проверки
@app.get("/")
def read_root():
    return {"message": "API is working!"}