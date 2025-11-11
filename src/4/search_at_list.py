def search(array: list[int], number: int) -> bool:
    """
    Функция для поиска числа в отсортированном списке.

    Args:
        array: отсортированный список целых чисел
        number: число для поиска

    Returns:
        True если число найдено, иначе False
    """
    left = 0
    right = len(array) - 1

    while left <= right:
        mid = (left + right) // 2

        if array[mid] == number:
            return True
        elif array[mid] < number:
            left = mid + 1
        else:
            right = mid - 1

    return False


if __name__ == "__main__":
    arr = [1, 2, 3, 45, 356, 569, 600, 705, 923]

    assert search(arr, 569)
    assert not search(arr, 100)
    assert search(arr, 1)
    assert search(arr, 923)
