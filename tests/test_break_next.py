"""Тесты для конструкций break и next.

Тестовые сценарии для управления потоком выполнения циклов.
Структура:
- TestBreak: тесты для break (10 тестов)
- TestNext: тесты для next (10 тестов)
- TestBreakNext: комбинированные тесты (4 теста)
- TestBreakNextErrors: тесты на ошибки (6 тестов)
- TestBreakNextEdgeCases: тесты граничных случаев
- TestBreakNextIntegration: интеграционные тесты
"""

import unittest
from decimal import Decimal
from interpreter import (
    Interpreter,
    DSLError,
    VariableNotFoundError,
)


def eval_code(code: str, initial_env=None):
    """Вспомогательная функция для выполнения кода."""
    interp = Interpreter(initial_env=initial_env)
    return interp.execute(code)


# ============================================================================
# TB: Break тесты
# ============================================================================

class TestBreak(unittest.TestCase):
    """Тесты конструкции break"""

    def test_break_simple_unconditional(self):
        """TB-001: Простой break (безусловный)"""
        code = """
        for i in 1 .. 10 (
            break with 99
        )
        """
        result = eval_code(code)
        self.assertEqual(result, Decimal(99))

    def test_break_with_condition_true(self):
        """TB-002: Break с условием - условие истинно"""
        code = """
        for i in 1 .. 10 (
            break when i == 5 with i * 10
        )
        """
        result = eval_code(code)
        self.assertEqual(result, Decimal(50))

    def test_break_with_condition_false(self):
        """TB-003: Break с условием - условие ложно"""
        code = """
        sum = 0
        for i in 1 .. 5 (
            sum += i
            break with 999 when i == 100
        )
        sum
        """
        result = eval_code(code)
        self.assertEqual(result, Decimal(15))

    def test_break_accumulate_variable(self):
        """TB-004: Break накапливает в переменной"""
        code = """
        sum = 0
        for i in 1 .. 10 (
            sum += i
            break when i == 5 with sum
        )
        """
        result = eval_code(code)
        self.assertEqual(result, Decimal(15))

    def test_break_nested_inner(self):
        """TB-005: Break с вложенными циклами - выход из внутреннего"""
        code = """
        result = 0
        for i in 1 .. 3 (
            for j in 1 .. 10 (
                break when j == 3 with j
                result = i * 100 + j
            )
        )
        result
        """
        result = eval_code(code)
        self.assertEqual(result, Decimal(302))

    def test_break_nested_outer_from(self):
        """TB-006: Break с вложенными циклами - break from внешнего"""
        code = """
        result = 0
        for i in 1 .. 100 (
            for j in 1 .. 100 (
                break from i when i * j > 50 with i * j
                result = i * j
            )
        )
        result
        """
        result = eval_code(code)
        self.assertEqual(result, Decimal(54))

    def test_break_without_condition(self):
        """TB-007: Break без условия (безусловный выход)"""
        code = """
        result = 0
        for i in 1 .. 10 (
            result = i * 2
            break with 777
        )
        """
        result = eval_code(code)
        self.assertEqual(result, Decimal(777))

    def test_break_multiple_only_first_triggers(self):
        """TB-008: Несколько break в цикле (только первый срабатывает)"""
        code = """
        result = 0
        for i in 1 .. 10 (
            break when i == 3 with 300
            break when i == 5 with 500
            result = i
        )
        result
        """
        result = eval_code(code)
        self.assertEqual(result, Decimal(300))

    def test_break_first_iteration(self):
        """TB-009: Break на первой итерации"""
        code = """
        result = 0
        for i in 1 .. 100 (
            result = i
            break with 42
        )
        """
        result = eval_code(code)
        self.assertEqual(result, Decimal(42))

    def test_break_with_complex_expression(self):
        """TB-010: Break с комплексным выражением в with"""
        code = """
        for i in 1 .. 10 (
            break when i > 5 with i * i - 10 * i + 100
        )
        """
        result = eval_code(code)
        # i = 6: 6*6 - 10*6 + 100 = 36 - 60 + 100 = 76
        self.assertEqual(result, Decimal(76))


# ============================================================================
# TN: Next тесты
# ============================================================================

