from typing import Any, Callable, Dict

from common import (
    create_asgi_response,
    create_error_response,
    extract_currency_from_path,
    fetch_exchange_rates_async,
)


async def asgi_app(scope: Dict[str, Any], receive: Callable, send: Callable) -> None:
    """
    ASGI приложение для проксирования курса валют.

    Args:
        scope: Информация о запросе
        receive: Функция для получения тела запроса
        send: Функция для отправки ответа
    """
    if scope["type"] != "http":
        # Игнорируем не HTTP запросы
        return

    # Проверяем метод - только GET
    if scope["method"] != "GET":
        error_response = create_error_response(
            "Method not allowed", "Only GET method is supported"
        )
        response_start, response_body = create_asgi_response(405, error_response)
        await send(response_start)
        await send(response_body)
        return

    # Извлекаем и валидируем код валюты
    currency, error = extract_currency_from_path(scope["path"])

    if error:
        response_start, response_body = create_asgi_response(400, error)
        await send(response_start)
        await send(response_body)
        return

    try:
        # Получаем данные от API
        rates_data = await fetch_exchange_rates_async(currency)

        # Отправляем успешный ответ
        response_start, response_body = create_asgi_response(200, rates_data)
        await send(response_start)
        await send(response_body)

    except Exception as e:
        # Обрабатываем ошибки
        error_body = create_error_response("Failed to fetch exchange rates", str(e))
        response_start, response_body = create_asgi_response(500, error_body)
        await send(response_start)
        await send(response_body)


# Экспорт для ASGI серверов
app = asgi_app


if __name__ == "__main__":
    """
    Пример запуска для тестирования ASGI приложения.
    Для работы требуется: pip install aiohttp uvicorn
    """
    import uvicorn

    print("Starting ASGI server on http://localhost:8000")
    print("Example: http://localhost:8000/USD")
    print("Example: http://localhost:8000/EUR")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
