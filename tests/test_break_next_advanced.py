"""Дополнительные тесты для глубокого тестирования break и next.

Рекомендуемые тестовые сценарии для повышения покрытия и надежности.
"""

# import pytest
# pytestmark = pytest.mark.skip("The tests are under construction")

import unittest
from decimal import Decimal
from interpreter import Interpreter, DSLError


def eval_code(code: str, initial_env=None):
    """Вспомогательная функция для выполнения кода."""
    interp = Interpreter(initial_env=initial_env)
    return interp.execute(code)


# ============================================================================
# Тесты граничных случаев производительности
# ============================================================================

class TestBreakNextPerformance(unittest.TestCase):
    """Тесты на оптимизацию и производительность"""

    def test_break_early_large_range(self):
        """Производительность: Break в начале большого диапазона"""
        code = """
        for i in 1 .. 1000000 (
            break when i == 1 with 42 
        )
        """
        result = eval_code(code)
        # Должен выполниться быстро, не пройдя все миллион итераций
        self.assertEqual(result, Decimal(42))

    def test_next_most_iterations_skipped(self):
        """Производительность: Next пропускает большинство итераций"""
        code = """
        count = 0
        for i in 1 .. 100000 (
            next when 1==1
            count += 1
        )
        count
        """
        result = eval_code(code)
        # Все итерации выполнены, но с next
        self.assertEqual(result, Decimal(0))

    def test_break_from_deeply_nested_large(self):
        """Производительность: Break from из глубоко вложенных циклов"""
        code = """
        for i in 1 .. 100 (
            for j in 1 .. 100 (
                for k in 1 .. 100 (
                    break from i when k == 50 with i
                )
            )
        )
        """
        result = eval_code(code)
        # Должен выйти при первой же итерации когда k==50
        self.assertEqual(result, Decimal(1))


# ============================================================================
# Тесты с математическими операциями
# ============================================================================

class TestBreakNextWithMathOperations(unittest.TestCase):
    """Тесты break/next с математическими функциями"""

    def test_break_with_trigonometric_functions(self):
        """Break с тригонометрическими функциями"""
        code = """
        set_precision(5)
        for i in 1 .. 360 by 30 (
            break when cos(i * pi / 180) < -0.5 with i
        )
        """
        result = eval_code(code)
        # cos становится < -0.5 при углах больше 120 градусов
        # 120 или 150 в зависимости от точности
        self.assertTrue(Decimal(120) <= result <= Decimal(150))

    def test_next_filtering_by_modular_arithmetic(self):
        """Next с модульной арифметикой"""
        code = """
        sum = 0
        for i in 1 .. 100 (
            next when (i * i) mod 13 == 0
            sum += 1
        )
        sum
        """
        result = eval_code(code)
        # Подсчет чисел где (i*i) mod 13 != 0
        self.assertGreater(result, Decimal(90))

    def test_break_with_power_operations(self):
        """Break с операциями возведения в степень"""
        code = """
        for i in 1 .. 100 (
            break when i ** 2 > 1000 with i * 2
        )
        """
        result = eval_code(code)
        # i^2 > 1000 при i > sqrt(1000) ≈ 31.6, т.е. при i=32
        # result = 32 * 2 = 64
        self.assertEqual(result, Decimal(64))

    # def test_next_with_factorial_recursion(self):
    #     """Next с рекурсивным вычислением факториала"""
    #     code = """
    #     fact(n) = if n <= 1 then 1 else n * fact(n - 1)
        
    #     sum = 0
    #     for i in 1 .. 10 (
    #         next when fact(i) mod 100 == 0
    #         sum += fact(i)
    #     )
    #     sum
    #     """
    #     result = eval_code(code)
    #     # Факториалы: 1,2,6,24,120,720,5040,...
    #     # 120 mod 100 = 20, 720 mod 100 = 20, 5040 mod 100 = 40
    #     # Нет факториалов кратных 100 в этом диапазоне
    #     self.assertGreater(result, Decimal(0))


# ============================================================================
# Тесты с комбинированными условиями
# ============================================================================