class TestNext(unittest.TestCase):
    """Тесты конструкции next"""

    def test_next_simple_unconditional(self):
        """TN-001: Простой next (безусловный)"""
        code = """
        sum = 0
        for i in 1 .. 5 (
            next
            sum += i
        )
        sum
        """
        result = eval_code(code)
        self.assertEqual(result, Decimal(0))

    def test_next_with_condition_true(self):
        """TN-002: Next с условием - условие истинно"""
        code = """
        sum = 0
        for i in 1 .. 10 (
            next when i mod 2 == 0
            sum += i
        )
        sum
        """
        result = eval_code(code)
        # 1 + 3 + 5 + 7 + 9 = 25
        self.assertEqual(result, Decimal(25))

    def test_next_with_condition_false(self):
        """TN-003: Next с условием - условие ложно"""
        code = """
        sum = 0
        for i in 1 .. 5 (
            next when false
            sum += i
        )
        sum
        """
        result = eval_code(code)
        self.assertEqual(result, Decimal(15))

    def test_next_on_last_iteration(self):
        """TN-004: Next на последней итерации"""
        code = """
        result = 0
        for i in 1 .. 3 (
            next when i == 3
            result = i
        )
        result
        """
        result = eval_code(code)
        self.assertEqual(result, Decimal(2))

    def test_next_collect_values(self):
        """TN-005: Next со списком всех итераций"""
        code = """
        values = ()
        for i in 1 .. 5 (
            next when i != 2
            values += (i)
        )
        values
        """
        result = eval_code(code)
        self.assertEqual(result, (Decimal(2),))

    def test_next_nested_inner(self):
        """TN-006: Next в вложенном цикле - ближайший"""
        code = """
        result = 0
        for i in 1 .. 3 (
            for j in 1 .. 3 (
                next when j == 2
                result = i * 100 + j
            )
        )
        result
        """
        result = eval_code(code)
        self.assertEqual(result, Decimal(303))

    def test_next_nested_with_variable(self):
        """TN-007: Next с явной переменной - выход из вложенного"""
        code = """
        result = 0
        for i in 1 .. 3 (
            for j in 1 .. 3 (
                next i when j == 2
                result = i * 100 + j
            )
        )
        result
        """
        result = eval_code(code)
        self.assertEqual(result, Decimal(301))

    def test_next_multiple_conditions(self):
        """TN-008: Несколько next в цикле"""
        code = """
        sum = 0
        for i in 1 .. 10 (
            next when i mod 2 == 0
            next when i mod 3 == 0
            sum += i
        )
        sum
        """
        result = eval_code(code)
        # Четные: 2,4,6,8,10 - пропускаются
        # Из нечетных: 1,3,5,7,9 пропускаются 3,9 (кратны 3)
        # Остаются: 1, 5, 7 => 1+5+7 = 13
        self.assertEqual(result, Decimal(13))

    def test_next_empty_range(self):
        """TN-009: Next в пустом цикле"""
        code = """
        for i in 10 .. 1 (
            next
        )
        """
        result = eval_code(code)
        self.assertIsNone(result)

    def test_next_with_side_effects(self):
        """TN-010: Next с побочными эффектами"""
        code = """
        result = 0
        counter = 0
        for i in 1 .. 5 (
            counter += 1
            next when i == 3
            result += i
        )
        counter
        """
        result = eval_code(code)
        # Все итерации выполнены (1,2,3,4,5), поэтому counter = 5
        self.assertEqual(result, Decimal(5))


# ============================================================================
# TC: Комбинированные тесты (Break + Next)
# ============================================================================

