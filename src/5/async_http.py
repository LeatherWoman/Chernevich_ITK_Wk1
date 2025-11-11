import asyncio
import json
import os
from typing import Dict, List

import aiohttp


async def fetch_urls(urls: List[str], file_path: str) -> Dict[str, int]:
    """
    Асинхронно выполняет HTTP-запросы к списку URL-адресов.

    Args:
        urls: Список URL-адресов для запроса
        file_path: Путь к файлу для сохранения результатов

    Returns:
        Словарь с URL-адресами в качестве ключей и статус-кодами в качестве значений
    """
    # Семафор для ограничения количества одновременных запросов
    semaphore = asyncio.Semaphore(5)

    async def fetch_single_url(url: str) -> Dict[str, int]:
        async with semaphore:
            try:
                async with aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as session:
                    async with session.get(url) as response:
                        return {"url": url, "status_code": response.status}

            except aiohttp.ClientConnectorError:
                # Ошибка соединения (недоступный ресурс)
                return {"url": url, "status_code": 0}
            except aiohttp.ServerTimeoutError:
                # Таймаут запроса
                return {"url": url, "status_code": 0}
            except aiohttp.ClientError:
                # Другие ошибки клиента
                return {"url": url, "status_code": 0}
            except Exception:
                # Любые другие исключения
                return {"url": url, "status_code": 0}

    # Создаем и выполняем все задачи
    tasks = [fetch_single_url(url) for url in urls]
    results = await asyncio.gather(*tasks)

    # Сохраняем результаты в файл
    with open(file_path, "w", encoding="utf-8") as f:
        for result in results:
            f.write(json.dumps(result) + "\n")

    # Преобразуем результаты в словарь {url: status_code}
    result_dict = {result["url"]: result["status_code"] for result in results}

    return result_dict


# Пример использования
if __name__ == "__main__":
    urls = [
        "https://example.com",
        "https://httpbin.org/status/404",
        "https://nonexistent.url",
        "https://httpbin.org/status/200",
        "https://httpbin.org/status/500",
        "https://google.com",
        "https://httpbin.org/delay/2",  # URL с задержкой для тестирования
    ]
    file_to_dir = os.path.dirname(os.path.abspath(__file__))

    async def main():
        results = await fetch_urls(urls, os.path.join(file_to_dir, "results.jsonl"))
        print("Результаты:")
        for url, status in results.items():
            print(f"{url}: {status}")

    asyncio.run(main())