class TestBreakNextComplexConditions(unittest.TestCase):
    """Тесты с комплексными условиями"""

    def test_break_with_compound_condition(self):
        """Break с составным условием (AND/OR)"""
        code = """
        for i in 1 .. 100 (
            break when (i > 50 and i mod 7 == 0) or i > 99 with i
        )
        """
        result = eval_code(code)
        # i mod 7 == 0: 7,14,21,28,35,42,49,56,...
        # Первое значение >50 кратное 7: 56
        self.assertEqual(result, Decimal(56))

    def test_next_with_multiple_conditions(self):
        """Next с множественными условиями"""
        code = """
        sum = 0
        for i in 1 .. 50 (
            next when (i mod 2 == 0 and i mod 3 == 0) or (i mod 5 == 0 and i < 25)
            sum += i
        )
        sum
        """
        result = eval_code(code)
        # Пропускаем:
        # - Числа кратные 2 И 3 (т.е. кратные 6): 6,12,18,24,30,36,42,48
        # - Числа кратные 5 И < 25: 5,10,15,20
        self.assertGreater(result, Decimal(0))

    def test_break_with_nested_conditions(self):
        """Break с вложенными условиями"""
        code = """
        for i in 1 .. 100 (
            break when i > 20 and i mod 11 == 0 with i
        )
        """
        result = eval_code(code)
        # Первое число > 20 кратное 11: 22
        self.assertEqual(result, Decimal(22))

    def test_next_condition_depends_on_accumulator(self):
        """Next с условием, зависящим от аккумулятора"""
        code = """
        sum = 0
        for i in 1 .. 100 (
            next when sum > 500
            sum += i
        )
        sum
        """
        result = eval_code(code)
        # Накапливаем до 500, потом пропускаем
        # 1+2+...+31 = 496, 1+...+32 = 528
        self.assertGreater(result, Decimal(500))


# ============================================================================
# Тесты с побочными эффектами
# ============================================================================

class TestBreakNextSideEffects(unittest.TestCase):
    """Тесты на побочные эффекты и модификацию состояния"""

    # def test_break_preserves_variable_modifications(self):
    #     """Break сохраняет побочные эффекты переменных"""
    #     code = """
    #     sum = 0
    #     count = 0
    #     for i in 1 .. 10 (
    #         sum += i
    #         count += 1
    #         break when i == 5 with 999
    #     )
    #     (sum, count)
    #     """
    #     result = eval_code(code)
    #     # sum должна быть 1+2+3+4+5 = 15
    #     # count должен быть 5
    #     self.assertEqual(result[0], Decimal(15))
    #     self.assertEqual(result[1], Decimal(5))

    # def test_next_preserves_partial_modifications(self):
    #     """Next сохраняет частичные модификации"""
    #     code = """
    #     sum = 0
    #     for i in 1 .. 5 (
    #         partial = i * 2
    #         next when i == 3
    #         sum += partial
    #     )
    #     (sum, partial)
    #     """
    #     result = eval_code(code)
    #     # i=1: partial=2, sum=2
    #     # i=2: partial=4, sum=6
    #     # i=3: partial=6, next
    #     # i=4: partial=8, sum=14
    #     # i=5: partial=10, sum=24
    #     # partial из последней итерации: 10
    #     self.assertEqual(result[0], Decimal(24))
    #     self.assertEqual(result[1], Decimal(10))

    # def test_break_with_global_state_modification(self):
    #     """Break с модификацией глобального состояния"""
    #     code = """
    #     state = []
    #     for i in 1 .. 5 (
    #         state += (i)
    #         break when len(state) >= 3 with i * 100
    #     )
    #     """
    #     result = eval_code(code)
    #     # state должна быть [1,2,3]
    #     # Результат цикла = 3 * 100 = 300
    #     self.assertEqual(result, Decimal(300))

    # def test_next_does_not_affect_previous_modifications(self):
    #     """Next не отменяет предыдущие модификации"""
    #     code = """
    #     values = ()
    #     for i in 1 .. 5 (
    #         values += (i)
    #         next when i == 3
    #         next when i == 4
    #     )
    #     len(values)
    #     """
    #     result = eval_code(code)
    #     # Все значения должны быть добавлены несмотря на next
    #     self.assertEqual(result, Decimal(5))


# ============================================================================
# Тесты граничных условий циклов
# ============================================================================

