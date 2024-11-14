from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
from typing import Dict
from loguru import logger
from app.data import config

from app.xray import xray_config

app = FastAPI()

# Данные для каждого сервера по стране
server_data: Dict[str, Dict[str, str]] = {
    "estonia": {"message": "User added successfully from Estonia!", "servers": ["estoniatest1", "estoniatest2"]},
    "germany": {"message": "User added successfully from Germany!", "servers": ["germanytest"]},
    "japan": {"message": "User added successfully from Japan!", "servers": ["japantest"]}
}

logger.add("logs/app_{time}.log", rotation="10 MB", compression="zip")

@app.post("/add_user/{country}/")
async def add_user(country: str, user_id: int, config_name: str):
    logger.info(f"Received request for {country} with user_id={user_id} and config_name={config_name}, Salam")
    if country in server_data:
        try:
            # Вызов функции для добавления нового пользователя
            user_link, config_uuid = await xray_config.add_new_user(config_name=config_name, user_telegram_id=user_id)
            server_domain = config.domain_name
            server_country = config.server_country  # Название страны
            server_country_code = config.server_country_code  # Код страны

            # Передаем данные в ответе
            return {
                "message": server_data[country]["message"],
                "link": user_link,
                "config_uuid": config_uuid,  # UUID передаем в ответ
                "server_domain": server_domain,
                "server_country": server_country,  # Отправляем название страны
                "server_country_code": server_country_code  # Отправляем код страны
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to add user: {str(e)}")
    else:
        raise HTTPException(status_code=404, detail="Country not supported")


@app.post("/reactivate_configs/{target_server}/")
async def reactivate_configs(
    target_server: str, 
    config_uuids: list[str] = Body(..., embed=True)
):
    """
    Эндпоинт для восстановления конфигов пользователей по их UUID.
    Принимаем список UUID и передаем в функцию восстановления.
    """
    try:
        # Вызов функции восстановления
        success = await xray_config.reactivate_user_configs_in_xray(config_uuids=config_uuids)

        if success:
            return {"status": "success", "message": "Конфиги успешно восстановлены."}
        else:
            raise HTTPException(status_code=500, detail="Не удалось восстановить конфиги.")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")


@app.get("/show_specified_config/{target_server}/")
async def show_specified_config(target_server: str, config_uuid: str, config_name: str):
    """Создать конфигурационную ссылку и вернуть её"""
    try:
        # Вызываем функцию для создания ссылки
        config_link = await xray_config.create_user_config_as_link_string(
            uuid=config_uuid,
            config_name=config_name
        )
        
        # Возвращаем сгенерированную ссылку
        return {"config_link": config_link}

    except Exception as e:
        logger.error(f"Ошибка при создании ссылки конфигурации: {str(e)}")
        raise HTTPException(status_code=500, detail="Не удалось создать ссылку конфигурации")


# # Упрощенный эндпоинт для удаления пользователя
# @app.delete("/delete_user/{target_server}/")
# def delete_user(target_server: str):
#     # Простое подтверждение удаления без привязки к стране
#     return {"message": f"User deleted successfully from {target_server}!"}


@app.delete("/delete_config/{target_server}/")
async def delete_config(target_server: str, config_uuid: str):
    """
    Эндпоинт для удаления конфига по UUID.
    """
    try:
        # Здесь вызываем функцию для удаления конфига, которая может взаимодействовать с сервером или БД
        success = await xray_config.disconnect_user_by_uuid(uuid=config_uuid)
        
        if success:
            return {"status": "success", "message": "Конфиг успешно удалён."}
        else:
            raise HTTPException(status_code=400, detail="Не удалось удалить конфиг.")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")



@app.delete("/deactivate_configs/{target_server}/")
async def deactivate_configs(
    target_server: str, 
    config_uuids: list[str] = Body(..., embed=True)
):
    # Проверяем, что передан список конфигов
    if not config_uuids:
        raise HTTPException(status_code=400, detail="Список config_uuids не может быть пустым.")
    
    try:
        # Асинхронно вызываем функцию деактивации конфигов
        await xray_config.deactivate_user_configs_in_xray(
            uuids=config_uuids
        )
        return {"message": f"Configs deactivated successfully."}
    
    except Exception as e:
        # Обрабатываем возможные ошибки и возвращаем сообщение об ошибке
        raise HTTPException(
            status_code=500, 
            detail=f"Ошибка при деактивации конфигов: {str(e)}"
        )
