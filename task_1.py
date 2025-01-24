import logging
import random
import time
import sys
from colorama import init, Fore
from collections import OrderedDict
from tabulate import tabulate

# ============================
# Logger & colorama
# ============================
init(autoreset=True)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s"
)
logger = logging.getLogger(__name__)


# ============================
# 1. LRUCache class
# ============================
class LRUCache:
    """
    LRU-кеш (Least Recently Used) на основі OrderedDict.
    Зберігатиме пари ключ -> значення, видаляючи
    найменш недавно використані при перевищенні capacity.
    """

    def __init__(self, capacity: int):
        """
        :param capacity: максимальний розмір кешу (кількість записів)
        """
        self.capacity = capacity
        self.cache = OrderedDict()  # key -> value

    def get(self, key):
        """
        Повертає значення з кешу за key або None, якщо ключа нема.
        При "хіті" переносить запис у кінець (позначає нещодавно використаний).
        """
        if key not in self.cache:
            return None
        # move_to_end => позначити як "нещодавно використаний"
        self.cache.move_to_end(key, last=True)
        return self.cache[key]

    def put(self, key, value):
        """
        Записати (key->value) в LRU-кеш.
        Якщо key вже був – оновити та перемістити в кінець.
        Якщо розмір перевищено – видалити найстаріший запис (leftmost).
        """
        if key in self.cache:
            self.cache.move_to_end(key, last=True)
            self.cache[key] = value
        else:
            self.cache[key] = value
            if len(self.cache) > self.capacity:
                self.cache.popitem(last=False)

    def clear(self):
        """Очистити весь кеш."""
        self.cache.clear()


# ============================
# 2. ArrayCacheSystem class
# ============================
class ArrayCacheSystem:
    """
    Клас, що містить:
      - основний масив (list[int]),
      - екземпляр LRUCache,
      - методи доступу (range_sum та update) з кешем / без.
    """

    def __init__(self, array_size: int, cache_capacity: int):
        """
        :param array_size: розмір масиву.
        :param cache_capacity: розмір LRU-кешу (K).
        """
        self.array = [0] * array_size
        self.cache = LRUCache(cache_capacity)

    def load_array(self, data):
        """
        Завантажує дані (list[int]) у внутрішній масив.
        Кількість елементів має збігатися з array_size.
        """
        if len(data) != len(self.array):
            raise ValueError("Data length mismatch with array size.")
        self.array = data

    # --- Методи без кешування ---
    def range_sum_no_cache(self, L, R) -> int:
        """
        Повертає суму елементів self.array[L..R] (включно) без кешу.
        """
        return sum(self.array[L : R + 1])

    def update_no_cache(self, index, value) -> None:
        """
        Оновлює значення self.array[index] = value (без кешу).
        """
        self.array[index] = value

    # --- Методи з кешуванням ---
    def range_sum_with_cache(self, L, R) -> int:
        """
        Обчислює суму [L..R], перевіряючи / оновлюючи LRUCache.
        Ключ = (L,R), Значення = сума на відрізку.
        """
        key = (L, R)
        cached_val = self.cache.get(key)
        if cached_val is not None:
            return cached_val

        # miss => обчислюємо sum
        s = sum(self.array[L : R + 1])
        self.cache.put(key, s)
        return s

    def update_with_cache(self, index, value) -> None:
        """
        Оновити значення у масиві та очистити кеш,
        оскільки дані відрізки стали неактуальними.
        (Спрощена логіка - видаляємо весь кеш.)
        """
        self.array[index] = value
        self.cache.clear()