class TestBreakNextLoopBoundaries(unittest.TestCase):
    """Тесты граничных условий циклов"""

    def test_break_first_iteration_single_value_range(self):
        """Break на первой (и единственной) итерации"""
        code = """
        for i in 42 .. 42 (
            break with i * 2
        )
        """
        result = eval_code(code)
        self.assertEqual(result, Decimal(84))

    def test_next_all_iterations_single_value_range(self):
        """Next на единственной итерации"""
        code = """
        result = 0
        for i in 5 .. 5 (
            next
            result = i
        )
        result
        """
        result = eval_code(code)
        # Единственная итерация имеет next, поэтому result не изменяется
        self.assertEqual(result, Decimal(0))

    def test_break_empty_range(self):
        """Break в пустом диапазоне"""
        code = """
        for i in 10 .. 1 (
            break with 123
        )
        """
        result = eval_code(code)
        # Пустой цикл не выполняется
        self.assertIsNone(result)

    def test_next_empty_range(self):
        """Next в пустом диапазоне"""
        code = """
        for i in 10 .. 1 (
            next
        )
        """
        result = eval_code(code)
        # Пустой цикл
        self.assertIsNone(result)

    def test_break_at_loop_boundary(self):
        """Break точно на границе диапазона"""
        code = """
        for i in 1 .. 100 (
            break when i == 100 with i
        )
        """
        result = eval_code(code)
        self.assertEqual(result, Decimal(100))

    def test_next_skips_last_iteration(self):
        """Next пропускает последнюю итерацию"""
        code = """
        result = 0
        for i in 1 .. 5 (
            next when i == 5
            result = i
        )
        result
        """
        result = eval_code(code)
        # Последняя итерация пропущена, результат = i=4 = 4
        self.assertEqual(result, Decimal(4))


# ============================================================================
# Тесты с циклами и функциями
# ============================================================================

class TestBreakNextWithFunctions(unittest.TestCase):
    """Тесты break/next в контексте функций"""

    # def test_break_in_function_containing_loop(self):
    #     """Break в функции с циклом"""
    #     code = """
    #     sum_until(n) = (
    #         sum = 0
    #         for i in 1 .. n (
    #             break when sum > 20 with sum
    #             sum += i
    #         )
    #     )
    #     sum_until(10)
    #     """
    #     result = eval_code(code)
    #     # 1+2+3+4+5+6 = 21 > 20
    #     self.assertEqual(result, Decimal(21))

    # def test_next_in_function_filter(self):
    #     """Next в функции для фильтрации"""
    #     code = """
    #     sum_even(n) = (
    #         sum = 0
    #         for i in 1 .. n (
    #             next when i mod 2 == 0
    #             sum += i
    #         )
    #         sum
    #     )
    #     sum_even(10)
    #     """
    #     result = eval_code(code)
    #     # 1+3+5+7+9 = 25
    #     self.assertEqual(result, Decimal(25))

    # def test_function_with_break_called_multiple_times(self):
    #     """Функция с break, вызванная несколько раз"""
    #     code = """
    #     first_gt(n, target) = (
    #         for i in 1 .. n (
    #             break when i > target with i
    #         )
    #     )
    #     (first_gt(10, 5), first_gt(20, 15))
    #     """
    #     result = eval_code(code)
    #     # first_gt(10, 5) должен вернуть 6
    #     # first_gt(20, 15) должен вернуть 16
    #     self.assertEqual(result[0], Decimal(6))
    #     self.assertEqual(result[1], Decimal(16))

    # def test_recursive_function_with_break_next(self):
    #     """Рекурсивная функция с break/next"""
    #     code = """
    #     sum_range(start, end, acc) = 
    #         if start > end then acc
    #         else if start mod 2 == 0 then
    #             sum_range(start + 1, end, acc)
    #         else
    #             sum_range(start + 1, end, acc + start)
        
    #     sum_range(1, 20, 0)
    #     """
    #     result = eval_code(code)
    #     # Сумма нечетных от 1 до 20: 1+3+5+7+9+11+13+15+17+19 = 100
    #     self.assertEqual(result, Decimal(100))


# ============================================================================
# Тесты с редкими расширенными сценариями
# ============================================================================

