import json
from http.client import HTTPConnection
from typing import Any, Dict, Optional, Tuple

import aiohttp


async def fetch_exchange_rates_async(currency: str) -> Dict[str, Any]:
    """
    Асинхронно получает курс валют от стороннего API.

    Args:
        currency: Код валюты (например, 'USD')

    Returns:
        Словарь с данными о курсах валют

    Raises:
        Exception: Если произошла ошибка при запросе
    """
    url = f"https://api.exchangerate-api.com/v4/latest/{currency.upper()}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception(f"API returned status {response.status}")


def fetch_exchange_rates_sync(currency: str) -> Dict[str, Any]:
    """
    Синхронно получает курс валют от стороннего API.

    Args:
        currency: Код валюты (например, 'USD')

    Returns:
        Словарь с данными о курсах валют

    Raises:
        Exception: Если произошла ошибка при запросе
    """
    conn = HTTPConnection("api.exchangerate-api.com")
    conn.request("GET", f"/v4/latest/{currency.upper()}")
    response = conn.getresponse()

    if response.status == 200:
        data = response.read().decode("utf-8")
        return json.loads(data)
    else:
        raise Exception(f"API returned status {response.status}")


def create_asgi_response(
    status: int, body: Dict[str, Any], headers: Optional[Dict[str, str]] = None
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Создает структуру ответа ASGI.

    Args:
        status: HTTP статус код
        body: Тело ответа
        headers: Дополнительные заголовки

    Returns:
        Кортеж (start_response, body_response)
    """
    default_headers = [
        (b"content-type", b"application/json"),
        (b"access-control-allow-origin", b"*"),
    ]

    if headers:
        for key, value in headers.items():
            default_headers.append((key.encode(), value.encode()))

    body_bytes = json.dumps(body).encode("utf-8")

    return (
        {
            "type": "http.response.start",
            "status": status,
            "headers": default_headers,
        },
        {
            "type": "http.response.body",
            "body": body_bytes,
        },
    )


def extract_currency_from_path(
    path: str,
) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """
    Извлекает код валюты из пути и валидирует его.

    Args:
        path: Путь запроса

    Returns:
        Кортеж (currency, error_response) - если ошибка, то currency=None
    """
    # Убираем начальный и конечный слэши
    path = path.strip("/")

    if not path:
        error_response = {
            "error": "Currency code is required",
            "example": "Use /USD or /EUR",
        }
        return None, error_response

    # Простая валидация - только буквы, длина 3
    if not path.isalpha() or len(path) != 3:
        error_response = {
            "error": "Invalid currency code",
            "details": "Currency code must be 3 letters (e.g., USD, EUR)",
        }
        return None, error_response

    return path.upper(), None


def create_error_response(
    message: str, details: Optional[str] = None
) -> Dict[str, Any]:
    """
    Создает стандартизированный ответ об ошибке.

    Args:
        message: Основное сообщение об ошибке
        details: Детали ошибки

    Returns:
        Словарь с описанием ошибки
    """
    error_response = {"error": message}
    if details:
        error_response["details"] = details
    return error_response