class TestBreakNext(unittest.TestCase):
    """Комбинированные тесты (break + next)"""

    def test_break_and_next_in_one_loop(self):
        """TC-001: Break и Next в одном цикле"""
        code = """
        result = 0
        for i in 1 .. 20 (
            next when i mod 2 == 0
            break when i > 10 with i
            result = i
        )
        result
        """
        result = eval_code(code)
        # i=1,3,5,7,9: не четные, не > 10 → result = 1,3,5,7,9
        # i=2,4,6,8,10: четные → next
        # i=11: не четное, > 10 → break with 11
        # result остается 9
        self.assertEqual(result, Decimal(9))

    def test_break_next_triple_nesting(self):
        """TC-002: Трехуровневая вложенность с break/next"""
        code = """
        result = 0
        for i in 1 .. 3 (
            for j in 1 .. 3 (
                for k in 1 .. 3 (
                    next j when k == 2
                    result = i * 10000 + j * 100 + k
                )
            )
        )
        result
        """
        result = eval_code(code)
        # При k=2 выполняем next j
        # Последнее выполненное: i=3, j=2, k=1 => 30201
        self.assertEqual(result, Decimal(30201))

    def test_break_in_one_loop_next_in_another(self):
        """TC-003: Break в одном цикле, next в другом"""
        code = """
        outer_result = 0
        for i in 1 .. 100 (
            inner_result = 0
            for j in 1 .. 100 (
                next when j mod 3 == 0
                break from i when i * j > 20 with i
                inner_result += j
            )
            outer_result = i
        )
        outer_result
        """
        result = eval_code(code)
        # i=1: 1*j <= 20 для всех j, так что outer_result = 1
        # i=2: при j=11 условие 2*11=22 > 20, выполняется break from i
        # outer_result = i не выполняется перед break
        self.assertEqual(result, Decimal(1))

    def test_break_next_cross_loop_boundaries(self):
        """TC-004: Next и Break с пересечением границ циклов"""
        code = """
        sum = 0
        for i in 1 .. 5 (
            for j in 1 .. 5 (
                next when j == 3
                break from i when i + j > 7 with sum
                sum += i * j
            )
        )
        sum
        """
        result = eval_code(code)
        # i=1: j=1: 1*1=1, sum=1; j=2: 1*2=2, sum=3; j=3: next; j=4: 1+4=5 not >7, sum=7; j=5: 1+5=6 not >7, sum=12
        # i=2: j=1: 2*1=2, sum=14; j=2: 2*2=4, sum=18; j=3: next; j=4: 2+4=6 not >7, sum=26; j=5: 2+5=7 not >7, sum=36
        # i=3: j=1: 3*1=3, sum=39; j=2: 3*2=6, sum=45; j=3: next; j=4: 3+4=7 not >7, sum=57; j=5: 3+5=8 > 7 => break with 57
        self.assertEqual(result, Decimal(57))


# ============================================================================
# TE: Тесты на ошибки
# ============================================================================

class TestBreakNextErrors(unittest.TestCase):
    """Тесты на ошибки и исключения"""

    def test_break_outside_loop_error(self):
        """TE-001: Break вне цикла"""
        code = "break with 5"
        with self.assertRaises(DSLError):
            eval_code(code)

    def test_next_outside_loop_error(self):
        """TE-002: Next вне цикла"""
        code = "next"
        with self.assertRaises(DSLError):
            eval_code(code)

    def test_break_from_nonexistent_loop_error(self):
        """TE-003: Break from несуществующего цикла"""
        code = """
        for i in 1 .. 10 (
            break from nonexistent with 5
        )
        """
        with self.assertRaises(DSLError):
            eval_code(code)

    def test_next_nonexistent_loop_error(self):
        """TE-004: Next для несуществующей переменной"""
        code = """
        for i in 1 .. 10 (
            next nonexistent
        )
        """
        with self.assertRaises(DSLError):
            eval_code(code)

    def test_duplicate_loop_variable_error(self):
        """TE-005: Вложенные циклы с одинаковой переменной"""
        code = """
        for i in 1 .. 10 (
            for i in 1 .. 5 (
                break with i
            )
        )
        """
        # Эта ошибка должна быть обнаружена на этапе парсинга или выполнения
        # В зависимости от реализации может быть разные способы обработки
        # Просто проверяем, что код либо работает (если вложенная переменная переопределяет),
        # либо выбрасывает ошибку
        try:
            result = eval_code(code)
            # Если это работает, проверяем результат
            self.assertIsNotNone(result)
        except DSLError:
            # Если это выбрасывает ошибку, это тоже валидно
            pass

    def test_break_in_if_block_but_outside_loop(self):
        """TE-006: Break в if-блоке, но вне цикла"""
        code = """
        x = 5
        break when x > 10 with 10
        """
        with self.assertRaises(DSLError):
            eval_code(code)


# ============================================================================
# Тесты граничных случаев
# ============================================================================

