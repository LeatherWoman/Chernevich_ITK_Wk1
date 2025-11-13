from typing import Any, Dict


class SingletonMeta(type):
    """Метакласс для реализации синглтона"""

    _instances: Dict[type, Any] = {}

    def __call__(cls, *args: Any, **kwargs: Any) -> Any:
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class Calculator(metaclass=SingletonMeta):
    """Простой класс калькулятора, использующий синглтон через метакласс"""

    def __init__(self) -> None:
        self.history: list[str] = []

    def add(self, a: float, b: float) -> float:
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result

    def multiply(self, a: float, b: float) -> float:
        result = a * b
        self.history.append(f"{a} * {b} = {result}")
        return result

    def get_history(self) -> list[str]:
        return self.history.copy()


def test_singleton_meta() -> None:
    """Тестирование синглтона через метаклассы"""

    # Создаем первый экземпляр
    calc1 = Calculator()
    calc1.add(5, 3)

    # Создаем второй экземпляр
    calc2 = Calculator()
    calc2.multiply(4, 2)

    # Проверяем, что это один и тот же объект
    assert calc1 is calc2, "Объекты должны быть одинаковыми"

    # Проверяем, что история операций общая
    assert len(calc1.get_history()) == 2, "История должна содержать 2 операции"
    assert len(calc2.get_history()) == 2, "История должна содержать 2 операции"

    # Проверяем математические вычисления
    assert calc1.add(10, 20) == 30, "Сложение работает некорректно"
    assert calc2.multiply(5, 6) == 30, "Умножение работает некорректно"

    print("✓ Синглтон через метаклассы работает корректно")


if __name__ == "__main__":
    test_singleton_meta()