class TestBreakNextAdvancedScenarios(unittest.TestCase):
    """Продвинутые сценарии использования"""

    # def test_break_next_with_try_catch_semantics(self):
    #     """Break/Next в контексте, подобном try-catch"""
    #     code = """
    #     safe_divide(a, b) = (
    #         for i in 1 .. 1 (
    #             break when b == 0 with 0
    #             result = a / b
    #         )
    #     )
    #     safe_divide(10, 2)
    #     """
    #     result = eval_code(code)
    #     self.assertEqual(result, Decimal(5))

    # def test_state_machine_simulation_with_break_next(self):
    #     """Симуляция конечного автомата"""
    #     code = """
    #     state = "start"
    #     events = [1, 2, 3, 4, 5]
    #     result = 0
        
    #     for event in 1 .. 5 (
    #         if state == "start" then
    #             state = "processing"
    #         else if state == "processing" then
    #             if event > 3 then
    #                 break with event
    #             state = "done"
    #         result = event
    #     )
    #     result
    #     """
    #     result = eval_code(code)
    #     # event > 3 при event = 4
    #     self.assertEqual(result, Decimal(3))

    def test_binary_search_with_break(self):
        """Симуляция бинарного поиска"""
        code = """
        target = 42
        left = 1
        right = 100
        result = 0
        
        for iteration in 1 .. 20 (
            mid = (left + right) / 2
            break when mid == target with mid
            left = mid + 1 if mid < target else left
            right = mid - 1 if mid > target else right
            mid
        )
        """
        result = eval_code(code)
        # Поиск должен найти 42 за несколько итераций
        self.assertAlmostEqual(result, Decimal(42), places=3)

    # def test_generator_like_behavior_with_break_next(self):
    #     """Поведение, подобное генератору"""
    #     code = """
    #     sequence = ()
    #     for i in 1 .. 20 (
    #         next when i mod 4 == 0
    #         sequence += (i)
    #         break when len(sequence) >= 5 with sequence
    #     )
    #     """
    #     result = eval_code(code)
    #     # 1,2,3,5,6 (4 пропущена) => 5 элементов
    #     self.assertEqual(len(result), 5)


# ============================================================================
# Стресс-тесты
# ============================================================================

class TestBreakNextStress(unittest.TestCase):
    """Стресс-тесты для проверки надежности"""

    def test_many_nested_loops_with_break(self):
        """Много вложенных циклов с break"""
        code = """
        for i in 1 .. 10 (
            for j in 1 .. 10 (
                for k in 1 .. 10 (
                    for l in 1 .. 10 (
                        break from i when i == 2 and j == 2 with i + j
                    )
                )
            )
        )
        """
        result = eval_code(code)
        self.assertEqual(result, Decimal(4))

    def test_alternating_break_next_conditions(self):
        """Чередующиеся условия break и next"""
        code = """
        sum = 0
        for i in 1 .. 50 (
            next when i mod 2 == 0
            next when i mod 3 == 0
            next when i mod 5 == 0
            break when sum > 100 with sum
            sum += i
        )
        """
        result = eval_code(code)
        # Пропускаем числа кратные 2, 3 или 5
        # Суммируем остальные до превышения 100
        self.assertGreater(result, Decimal(100))

    def test_rapid_consecutive_breaks(self):
        """Быстро следующие друг за другом breaks"""
        code = """
        for i in 1 .. 100 (
            break when i == 1 with 100
            break when i == 2 with 200
            break when i == 3 with 300
        )
        """
        result = eval_code(code)
        # Только первый break срабатывает
        self.assertEqual(result, Decimal(100))


# ============================================================================
# Тесты с типами данных
# ============================================================================

class TestBreakNextWithDataTypes(unittest.TestCase):
    """Тесты с различными типами данных"""

    # def test_break_with_tuple_result(self):
    #     """Break с кортежем как результат"""
    #     code = """
    #     for i in 1 .. 10 (
    #         break when i == 5 with (i, i*2, i*3)
    #     )
    #     """
    #     result = eval_code(code)
    #     self.assertEqual(result, (Decimal(5), Decimal(10), Decimal(15)))

    # def test_next_with_tuple_accumulation(self):
    #     """Next при накоплении кортежей"""
    #     code = """
    #     tuples = ()
    #     for i in 1 .. 5 (
    #         next when i mod 2 == 0
    #         tuples += ((i, i*2))
    #     )
    #     len(tuples)
    #     """
    #     result = eval_code(code)
    #     # 2 нечетных числа: 1, 3, 5
    #     self.assertEqual(result, Decimal(3))

    def test_break_with_decimal_precision(self):
        """Break с высокой точностью Decimal"""
        code = """
        set_precision(50)
        for i in 1 .. 1000 (
            val = pi * i / 180
            break when sin(val) > 0.999 with val
        )
        """
        result = eval_code(code)
        # sin(x) > 0.999 при x близко к pi/2 ≈ 90 градусов
        self.assertGreater(result, Decimal(1.5))


if __name__ == '__main__':
    unittest.main()
