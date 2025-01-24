import logging
from colorama import init, Fore
import sys
import timeit
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
# 2. Класи для Splay-дерева
# ======================================
class Node:
    def __init__(self, data, value, parent=None):
        self.data = data  # n
        self.value = value  # fib(n)
        self.parent = parent
        self.left_node = None
        self.right_node = None


class SplayTree:
    def __init__(self):
        self.root = None

    def insert(self, data, value):
        if self.root is None:
            self.root = Node(data, value)
        else:
            self._insert_node(data, value, self.root)
        node = self.find_node(data)
        if node:
            self._splay(node)

    def _insert_node(self, data, value, current_node):
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
        node = self.find_node(data)
        if node:
            self._splay(node)
            return node.value
        return None

    def find_node(self, data):
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
    def __init__(self):
        self.tree = SplayTree()
        self.tree.insert(0, 0)
        self.tree.insert(1, 1)

    def fibonacci_splay(self, n: int) -> int:
        val = self.tree.search(n)
        if val is not None:
            return val
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
    Порівнюємо час виконання fibonacci_lru vs fibonacci_splay
    з використанням timeit.timeit().
    """

    def __init__(self):
        # 0..950 (крок 50)
        self.ns = list(range(0, 951, 50))
        self.results_lru = []
        self.results_splay = []

    def measure_lru_time(self, n: int, repeats=3) -> float:
        """
        Використовуємо timeit.timeit(...) з setup_code та stmt_code.
        """
        setup_code = f"""\
from __main__ import LruFibSystem
"""
        stmt_code = f"LruFibSystem.fibonacci_lru({n})"
        total_time = 0.0
        # Кілька повторів (для усереднення)

        total_time = timeit.timeit(stmt=stmt_code, setup=setup_code, number=repeats)
        return total_time / repeats

    def measure_splay_time(self, n: int, repeats=3) -> float:
        """
        Використовуємо timeit.timeit(...) для SplayFibSystem,
        кожен виклик створює новий SplayFibSystem()
        """
        setup_code = f"""\
from __main__ import SplayFibSystem
fib_sys = SplayFibSystem()
"""
        stmt_code = f"fib_sys.fibonacci_splay({n})"
        import timeit

        total_time = timeit.timeit(stmt=stmt_code, setup=setup_code, number=repeats)
        return total_time / repeats

    def run_comparison(self):
        logger.info(Fore.GREEN + "=== Starting FibComparison with timeit ===")

        for n in self.ns:
            logger.info(Fore.BLUE + f"Measuring times for n={n}")
            t_lru = self.measure_lru_time(n, repeats=3)
            t_splay = self.measure_splay_time(n, repeats=3)
            self.results_lru.append(t_lru)
            self.results_splay.append(t_splay)

        # Формуємо таблицю
        table_data = []
        for i, n in enumerate(self.ns):
            table_data.append(
                [n, f"{self.results_lru[i]:.8f}", f"{self.results_splay[i]:.8f}"]
            )

        print("\nРезультати порівняння (timeit, середній час, сек):")
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
        plt.title("Порівняння часу (timeit) для LRU Cache та Splay Tree")
        plt.xlabel("Число Фібоначчі (n)")
        plt.ylabel("Середній час (сек)")
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
