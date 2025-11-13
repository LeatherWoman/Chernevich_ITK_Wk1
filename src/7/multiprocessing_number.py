import json
import math
import multiprocessing as mp
import os
import random
import time
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Process, Queue, cpu_count
from typing import Any, Dict, List


def generate_data(n: int) -> List[int]:
    """Генерирует список из n случайных целых чисел от 1 до 1000."""
    return [random.randint(1, 1000) for _ in range(n)]


def process_number(number: int) -> Dict[str, Any]:
    """
    Более ресурсоемкие вычисления для лучшего сравнения.
    """
    # Более сложная проверка на простое число
    is_prime = True
    if number < 2:
        is_prime = False
    elif number == 2:
        is_prime = True
    elif number % 2 == 0:
        is_prime = False
    else:
        # Проверяем нечетные делители до корня из числа
        for i in range(3, int(math.isqrt(number)) + 1, 2):
            if number % i == 0:
                is_prime = False
                break

    # Вычисление двойного факториала для увеличения нагрузки
    double_factorial = 1
    current = number
    while current > 0:
        double_factorial *= current
        current -= 2

    # Сумма различных математических последовательностей
    sum_cubes = sum(i**3 for i in range(1, min(number, 100) + 1))
    sum_fibonacci = 0
    a, b = 0, 1
    for _ in range(min(number, 100)):
        sum_fibonacci += a
        a, b = b, a + b

    return {
        "number": number,
        "is_prime": is_prime,
        "double_factorial": double_factorial,
        "sum_cubes": sum_cubes,
        "sum_fibonacci": sum_fibonacci,
    }


def sequential_processing(data: List[int]) -> List[Dict[str, Any]]:
    """Однопоточная обработка данных."""
    return [process_number(num) for num in data]


def parallel_threads(data: List[int], max_workers: int = None) -> List[Dict[str, Any]]:
    """Параллельная обработка с использованием пула потоков."""
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(process_number, data))
    return results


def parallel_processes_pool(data: List[int]) -> List[Dict[str, Any]]:
    """Параллельная обработка с использованием multiprocessing.Pool."""
    with mp.Pool(processes=cpu_count()) as pool:
        results = pool.map(process_number, data)
    return results


def worker_process_optimized(input_queue: Queue, output_queue: Queue, process_id: int):
    """Оптимизированная функция-воркер с пакетной обработкой."""
    batch_size = 100  # Обрабатываем пачками для уменьшения накладных расходов
    batch = []

    while True:
        try:
            data = input_queue.get(timeout=1)  # Таймаут для избежания блокировки
            if data is None:  # Сигнал завершения
                if batch:
                    # Обрабатываем оставшиеся данные в батче
                    for number, index in batch:
                        result = process_number(number)
                        output_queue.put((index, result))
                break

            batch.append(data)

            if len(batch) >= batch_size:
                # Обрабатываем весь батч
                for number, index in batch:
                    result = process_number(number)
                    output_queue.put((index, result))
                batch.clear()

        except:
            continue


def parallel_individual_processes_optimized(data: List[int]) -> List[Dict[str, Any]]:
    """Оптимизированная версия с отдельными процессами."""
    num_processes = min(
        cpu_count(), len(data) // 1000
    )  # Адаптивное количество процессов
    if num_processes < 1:
        num_processes = 1

    input_queue = Queue()
    output_queue = Queue()

    # Создание и запуск процессов
    processes = []
    for i in range(num_processes):
        p = Process(
            target=worker_process_optimized, args=(input_queue, output_queue, i)
        )
        p.start()
        processes.append(p)

    # Отправка данных в очередь пачками
    for i, number in enumerate(data):
        input_queue.put((number, i))

    # Отправка сигналов завершения
    for _ in range(num_processes):
        input_queue.put(None)

    # Сбор результатов
    results = [None] * len(data)
    received_count = 0
    while received_count < len(data):
        try:
            index, result = output_queue.get(timeout=30)  # Таймаут на случай проблем
            results[index] = result
            received_count += 1
        except:
            print("Таймаут при получении результатов")
            break

    # Ожидание завершения процессов
    for p in processes:
        p.join(timeout=5)
        if p.is_alive():
            p.terminate()

    return results


