from typing import Any, Optional


class GeometryCalculator:
    """Класс для геометрических вычислений с синглтоном через __new__"""

    _instance: Optional["GeometryCalculator"] = None
    _initialized: bool = False

    def __new__(cls, *args: Any, **kwargs: Any) -> "GeometryCalculator":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        # Защита от повторной инициализации
        if not GeometryCalculator._initialized:
            self.calculation_count: int = 0
            GeometryCalculator._initialized = True

    def circle_area(self, radius: float) -> float:
        """Вычисляет площадь круга"""
        self.calculation_count += 1
        return 3.14159 * radius**2

    def triangle_area(self, base: float, height: float) -> float:
        """Вычисляет площадь треугольника"""
        self.calculation_count += 1
        return 0.5 * base * height

    def rectangle_area(self, width: float, height: float) -> float:
        """Вычисляет площадь прямоугольника"""
        self.calculation_count += 1
        return width * height

    def get_calculation_count(self) -> int:
        return self.calculation_count


def test_singleton_new() -> None:
    """Тестирование синглтона через метод __new__"""

    # Сбрасываем состояние для чистого теста
    GeometryCalculator._instance = None
    GeometryCalculator._initialized = False

    # Создаем первый экземпляр
    geom1 = GeometryCalculator()
    area1 = geom1.circle_area(5.0)

    # Создаем второй экземпляр
    geom2 = GeometryCalculator()
    area2 = geom2.triangle_area(4.0, 3.0)

    # Проверяем, что это один и тот же объект
    assert geom1 is geom2, "Объекты должны быть одинаковыми"

    # Проверяем, что счетчик вычислений общий
    assert geom1.get_calculation_count() == 2, (
        f"Должно быть 2 вычисления, но получили {geom1.get_calculation_count()}"
    )
    assert geom2.get_calculation_count() == 2, (
        f"Должно быть 2 вычисления, но получили {geom2.get_calculation_count()}"
    )

    # Проверяем математические вычисления
    expected_circle_area = 3.14159 * 25.0
    assert abs(area1 - expected_circle_area) < 0.001, "Площадь круга вычислена неверно"

    expected_triangle_area = 0.5 * 4.0 * 3.0
    assert area2 == expected_triangle_area, "Площадь треугольника вычислена неверно"

    # Проверяем третье вычисление
    rect_area = geom1.rectangle_area(6.0, 4.0)
    assert rect_area == 24.0, "Площадь прямоугольника вычислена неверно"
    assert geom2.get_calculation_count() == 3, (
        f"Должно быть 3 вычисления, но получили {geom2.get_calculation_count()}"
    )

    print("✓ Синглтон через __new__ работает корректно")


if __name__ == "__main__":
    test_singleton_new()