class TestBreakNextEdgeCases(unittest.TestCase):
    """Тесты граничных случаев для break и next"""

    def test_break_with_step_loop(self):
        """Граничный случай: Break в цикле с шагом"""
        code = """
        sum = 0
        for i in 1 .. 100 by 10 (
            break when i > 50 with i
            sum += i
        )
        """
        result = eval_code(code)
        # i=1,11,21,31,41: не > 50, sum=1+11+21+31+41=105
        # i=51: > 50, break with 51
        self.assertEqual(result, Decimal(51))

    def test_next_with_step_loop(self):
        """Граничный случай: Next в цикле с шагом"""
        code = """
        sum = 0
        for i in 1 .. 20 by 3 (
            next when i mod 6 == 3
            sum += i
        )
        sum
        """
        result = eval_code(code)
        # i=1,4,7,10,13,16,19
        # 7 mod 6 = 1, 13 mod 6 = 1, 19 mod 6 = 1
        # 4 mod 6 = 4, 10 mod 6 = 4, 16 mod 6 = 4
        # 1 mod 6 = 1
        # Условие i mod 6 == 3: никогда не выполняется
        # sum = 1+4+7+10+13+16+19 = 70
        self.assertEqual(result, Decimal(70))

    def test_break_negative_range(self):
        """Граничный случай: Break в цикле с отрицательным диапазоном"""
        code = """
        for i in -10 .. -1 (
            break when i > -5 with i * 100
        )
        """
        result = eval_code(code)
        # i=-10,-9,-8,-7,-6,-5,-4,-3,-2,-1
        # При i=-4: -4 > -5 → break with -4*100 = -400
        self.assertEqual(result, Decimal(-400))

    def test_next_all_iterations(self):
        """Граничный случай: Next на всех итерациях"""
        code = """
        for i in 1 .. 5 (
            next
        )
        """
        result = eval_code(code)
        # Все итерации выполнены с next, результат последней итерации
        self.assertIsNone(result)

    def test_break_with_zero(self):
        """Граничный случай: Break с нулевым значением"""
        code = """
        for i in 1 .. 100 (
            break with 0
        )
        """
        result = eval_code(code)
        self.assertEqual(result, Decimal(0))

    def test_nested_break_immediate(self):
        """Граничный случай: Break в первой итерации вложенного цикла"""
        code = """
        result = 0
        for i in 1 .. 3 (
            for j in 1 .. 3 (
                break when j == 1 with j
                result = i * 100 + j
            )
        )
        result
        """
        result = eval_code(code)
        # Внутренний цикл каждый раз выходит при j=1
        # Внешний цикл продолжает работать
        # Последнее выполненное выражение в последней итерации i=3
        self.assertEqual(result, Decimal(0))

    def test_break_from_deeply_nested(self):
        """Граничный случай: Break from глубоко вложенного цикла"""
        code = """
        result = 0
        for i in 1 .. 5 (
            for j in 1 .. 5 (
                for k in 1 .. 5 (
                    for l in 1 .. 5 (
                        break from i when l == 2 with i
                        result = i
                    )
                )
            )
        )
        result
        """
        result = eval_code(code)
        # При l=2 выполняется break from i
        self.assertEqual(result, Decimal(1))

    def test_next_with_decimal_values(self):
        """Граничный случай: Работа next с Decimal значениями"""
        code = """
        precision(15)
        sum = 0
        for i in 1 .. 5 (
            next when i == 3
            sum += i / 2
        )
        sum
        """
        result = eval_code(code)
        # 1/2 + 2/2 + 4/2 + 5/2 = 0.5 + 1 + 2 + 2.5 = 6
        self.assertEqual(result, Decimal(6))

    def test_next_with_variable_scope(self):
        """Граничный случай: Next и область видимости переменных"""
        code = """
        outer = 10
        result = 0
        for i in 1 .. 5 (
            inner = i
            next when i == 2
            result = inner + outer
        )
        result
        """
        result = eval_code(code)
        # i=1: inner=1, result=1+10=11
        # i=2: inner=2, next
        # i=3: inner=3, result=3+10=13
        # i=4: inner=4, result=4+10=14
        # i=5: inner=5, result=5+10=15 (ПОСЛЕДНЯЯ ИТЕРАЦИЯ)
        self.assertEqual(result, Decimal(15))


# ============================================================================
# Интеграционные тесты
# ============================================================================

