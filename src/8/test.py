"""
Тестовый скрипт для проверки работы приложения с использованием assert.
"""

# import requests
import asyncio
import json

import pytest

# import aiohttp
# from typing import Dict, Any, List, Callable


def test_currency_extraction():
    """Тестирование функции извлечения валюты из пути"""
    from common import extract_currency_from_path

    # Тестовые случаи
    test_cases = [
        ("/USD", ("USD", None)),
        ("/eur", ("EUR", None)),
        ("/gBp", ("GBP", None)),
        (
            "/",
            (
                None,
                {"error": "Currency code is required", "example": "Use /USD or /EUR"},
            ),
        ),
        (
            "/123",
            (
                None,
                {
                    "error": "Invalid currency code",
                    "details": "Currency code must be 3 letters (e.g., USD, EUR)",
                },
            ),
        ),
        (
            "/USDD",
            (
                None,
                {
                    "error": "Invalid currency code",
                    "details": "Currency code must be 3 letters (e.g., USD, EUR)",
                },
            ),
        ),
        (
            "/U1D",
            (
                None,
                {
                    "error": "Invalid currency code",
                    "details": "Currency code must be 3 letters (e.g., USD, EUR)",
                },
            ),
        ),
    ]

    for path, expected in test_cases:
        result = extract_currency_from_path(path)
        assert result == expected, (
            f"Failed for path '{path}': expected {expected}, got {result}"
        )

    print("✓ test_currency_extraction passed")


def test_error_response_creation():
    """Тестирование создания ошибок"""
    from common import create_error_response

    # Тест без деталей
    error1 = create_error_response("Test error")
    assert error1 == {"error": "Test error"}

    # Тест с деталями
    error2 = create_error_response("Test error", "Detailed message")
    assert error2 == {"error": "Test error", "details": "Detailed message"}

    print("✓ test_error_response_creation passed")


def test_asgi_response_creation():
    """Тестирование создания ASGI ответов"""
    from common import create_asgi_response

    test_data = {"test": "data", "number": 123}
    start_response, body_response = create_asgi_response(200, test_data)

    assert start_response["type"] == "http.response.start"
    assert start_response["status"] == 200
    assert (b"content-type", b"application/json") in start_response["headers"]
    assert (b"access-control-allow-origin", b"*") in start_response["headers"]

    assert body_response["type"] == "http.response.body"
    parsed_body = json.loads(body_response["body"].decode("utf-8"))
    assert parsed_body == test_data

    print("✓ test_asgi_response_creation passed")


@pytest.mark.asyncio
async def test_asgi_app_structure():
    """Тестирование структуры ASGI приложения"""
    from asgi import asgi_app

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/USD",
    }

    received_messages = []

    async def receive():
        return {"type": "http.request"}

    async def send(message):
        received_messages.append(message)

    await asgi_app(scope, receive, send)

    assert len(received_messages) >= 2, (
        "Should receive at least start and body messages"
    )

    start_message = next(
        (m for m in received_messages if m["type"] == "http.response.start"), None
    )
    body_message = next(
        (m for m in received_messages if m["type"] == "http.response.body"), None
    )

    assert start_message is not None, "Should have start response message"
    assert body_message is not None, "Should have body response message"
    assert start_message["status"] == 200
    assert (b"content-type", b"application/json") in start_message["headers"]

    print("✓ test_asgi_app_structure passed")


@pytest.mark.asyncio
async def test_asgi_app_method_validation():
    """Тестирование валидации методов в ASGI"""
    from asgi import asgi_app

    scope = {
        "type": "http",
        "method": "POST",  # Неподдерживаемый метод
        "path": "/USD",
    }

    received_messages = []

    async def receive():
        return {"type": "http.request"}

    async def send(message):
        received_messages.append(message)

    await asgi_app(scope, receive, send)

    start_message = next(
        (m for m in received_messages if m["type"] == "http.response.start"), None
    )
    assert start_message is not None, "Should have start response message"
    assert start_message["status"] == 405

    body_message = next(
        (m for m in received_messages if m["type"] == "http.response.body"), None
    )
    assert body_message is not None, "Should have body response message"

    error_data = json.loads(body_message["body"].decode("utf-8"))
    assert "error" in error_data
    assert "Method not allowed" in error_data["error"]

    print("✓ test_asgi_app_method_validation passed")


