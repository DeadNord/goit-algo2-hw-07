import logging
from colorama import init, Fore
import sys
import time
from functools import lru_cache
import matplotlib.pyplot as plt
from tabulate import tabulate

init(autoreset=True)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s"
)
logger = logging.getLogger(__name__)


# ======================================
# 1. Клас LruFibSystem
# ======================================
class LruFibSystem:
    """
    Клас для обчислення чисел Фібоначчі через декоратор @lru_cache.
    """

    @staticmethod
    @lru_cache(None)
    def fibonacci_lru(n: int) -> int:
        if n < 2:
            return n
        return LruFibSystem.fibonacci_lru(n - 1) + LruFibSystem.fibonacci_lru(n - 2)


# ======================================
# 2. Класи для Splay-дерева (більш схожі на приклад)
# ======================================
class Node:
    """
    Вузол Splay-дерева. Зберігає data (Fibonacci index)
    + value (fib(n)) + parent, left_node, right_node.
    """

    def __init__(self, data, value, parent=None):
        self.data = data
        self.value = value
        self.parent = parent
        self.left_node = None
        self.right_node = None


class SplayTree:
    """
    Реалізація Splay-дерева для кешу Fibonacci:
      data = n (індекс),
      value = fib(n).
    """

    def __init__(self):
        self.root = None

    def insert(self, data, value):
        """Вставка нового вузла (data, value)."""
        if self.root is None:
            self.root = Node(data, value)
        else:
            self._insert_node(data, value, self.root)
        # Після вставки знайдемо новий вузол і splay його:
        node = self.find_node(data)
        if node:
            self._splay(node)

    def _insert_node(self, data, value, current_node):
        """Рекурсивна вставка (data, value) у піддерево з коренем current_node."""
        if data < current_node.data:
            if current_node.left_node:
                self._insert_node(data, value, current_node.left_node)
            else:
                current_node.left_node = Node(data, value, current_node)
        else:
            if current_node.right_node:
                self._insert_node(data, value, current_node.right_node)
            else:
                current_node.right_node = Node(data, value, current_node)

    def search(self, data):
        """
        Пошук елемента data (n) в дереві + splay.
        Якщо знайдено => підтягуємо вузол у корінь і повертаємо value.
        Якщо ні => повертаємо None.
        """
        node = self.find_node(data)
        if node:
            self._splay(node)
            return node.value
        return None

    def find_node(self, data):
        """Пошук вузла (без splay) для data."""
        node = self.root
        while node:
            if data < node.data:
                node = node.left_node
            elif data > node.data:
                node = node.right_node
            else:
                return node
        return None

    def _splay(self, node):
        """Splay операція (підняти node у корінь)."""
        while node.parent is not None:
            parent = node.parent
            grandparent = parent.parent
            if grandparent is None:
                # Zig
                if node == parent.left_node:
                    self._rotate_right(parent)
                else:
                    self._rotate_left(parent)
            elif node == parent.left_node and parent == grandparent.left_node:
                # Zig-Zig (Right-Right)
                self._rotate_right(grandparent)
                self._rotate_right(parent)
            elif node == parent.right_node and parent == grandparent.right_node:
                # Zig-Zig (Left-Left)
                self._rotate_left(grandparent)
                self._rotate_left(parent)
            else:
                # Zig-Zag
                if node == parent.left_node:
                    self._rotate_right(parent)
                    self._rotate_left(grandparent)
                else:
                    self._rotate_left(parent)
                    self._rotate_right(grandparent)

    def _rotate_right(self, node):
        """Права ротація вузла node."""
        left_child = node.left_node
        if left_child is None:
            return
        node.left_node = left_child.right_node
        if left_child.right_node:
            left_child.right_node.parent = node
        left_child.parent = node.parent
        if node.parent is None:
            self.root = left_child
        elif node == node.parent.left_node:
            node.parent.left_node = left_child
        else:
            node.parent.right_node = left_child
        left_child.right_node = node
        node.parent = left_child

    def _rotate_left(self, node):
        """Ліва ротація вузла node."""
        right_child = node.right_node
        if right_child is None:
            return
        node.right_node = right_child.left_node
        if right_child.left_node:
            right_child.left_node.parent = node
        right_child.parent = node.parent
        if node.parent is None:
            self.root = right_child
        elif node == node.parent.left_node:
            node.parent.left_node = right_child
        else:
            node.parent.right_node = right_child
        right_child.left_node = node
        node.parent = right_child


