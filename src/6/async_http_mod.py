import asyncio
import json
import logging
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp

# Настройка логирования
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class FetchResult:
    """Результат выполнения HTTP-запроса"""

    url: str
    success: bool
    content: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    response_time: float = 0.0


class URLFetcher:
    """Класс для асинхронной загрузки URL"""

    def __init__(
        self,
        max_concurrent: int = 5,
        timeout: aiohttp.ClientTimeout = aiohttp.ClientTimeout(total=30),
        max_retries: int = 2,
    ):
        """
        Args:
            max_concurrent: Максимальное количество одновременных запросов
            timeout: Таймаут для запросов
            max_retries: Максимальное количество повторных попыток
        """
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.max_retries = max_retries
        self.semaphore = asyncio.Semaphore(max_concurrent)

    @asynccontextmanager
    async def _create_session(self) -> aiohttp.ClientSession:
        """Создает и управляет сессией aiohttp"""
        connector = aiohttp.TCPConnector(limit=self.max_concurrent, limit_per_host=2)
        session = aiohttp.ClientSession(
            connector=connector,
            timeout=self.timeout,
            headers={"User-Agent": "AsyncURLFetcher/1.0"},
        )
        try:
            yield session
        finally:
            await session.close()

    async def _fetch_single_url(
        self, session: aiohttp.ClientSession, url: str
    ) -> FetchResult:
        """Выполняет один HTTP-запрос с обработкой ошибок"""
        start_time = time.time()

        for attempt in range(self.max_retries + 1):
            try:
                async with self.semaphore:
                    async with session.get(url) as response:
                        if response.status == 200:
                            # Читаем и парсим JSON
                            text = await response.text()
                            try:
                                json_content = json.loads(text)
                                return FetchResult(
                                    url=url,
                                    success=True,
                                    content=json_content,
                                    response_time=time.time() - start_time,
                                )
                            except json.JSONDecodeError as e:
                                error_msg = f"Invalid JSON: {str(e)}"
                                if attempt == self.max_retries:
                                    return FetchResult(
                                        url=url,
                                        success=False,
                                        error=error_msg,
                                        response_time=time.time() - start_time,
                                    )
                        else:
                            error_msg = f"HTTP {response.status}"
                            if attempt == self.max_retries:
                                return FetchResult(
                                    url=url,
                                    success=False,
                                    error=error_msg,
                                    response_time=time.time() - start_time,
                                )

            except asyncio.TimeoutError:
                error_msg = "Timeout"
                if attempt == self.max_retries:
                    return FetchResult(
                        url=url,
                        success=False,
                        error=error_msg,
                        response_time=time.time() - start_time,
                    )

            except aiohttp.ClientError as e:
                error_msg = f"Client error: {str(e)}"
                if attempt == self.max_retries:
                    return FetchResult(
                        url=url,
                        success=False,
                        error=error_msg,
                        response_time=time.time() - start_time,
                    )

            except Exception as e:
                error_msg = f"Unexpected error: {str(e)}"
                if attempt == self.max_retries:
                    return FetchResult(
                        url=url,
                        success=False,
                        error=error_msg,
                        response_time=time.time() - start_time,
                    )

            # Пауза перед повторной попыткой
            if attempt < self.max_retries:
                await asyncio.sleep(1 * (attempt + 1))

        # Этот код никогда не должен выполняться, но для безопасности:
        return FetchResult(
            url=url,
            success=False,
            error="Max retries exceeded",
            response_time=time.time() - start_time,
        )

    async def fetch_urls(
        self, urls: List[str], output_file: str = "result.jsonl"
    ) -> Dict[str, Any]:
        """
        Асинхронно загружает список URL и сохраняет результаты в файл

        Args:
            urls: Список URL для загрузки
            output_file: Имя выходного файла

        Returns:
            Статистика выполнения
        """
        stats = {"total": len(urls), "successful": 0, "failed": 0, "total_time": 0.0}

        start_time = time.time()

        async with self._create_session() as session:
            tasks = [self._fetch_single_url(session, url) for url in urls]

            # Обрабатываем результаты по мере их поступления
            with open(output_file, "w", encoding="utf-8") as f:
                for future in asyncio.as_completed(tasks):
                    result = await future

                    # Записываем успешные результаты
                    if result.success and result.content is not None:
                        output_data = {"url": result.url, "content": result.content}
                        f.write(json.dumps(output_data, ensure_ascii=False) + "\n")
                        f.flush()  # Обеспечиваем запись после каждого URL
                        stats["successful"] += 1
                        logger.info(
                            f"✅ Success: {result.url} ({result.response_time:.2f}s)"
                        )
                    else:
                        stats["failed"] += 1
                        logger.warning(f"❌ Failed: {result.url} - {result.error}")

        stats["total_time"] = time.time() - start_time
        return stats