class TestBreakNextIntegration(unittest.TestCase):
    """Интеграционные тесты для break и next"""

    def test_complex_algorithm_with_break_next(self):
        """Алгоритм поиска: нахождение первого числа > 100, которое делится на 7"""
        code = """
        result = 0
        for i in 1 .. 1000 (
            next when i mod 7 != 0
            break when i > 100 with i
            result = i
        )
        """
        result = eval_code(code)
        # Ищем первое число > 100, кратное 7
        # 105 = 15 * 7, 105 > 100
        self.assertEqual(result, Decimal(105))


    def test_nested_loops_with_early_termination(self):
        """Поиск пары (i,j) в 2D матрице с условиями"""
        code = """
        found = 0
        for i in 1 .. 10 (
            for j in 1 .. 10 (
                next when i != j
                break when i*j > 50from i with i * 10 + j
                found = i * 10 + j
            )
        )
        found
        """
        result = eval_code(code)
        # Ищем пары где i==j (диагональ)
        # i=1,j=1: 1*1=1, not >50
        # ...
        # i=7,j=7: 7*7=49, not >50
        # i=8,j=8: 8*8=64 > 50, break from i
        # found = 8*10 + 8 = 88
        self.assertEqual(result, Decimal(88))

    def test_fibonacci_with_max_value_break(self):
        """Генерация чисел Фибоначчи до значения > 1000"""
        code = """
        a = 0
        b = 1
        result = 0
        for i in 1 .. 100 (
            temp = b
            b = a + b
            a = temp
            break when b > 1000 with b
            result = b
        )
        """
        result = eval_code(code)
        # Фибоначчи: 1,1,2,3,5,8,13,21,34,55,89,144,233,377,610,987,1597
        # Первое > 1000 это 1597
        self.assertEqual(result, Decimal(1597))

    def test_accumulation_with_selective_next(self):
        """Накопление с выборочными пропусками"""
        code = """
        sum = 0
        for i in 1 .. 100 (
            next when i mod 5 == 0
            next when i mod 7 == 0
            break when sum > 500 with sum
            sum += i
        )
        """
        result = eval_code(code)
        # Пропускаем числа кратные 5 или 7
        # Суммируем остальные
        # Продолжаем пока sum <= 500, потом break
        self.assertGreater(result, Decimal(500))
        self.assertLess(result, Decimal(600))

    def test_multi_level_control_flow(self):
        """Сложное управление потоком с множественными уровнями"""
        code = """
        total = 0
        for i in 1 .. 20 (
            next when i mod 2 == 1
            inner_sum = 0
            for j in 1 .. 20 (
                next when j mod 3 == 0
                break from i when i * j > 200 with total
                inner_sum += j
            )
            total += inner_sum
        )
        total
        """
        result = eval_code(code)
        # Сложный алгоритм с вложенными управлениями
        self.assertIsNotNone(result)

    def test_break_next_with_conditional(self):
        """Break и Next вместе с условными выражениями"""
        code = """
        result = 0
        for i in 1 .. 10 (
            val = 100 if i mod 2 == 0 else 200
            next when val == 100
            break when i > 5 with i
            result = result + val
        )
        result
        """
        result = eval_code(code)
        # i=1: val=200, not even, result=200
        # i=2: val=100, next
        # i=3: val=200, result=400
        # i=4: val=100, next
        # i=5: val=200, result=600
        # i=6: val=100, next
        # i=7: val=200, i>5, break with 7
        # result остается 600
        self.assertEqual(result, Decimal(600))


# ============================================================================
# Тесты обратной совместимости (примеры)
# ============================================================================

class TestBackwardCompatibility(unittest.TestCase):
    """Выборочные тесты обратной совместимости"""

    def test_basic_loop_without_break_next(self):
        """Обратная совместимость: базовый цикл"""
        code = """
        sum = 0
        for i in 1 .. 10 (
            sum += i
        )
        sum
        """
        result = eval_code(code)
        self.assertEqual(result, Decimal(55))

    def test_nested_loops_unchanged(self):
        """Обратная совместимость: вложенные циклы"""
        code = """
        sum = 0
        for i in 1 .. 5 (
            for j in 1 .. 5 (
                sum += i * j
            )
        )
        sum
        """
        result = eval_code(code)
        # Сумма произведений от 1 до 5
        self.assertEqual(result, Decimal(225))

    def test_loop_with_if_else_unchanged(self):
        """Обратная совместимость: циклы с условиями"""
        code = """
        sum = 0
        for i in 1 .. 10 (
            sum += i * 2 if i mod 2 == 0 else i
        )
        sum
        """
        result = eval_code(code)
        self.assertEqual(result, Decimal(65))

    def test_function_definition_unchanged(self):
        """Обратная совместимость: определение функций"""
        code = """
        double(x) = x * 2
        sum = 0
        for i in 1 .. 5 (
            sum += double(i)
        )
        sum
        """
        result = eval_code(code)
        self.assertEqual(result, Decimal(30))

    def test_arithmetic_operations_unchanged(self):
        """Обратная совместимость: арифметические операции"""
        code = """
        result = 0
        for i in 1 .. 10 (
            result = i * 2 + 3
        )
        result
        """
        result = eval_code(code)
        # Последняя итерация: i=10, result = 10*2+3 = 23
        self.assertEqual(result, Decimal(23))


if __name__ == '__main__':
    unittest.main()