# ======================================
# 3. Fibonacci через SplayFibSystem
# ======================================
class SplayFibSystem:
    """
    Клас, що містить SplayTree для кешування fib(n).
    root.data = n, root.value = fib(n).
    """

    def __init__(self):
        self.tree = SplayTree()
        # Вставимо базові (0->0, 1->1)
        self.tree.insert(0, 0)
        self.tree.insert(1, 1)

    def fibonacci_splay(self, n: int) -> int:
        # Якщо вже маємо:
        val = self.tree.search(n)
        if val is not None:
            return val
        # Інакше обчислюємо
        if n < 2:
            return n
        f1 = self.fibonacci_splay(n - 1)
        f2 = self.fibonacci_splay(n - 2)
        res = f1 + f2
        self.tree.insert(n, res)
        return res


# ======================================
# 4. Порівняння FibComparison
# ======================================
class FibComparison:
    """
    Порівнюємо час виконання:
      - LruFibSystem.fibonacci_lru(n)
      - SplayFibSystem().fibonacci_splay(n)
    для n у діапазоні [0..951] з кроком 50.
    """

    def __init__(self):
        self.ns = list(range(0, 951, 50))
        self.results_lru = []
        self.results_splay = []

    def measure_lru_time(self, n: int, repeats=5) -> float:
        """
        Прямий замір часу - кілька повторів (repeats).
        """
        start = time.time()
        for _ in range(repeats):
            LruFibSystem.fibonacci_lru(n)
        end = time.time()
        return (end - start) / repeats

    def measure_splay_time(self, n: int, repeats=5) -> float:
        """
        Для кожного заміру створюємо новий SplayFibSystem().
        Виконуємо 'repeats' повторів, беремо середнє.
        """
        start = time.time()
        for _ in range(repeats):
            splay_fib = SplayFibSystem()
            splay_fib.fibonacci_splay(n)
        end = time.time()
        return (end - start) / repeats

    def run_comparison(self):
        logger.info(Fore.GREEN + "=== Starting FibComparison ===")

        # "Прогріємо" LruFibSystem хоч раз
        # (примітка: не скидаємо кеш @lru_cache, він зберігається між викликами)
        LruFibSystem.fibonacci_lru(1)

        for n in self.ns:
            logger.info(Fore.BLUE + f"Measuring times for n={n}")
            # LRU
            t_lru = self.measure_lru_time(n, repeats=3)
            # Splay
            t_splay = self.measure_splay_time(n, repeats=3)
            self.results_lru.append(t_lru)
            self.results_splay.append(t_splay)

        # Формуємо таблицю
        table_data = []
        for i, n in enumerate(self.ns):
            table_data.append(
                [n, f"{self.results_lru[i]:.8f}", f"{self.results_splay[i]:.8f}"]
            )

        print("\nРезультати порівняння (середній час, сек):")
        print(
            tabulate(
                table_data,
                headers=["n", "LRU Cache Time (s)", "Splay Tree Time (s)"],
                tablefmt="github",
            )
        )

        # Побудова графіка
        plt.figure(figsize=(8, 5))
        plt.plot(self.ns, self.results_lru, marker="o", label="LRU Cache")
        plt.plot(self.ns, self.results_splay, marker="x", label="Splay Tree")
        plt.title("Порівняння часу виконання для LRU Cache та Splay Tree")
        plt.xlabel("Число Фібоначчі (n)")
        plt.ylabel("Середній час виконання (сек)")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.show()


def main():
    sys.setrecursionlimit(10**7)
    comparison = FibComparison()
    comparison.run_comparison()


if __name__ == "__main__":
    main()
