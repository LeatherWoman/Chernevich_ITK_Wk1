from datetime import datetime


class CreatedAtMeta(type):
    """Метакласс, добавляющий атрибут created_at с текущей датой и временем"""

    def __new__(cls, name, bases, attrs):
        # Добавляем атрибут created_at с текущим временем
        attrs["created_at"] = datetime.now()
        return super().__new__(cls, name, bases, attrs)


class TestOne(metaclass=CreatedAtMeta):
    pass


class TestTwo(metaclass=CreatedAtMeta):
    pass


if __name__ == "__main__":
    obj_one = TestOne()
    obj_two = TestTwo()

    print(TestOne.created_at, TestTwo.created_at)
    print(f"object one created at {obj_one.created_at}")
    print(f"object two created at {obj_one.created_at}")