# ============================
# 3. CacheDemo class
# ============================
class CacheDemo:
    """
    Клас для демонстрації (N=100000 елементів, Q=50000 запитів),
    порівняння часу виконання з кешем та без нього.
    """

    def __init__(self, N=100_000, Q=50_000, K=1000):
        """
        :param N: розмір масиву
        :param Q: кількість запитів
        :param K: ємність LRU-кешу
        """
        self.N = N
        self.Q = Q
        self.K = K
        self.queries = []
        self.data_no_cache = []
        self.data_with_cache = []
        self.system_no_cache = None
        self.system_with_cache = None

    def generate_data(self):
        """
        Генерує:
        - масив випадкових int (1..1000) на N елементів,
        - Q запитів (Range / Update) за такими правилами:
            - ~80% - Range, ~20% - Update
            - Серед Range ~70% обираються зі списку "популярних" (L,R),
            решта ~30% - випадкові.
        - зберігає масив у data_no_cache та data_with_cache для однакових початкових даних.
        """
        logger.info(
            Fore.CYAN + f"Generating array of size {self.N} and {self.Q} queries."
        )
        # 1) Генеруємо сам масив
        arr = [random.randint(1, 1000) for _ in range(self.N)]
        self.data_no_cache = list(arr)  # копія
        self.data_with_cache = list(arr)

        # 2) Заздалегідь формуємо кілька "популярних" діапазонів
        #    Наприклад, 10 штук
        popular_ranges = []
        for _ in range(10):
            L = random.randint(0, self.N - 1)
            R = random.randint(L, self.N - 1)
            popular_ranges.append((L, R))

        # 3) Генеруємо Q запитів:
        #    - 80% Range, 20% Update
        #    - з Range: 70% беремо з popular_ranges, 30% - випадкові
        self.queries = []
        for _ in range(self.Q):
            # Визначаємо, який запит: Range чи Update
            # ~80% = 0.8; random.random() повертає float [0..1)
            if random.random() < 0.8:
                # Це Range
                # Вирішуємо, популярний чи випадковий
                if random.random() < 0.7:
                    # популярний
                    L, R = random.choice(popular_ranges)
                else:
                    # випадковий
                    L = random.randint(0, self.N - 1)
                    R = random.randint(L, self.N - 1)
                self.queries.append(("Range", L, R))
            else:
                # Це Update
                idx = random.randint(0, self.N - 1)
                val = random.randint(1, 2000)
                self.queries.append(("Update", idx, val))

    def setup_systems(self):
        """
        Створює два об'єкти ArrayCacheSystem:
         - один без кешу,
         - один із LRUCache (розмір K).
        Завантажує у них згенеровані дані.
        """
        self.system_no_cache = ArrayCacheSystem(self.N, cache_capacity=0)
        self.system_with_cache = ArrayCacheSystem(self.N, cache_capacity=self.K)

        # Завантажити дані
        self.system_no_cache.load_array(self.data_no_cache)
        self.system_with_cache.load_array(self.data_with_cache)

    def run_no_cache(self) -> float:
        """
        Виконує усі Q запитів на system_no_cache, вимірює час і повертає його (сек).
        """
        logger.info(Fore.GREEN + "Executing queries without cache...")
        start = time.time()
        for q in self.queries:
            if q[0] == "Range":
                _, L, R = q
                self.system_no_cache.range_sum_no_cache(L, R)
            else:
                _, idx, val = q
                self.system_no_cache.update_no_cache(idx, val)
        return time.time() - start

    def run_with_cache(self) -> float:
        """
        Виконує усі Q запитів на system_with_cache (з LRUCache), вимірює час і повертає його (сек).
        """
        logger.info(
            Fore.GREEN + f"Executing queries WITH LRUCache (capacity={self.K})..."
        )
        start = time.time()
        for q in self.queries:
            if q[0] == "Range":
                _, L, R = q
                self.system_with_cache.range_sum_with_cache(L, R)
            else:
                _, idx, val = q
                self.system_with_cache.update_with_cache(idx, val)
        return time.time() - start

    def run_comparison(self):
        """
        Основний метод:
          1) генеруємо дані
          2) створюємо системи
          3) виконуємо Q запитів без кешу та з кешем
          4) виводимо результати таблично
        """
        from tabulate import (
            tabulate,
        )  # Перенесено всередину, щоб не було конфліктів, якщо імпорт зверху

        self.generate_data()
        self.setup_systems()

        # 1) Без кешу
        time_no_cache = self.run_no_cache()

        # 2) З кешем
        time_with_cache = self.run_with_cache()

        # Формуємо таблицю
        table_data = [
            ["Без кешування", f"{time_no_cache:.2f}"],
            ["З LRU-кешем", f"{time_with_cache:.2f}"],
        ]
        print("\nРезультати порівняння:")
        print(tabulate(table_data, headers=["Метод", "Час (с)"], tablefmt="github"))


def main():
    """
    Точка входу. Параметри N, Q, K можна змінити за бажанням.
    """
    sys.setrecursionlimit(10**7)

    # Параметри
    N = 100_000
    Q = 50_000
    K = 1000

    demo = CacheDemo(N=N, Q=Q, K=K)
    demo.run_comparison()


if __name__ == "__main__":
    main()