def read_urls_from_file(file_path: str, limit: Optional[int] = None) -> List[str]:
    """
    Читает список URL из файла с возможностью ограничения количества

    Args:
        file_path: Путь к файлу с URL
        limit: Максимальное количество URL для чтения (None - все)

    Returns:
        Список URL
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File {file_path} not found")

    urls = []
    with open(file_path, "r", encoding="utf-8") as f:
        # Пропускаем заголовок если есть
        lines = f.readlines()
        start_index = 1 if lines and lines[0].strip().lower() == "url" else 0

        for i, line in enumerate(lines[start_index:], start=1):
            if limit is not None and len(urls) >= limit:
                break

            url = line.strip()
            if url and not url.startswith(
                "#"
            ):  # Игнорируем пустые строки и комментарии
                urls.append(url)

    return urls


async def fetch_urls_from_file(
    input_file: str = "src/6/1.csv",
    output_file: str = "src/6/result.jsonl",
    max_concurrent: int = 5,
    timeout: int = 10,
    max_retries: int = 2,
    limit: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Основная функция для загрузки URL из файла

    Args:
        input_file: Входной файл с URL
        output_file: Выходной файл для результатов
        max_concurrent: Максимальное количество одновременных запросов
        timeout: Таймаут в секундах
        max_retries: Количество повторных попыток
        limit: Ограничение количества URL для обработки (для тестирования)

    Returns:
        Статистика выполнения
    """
    try:
        # Читаем URL из файла
        urls = read_urls_from_file(input_file, limit=limit)

        if not urls:
            logger.warning("No URLs found in input file")
            return {}

        limit_info = f" (limited to first {limit})" if limit else ""
        logger.info(f"Found {len(urls)} URLs to process{limit_info}")

        # Создаем фетчер с настройками
        fetcher = URLFetcher(
            max_concurrent=max_concurrent,
            timeout=aiohttp.ClientTimeout(total=timeout),
            max_retries=max_retries,
        )

        # Выполняем загрузку
        stats = await fetcher.fetch_urls(urls, output_file)

        # Выводим статистику
        logger.info("=" * 50)
        logger.info("📊 PROCESSING COMPLETE")
        logger.info(f"Total URLs processed: {stats['total']}")
        logger.info(f"Successful: {stats['successful']}")
        logger.info(f"Failed: {stats['failed']}")
        logger.info(
            f"Success rate: {(stats['successful'] / stats['total'] * 100):.1f}%"
        )
        logger.info(f"Total time: {stats['total_time']:.2f} seconds")
        logger.info(
            f"Avg time per URL: {stats['total_time'] / stats['total']:.2f} seconds"
        )
        logger.info(f"Results saved to: {output_file}")

        return stats

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise


async def main():
    """Основная функция с поддержкой аргументов командной строки"""
    import argparse

    parser = argparse.ArgumentParser(description="Async URL fetcher")
    parser.add_argument(
        "--input", default="src/6/1.csv", help="Input CSV file with URLs"
    )
    parser.add_argument(
        "--output", default="src/6/result.jsonl", help="Output JSONL file for results"
    )
    parser.add_argument(
        "--limit", type=int, help="Limit number of URLs to process (for testing)"
    )
    parser.add_argument(
        "--concurrent", type=int, default=5, help="Maximum concurrent requests"
    )
    parser.add_argument(
        "--timeout", type=int, default=120, help="Request timeout in seconds"
    )
    parser.add_argument("--retries", type=int, default=2, help="Maximum retry attempts")

    args = parser.parse_args()

    await fetch_urls_from_file(
        input_file=args.input,
        output_file=args.output,
        max_concurrent=args.concurrent,
        timeout=args.timeout,
        max_retries=args.retries,
        limit=args.limit,
    )


if __name__ == "__main__":
    # Запускаем асинхронную функцию
    asyncio.run(main())
