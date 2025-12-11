from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
from typing import Dict
from loguru import logger
from app.data import config
from fastapi import FastAPI, HTTPException, Query
from app.xray import xray_config

app = FastAPI()


logger.add("logs/app_{time}.log", rotation="10 MB", compression="zip")

@app.post("/add_user/{country}/")
async def add_user(
    country: str, 
    user_id: int, 
    config_name: str,
    # 💡 ДОБАВЛЕНО: Новый, обязательный параметр UUID
    user_uuid: str = Query() 
):
    logger.info(f"Received request for {country} with user_id={user_id}, config_name={config_name}, custom_uuid={user_uuid}")
    
    try:
        # 💡 ПЕРЕДАЧА UUID: Передаем полученный user_uuid в add_new_user
        user_link, config_uuid = await xray_config.add_new_user(
            config_name=config_name, 
            user_telegram_id=user_id,
            custom_uuid=user_uuid # <--- Передаем
        )
        server_domain = config.domain_name
        server_country = config.server_country  # Название страны
        server_country_code = config.server_country_code  # Код страны
        return {
            "link": user_link,
            "config_uuid": config_uuid, 
            "server_domain": server_domain,
            "server_country": server_country, 
            "server_country_code": server_country_code
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add user: {str(e)}")



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


@app.get("/server_stats/")
async def get_server_stats():
    """
    Эндпоинт для получения текущей статистики сервера.
    Возвращает информацию о количестве активных клиентов, стране и домене.
    """
    # logger.info("Получен запрос на статистику сервера.")

    try:
        # Читаем количество активных клиентов
        active_clients = await xray_config.get_active_client_count()  # Функция для подсчета клиентов

        # Возвращаем статистику
        return {
            "server_domain": config.domain_name,  # Домен сервера
            "server_country": config.server_country,  # Название страны
            "server_country_code": config.server_country_code,  # Код страны
            "active_clients": active_clients  # Количество активных клиентов
        }

    except Exception as e:
        logger.error(f"Ошибка при получении статистики: {str(e)}")
        raise HTTPException(status_code=500, detail="Не удалось получить статистику")

@app.delete("/cleanup_configs/{target_server}/")
async def cleanup_configs(target_server: str, valid_uuids: dict):
    """
    Удаляет устаревшие VPN-конфиги с сервера Xray.
    """

    try:
        valid_uuids_list = valid_uuids.get("valid_uuids", [])

        if not valid_uuids_list:
            raise HTTPException(status_code=400, detail="Список валидных UUID пуст")

        # Получаем все текущие UUID с сервера
        all_uuids = await xray_config.get_all_uuids()

        # Находим невалидные (те, которых нет в списке валидных)
        invalid_uuids = list(set(all_uuids) - set(valid_uuids_list))

        if not invalid_uuids:
            return {"status": "success", "message": "Нет невалидных конфигов для удаления"}

        # Удаляем невалидные UUID
        success = await xray_config.disconnect_many_uuids(invalid_uuids)

        if success:
            return {"status": "success", "removed_count": len(invalid_uuids)}
        else:
            raise HTTPException(status_code=500, detail="Ошибка при удалении конфигов")

    except Exception as e:
        logger.error(f"Ошибка при очистке конфигов: {e}")
        raise HTTPException(status_code=500, detail="Не удалось очистить конфигурацию")