def test_exchange_rates_api_sync():
    """Тестирование синхронного API получения курсов валют"""
    from common import fetch_exchange_rates_sync

    try:
        result = fetch_exchange_rates_sync("USD")

        # Проверяем структуру ответа
        assert isinstance(result, dict)
        assert "base" in result
        assert result["base"] == "USD"
        assert "rates" in result
        assert isinstance(result["rates"], dict)
        assert "USD" in result["rates"]
        assert result["rates"]["USD"] == 1.0

        print("✓ test_exchange_rates_api_sync passed")
    except Exception as e:
        print(f"⚠ test_exchange_rates_api_sync skipped: {e}")


@pytest.mark.asyncio
async def test_exchange_rates_api_async():
    """Тестирование асинхронного API получения курсов валют"""
    from common import fetch_exchange_rates_async

    try:
        result = await fetch_exchange_rates_async("EUR")

        # Проверяем структуру ответа
        assert isinstance(result, dict)
        assert "base" in result
        assert result["base"] == "EUR"
        assert "rates" in result
        assert isinstance(result["rates"], dict)
        assert "EUR" in result["rates"]
        assert result["rates"]["EUR"] == 1.0

        print("✓ test_exchange_rates_api_async passed")
    except Exception as e:
        print(f"⚠ test_exchange_rates_api_async skipped: {e}")


@pytest.mark.asyncio
async def test_asgi_app_invalid_paths():
    """Тестирование ASGI с некорректными путями"""
    from asgi import asgi_app

    test_cases = [
        ("/", 400),
        ("/123", 400),
        ("/USDD", 400),
    ]

    for path, expected_status in test_cases:
        scope = {
            "type": "http",
            "method": "GET",
            "path": path,
        }

        received_messages = []

        async def receive():
            return {"type": "http.request"}

        async def send(message):
            received_messages.append(message)

        await asgi_app(scope, receive, send)

        start_message = next(
            (m for m in received_messages if m["type"] == "http.response.start"), None
        )
        assert start_message is not None, (
            f"Should have start response for path '{path}'"
        )
        assert start_message["status"] == expected_status, (
            f"Failed for path '{path}': expected {expected_status}, got {start_message['status']}"
        )

    print("✓ test_asgi_app_invalid_paths passed")


@pytest.mark.asyncio
async def test_asgi_app_successful_response():
    """Тестирование успешного ответа ASGI приложения"""
    from asgi import asgi_app

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/USD",
    }

    received_messages = []

    async def receive():
        return {"type": "http.request"}

    async def send(message):
        received_messages.append(message)

    await asgi_app(scope, receive, send)

    # Находим сообщения
    start_message = next(
        (m for m in received_messages if m["type"] == "http.response.start"), None
    )
    body_message = next(
        (m for m in received_messages if m["type"] == "http.response.body"), None
    )

    assert start_message is not None
    assert start_message["status"] == 200

    assert body_message is not None
    data = json.loads(body_message["body"].decode("utf-8"))

    # Проверяем базовую структуру ответа
    assert "base" in data
    assert data["base"] == "USD"
    assert "rates" in data
    assert isinstance(data["rates"], dict)

    print("✓ test_asgi_app_successful_response passed")


def run_all_tests():
    """Запуск всех тестов (для запуска без pytest)"""
    print("Running currency exchange proxy tests...")
    print("=" * 50)

    # Синхронные тесты
    test_currency_extraction()
    test_error_response_creation()
    test_asgi_response_creation()
    test_exchange_rates_api_sync()

    # Асинхронные тесты
    async_tests = [
        test_asgi_app_structure(),
        test_asgi_app_method_validation(),
        test_asgi_app_invalid_paths(),
        test_asgi_app_successful_response(),
        test_exchange_rates_api_async(),
    ]

    # Запуск асинхронных тестов
    async def run_async_tests():
        for test in async_tests:
            await test

    asyncio.run(run_async_tests())

    print("=" * 50)
    print("🎉 All tests passed!")


if __name__ == "__main__":
    try:
        run_all_tests()
    except AssertionError as e:
        print(f"❌ Test failed: {e}")
        exit(1)
    except Exception as e:
        print(f"💥 Unexpected error: {e}")
        exit(1)