def measure_performance(data: List[int]) -> Dict[str, Any]:
    """Измеряет время выполнения для всех вариантов обработки."""
    print(f"Обработка {len(data)} чисел...")
    print(f"Количество CPU: {cpu_count()}")

    results = {}

    # Однопоточная обработка
    print("Запуск однопоточной обработки...")
    start_time = time.time()
    sequential_results = sequential_processing(data)
    sequential_time = time.time() - start_time
    results["sequential"] = sequential_time
    print(f"Однопоточная обработка: {sequential_time:.2f} секунд")

    # Параллельная обработка с потоками
    print("Запуск параллельной обработки с потоками...")
    start_time = time.time()
    threads_results = parallel_threads(data)
    threads_time = time.time() - start_time
    results["threads"] = threads_time
    print(f"Параллельные потоки: {threads_time:.2f} секунд")

    # Параллельная обработка с процессами (Pool)
    print("Запуск параллельной обработки с процессами (Pool)...")
    start_time = time.time()
    processes_results = parallel_processes_pool(data)
    processes_time = time.time() - start_time
    results["processes_pool"] = processes_time
    print(f"Процессы (Pool): {processes_time:.2f} секунд")

    # Оптимизированная версия отдельных процессов
    print("Запуск оптимизированной обработки с отдельными процессами...")
    start_time = time.time()
    individual_opt_results = parallel_individual_processes_optimized(data)
    individual_opt_time = time.time() - start_time
    results["individual_processes_opt"] = individual_opt_time
    print(f"Отдельные процессы (оптим.): {individual_opt_time:.2f} секунд")

    return results, sequential_results


def print_comparison_table(performance_results: Dict[str, float]) -> None:
    """Выводит таблицу сравнения производительности."""
    print("\n" + "=" * 70)
    print("СРАВНЕНИЕ ПРОИЗВОДИТЕЛЬНОСТИ")
    print("=" * 70)

    sequential_time = performance_results["sequential"]

    print(f"{'Метод':<30} {'Время (с)':<12} {'Ускорение':<12} {'Эффективность':<15}")
    print("-" * 70)

    method_names = {
        "sequential": "Однопоточный",
        "threads": "Потоки",
        "processes_pool": "Процессы (Pool)",
        "individual_processes_opt": "Отдельные процессы (оптим.)",
    }

    for method, time_taken in performance_results.items():
        method_name = method_names.get(method, method)

        speedup = sequential_time / time_taken if time_taken > 0 else 1
        efficiency = (speedup / cpu_count()) * 100 if "process" in method else 0

        efficiency_str = f"{efficiency:.1f}%" if efficiency > 0 else "N/A"

        print(
            f"{method_name:<30} {time_taken:<12.2f} {speedup:<12.2f}x {efficiency_str:<15}"
        )


def main():
    """Основная функция программы."""
    # Генерация данных
    print("Генерация данных...")
    data_size = 100000
    data = generate_data(data_size)

    # Измерение производительности
    performance_results, processed_results = measure_performance(data)

    # Вывод результатов сравнения
    print_comparison_table(performance_results)

    # Сохранение результатов
    save_results(processed_results[:100], "processing_results.json")

    # Анализ результатов
    print("\nАнализ результатов:")
    print("- Процессы обходят GIL и показывают лучшее ускорение")
    print("- Потоки медленнее из-за GIL в CPU-интенсивных задачах")
    print("- Отдельные процессы имеют высокие накладные расходы")


def get_script_directory() -> str:
    """Возвращает путь к папке где находится запускаемый скрипт."""
    return os.path.dirname(os.path.abspath(__file__))


def save_results(results: List[Dict[str, Any]], filename: str) -> None:
    """Сохраняет результаты в JSON файл в той же папке что и скрипт."""
    script_dir = get_script_directory()
    full_path = os.path.join(script_dir, filename)

    with open(full_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"✓ Результаты сохранены в: {full_path}")


if __name__ == "__main__":
    mp.freeze_support()
    main()
