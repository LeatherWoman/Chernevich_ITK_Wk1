import unittest.mock
from collections import OrderedDict
from typing import Any, Callable


def lru_cache(*args, **kwargs) -> Callable:
    """
    Реализация декоратора кэша

    Может быть использован как:
    - @lru_cache
    - @lru_cache(maxsize=N)
    """
    # Если декоратор вызван без скобок: @lru_cache
    if len(args) == 1 and callable(args[0]) and not kwargs:
        func = args[0]
        return lru_cache()(func)

    # Получаем maxsize из аргументов или используем значение по умолчанию
    maxsize = kwargs.get("maxsize", None)

    def decorator(func: Callable) -> Callable:
        cache: OrderedDict = OrderedDict()

        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Создаем ключ на основе позиционных и именованных аргументов
            key = (args, tuple(sorted(kwargs.items())))

            # Если результат уже в кеше - перемещаем в конец и возвращаем
            if key in cache:
                result = cache.pop(key)
                cache[key] = result
                return result

            # Вызываем функцию и сохраняем результат
            result = func(*args, **kwargs)
            cache[key] = result

            # Если достигли максимального размера - удаляем самый старый элемент
            if maxsize is not None and len(cache) > maxsize:
                cache.popitem(last=False)

            return result

        return wrapper

    return decorator


@lru_cache
def sum(a: int, b: int) -> int:
    return a + b


@lru_cache
def sum_many(a: int, b: int, *, c: int, d: int) -> int:
    return a + b + c + d


@lru_cache(maxsize=3)
def multiply(a: int, b: int) -> int:
    return a * b


if __name__ == "__main__":
    assert sum(1, 2) == 3
    assert sum(3, 4) == 7

    assert multiply(1, 2) == 2
    assert multiply(3, 4) == 12

    assert sum_many(1, 2, c=3, d=4) == 10

    mocked_func = unittest.mock.Mock()
    mocked_func.side_effect = [1, 2, 3, 4]

    decorated = lru_cache(maxsize=2)(mocked_func)
    assert decorated(1, 2) == 1
    assert decorated(1, 2) == 1
    assert decorated(3, 4) == 2
    assert decorated(3, 4) == 2
    assert decorated(5, 6) == 3
    assert decorated(5, 6) == 3
    assert decorated(1, 2) == 4
    assert mocked_func.call_count == 4
