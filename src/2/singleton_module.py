from typing import List


class StatisticsCalculator:
    """Класс для статистических вычислений (синглтон через модуль)"""

    def __init__(self) -> None:
        self.datasets: List[List[float]] = []

    def add_dataset(self, data: List[float]) -> None:
        """Добавляет набор данных для анализа"""
        self.datasets.append(data.copy())

    def mean(self, dataset_index: int = 0) -> float:
        """Вычисляет среднее значение"""
        if not self.datasets or dataset_index >= len(self.datasets):
            return 0.0
        data = self.datasets[dataset_index]
        return sum(data) / len(data) if data else 0.0

    def variance(self, dataset_index: int = 0) -> float:
        """Вычисляет дисперсию"""
        if not self.datasets or dataset_index >= len(self.datasets):
            return 0.0
        data = self.datasets[dataset_index]
        if not data:
            return 0.0
        mean_val = self.mean(dataset_index)
        return sum((x - mean_val) ** 2 for x in data) / len(data)

    def get_dataset_count(self) -> int:
        return len(self.datasets)


# Создаем единственный экземпляр
stat_calculator = StatisticsCalculator()


def test_singleton_module() -> None:
    """Тестирование синглтона через механизм импортов"""

    from singleton_module import stat_calculator as calc1
    from singleton_module import stat_calculator as calc2

    # Проверяем, что это один и тот же объект
    assert calc1 is calc2, "Объекты должны быть одинаковыми"

    # Работаем с первым "экземпляром"
    calc1.add_dataset([1.0, 2.0, 3.0, 4.0, 5.0])

    # Проверяем через второй "экземпляр"
    assert calc2.get_dataset_count() == 1, "Должен быть один набор данных"

    # Проверяем математические вычисления
    expected_mean = 3.0
    assert calc1.mean(0) == expected_mean, "Среднее значение вычислено неверно"

    expected_variance = 2.0  # ((1-3)² + (2-3)² + (3-3)² + (4-3)² + (5-3)²) / 5 = (4+1+0+1+4)/5 = 10/5 = 2
    assert calc2.variance(0) == expected_variance, "Дисперсия вычислена неверно"

    # Добавляем второй набор данных через второй объект
    calc2.add_dataset([10.0, 20.0, 30.0])

    # Проверяем через первый объект
    assert calc1.get_dataset_count() == 2, "Должно быть два набора данных"
    assert calc1.mean(1) == 20.0, "Среднее второго набора вычислено неверно"

    print("✓ Синглтон через механизм импортов работает корректно")


if __name__ == "__main__":
    test_singleton_module()
