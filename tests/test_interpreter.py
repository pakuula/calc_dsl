"""Тесты для интерпретатора."""

from decimal import Decimal

import pytest

from interpreter import DivisionByZeroError, Interpreter, VariableNotFoundError


def eval_code(code: str):
    """Вспомогательная функция для выполнения кода."""
    return Interpreter().execute(code)


# ============================================================================
# Базовые тесты арифметики и операторов
# ============================================================================


def test_operator_precedence():
    """Проверка правильного порядка операций."""
    result = eval_code("2 + 2 * 2")
    assert result == Decimal("6")


def test_power_mod_precedence():
    """Проверка возведения в степень по модулю."""
    result = eval_code("2 ** 3 mod 5")
    assert result == Decimal("3")


def test_assignments_sequence():
    """Проверка последовательных присваиваний и операторов присваивания."""
    result = eval_code("x = 5; x += 10; x mod= 4; x")
    assert result == Decimal("3")


def test_negative_mod_semantics():
    """Проверка остатка от деления для отрицательных чисел."""
    result = eval_code("-5 mod 3")
    assert result == Decimal("1")


# ============================================================================
# Тесты математических функций
# ============================================================================


def test_math_functions():
    """Проверка математических функций."""
    result = eval_code("sqrt(4)")
    assert result == Decimal("2")
    result = eval_code("sin(pi/2)")
    assert result == Decimal("1")
    result = eval_code("ln(e)")
    assert result == Decimal("1")
    result = eval_code("nrt(27, 3)")
    assert result == Decimal("3")


# ============================================================================
# Тесты обработки ошибок
# ============================================================================


def test_division_by_zero():
    """Проверка обработки деления на ноль."""
    with pytest.raises(DivisionByZeroError):
        eval_code("1 / 0")


def test_domain_errors():
    """Проверка обработки ошибок области определения для функций."""
    with pytest.raises(Exception):
        eval_code("sqrt(-1)")


def test_undefined_variable():
    """Проверка обращения к неопределённой переменной."""
    with pytest.raises(VariableNotFoundError):
        eval_code("x + 1")


# ============================================================================
# Тесты функций print и управления точностью
# ============================================================================


def test_print_allows_strings(capsys):
    """Проверка, что print может выводить строки."""
    interp = Interpreter()
    interp.execute('print("x =", 2 + 2)')
    captured = capsys.readouterr()
    assert captured.out.strip() == "x = 4.0000000000"


def test_precision_control():
    """Проверка функций get_precision и set_precision."""
    interp = Interpreter()

    # Default precision is 10
    result = interp.execute("get_precision()")
    assert result == Decimal("10")

    # Set precision to 5
    interp.execute("set_precision(5)")
    result = interp.execute("get_precision()")
    assert result == Decimal("5")

    # Set precision to 0 (allowed)
    interp.execute("set_precision(0)")
    result = interp.execute("get_precision()")
    assert result == Decimal("0")

    # Restore precision
    interp.execute("set_precision(10)")
    result = interp.execute("get_precision()")
    assert result == Decimal("10")


def test_precision_affects_formatting(capsys):
    """Проверка, что точность влияет на форматирование вывода print."""
    interp = Interpreter()
    code = """
x = 2 + 2 * 2
set_precision(4)
p = get_precision()
set_precision(0)
print("2 + 2 * 2 =", x)
set_precision(p)
print("2 + 2 * 2 =", x)
    """
    interp.execute(code)
    captured = capsys.readouterr()
    lines = captured.out.strip().split("\n")

    # First line: precision 0, should print "6" without decimal point
    assert lines[0] == "2 + 2 * 2 = 6"

    # Second line: precision 4, should print "6.0000" with 4 decimal places
    assert lines[1] == "2 + 2 * 2 = 6.0000"


def test_precision_zero_formats_as_integer(capsys):
    """Проверка, что точность 0 форматирует числа как целые."""
    interp = Interpreter()
    interp.execute("set_precision(0)")
    interp.execute('print("result:", 123.456789)')
    captured = capsys.readouterr()
    assert captured.out.strip() == "result: 123"

    # Test with whole number expression
    interp.execute("print(10 / 2)")
    captured = capsys.readouterr()
    assert captured.out.strip() == "5"


def test_precision_affects_calculations():
    """Проверка, что точность влияет на результаты вычислений."""
    interp = Interpreter()

    # With precision 2
    interp.execute("set_precision(2)")
    result = interp.execute("1 / 3")
    # Should be rounded to 2 decimal places
    assert result == Decimal("0.33")

    # With precision 5
    interp.execute("set_precision(5)")
    result = interp.execute("1 / 3")
    assert result == Decimal("0.33333")


def test_set_precision_returns_old_value():
    """Проверка, что set_precision возвращает старое значение точности."""
    interp = Interpreter()

    # Test exact user scenario: set_precision(10); p = set_precision(0); p
    code = """set_precision(10)
p = set_precision(0)
p"""
    result = interp.execute(code)
    assert result == Decimal("10")

    # Test chaining
    code = """set_precision(5)
old = set_precision(3)
old"""
    result = interp.execute(code)
    assert result == Decimal("5")


# ============================================================================
# Тесты обратной совместимости
# ============================================================================


def test_backward_compatibility():
    """Существующие скрипты работают без изменений."""
    result = eval_code("2 + 3 * 4")
    assert result == Decimal("14")


def test_backward_compatibility_functions():
    """Существующие функции работают без изменений."""
    result = eval_code("sqrt(16)")
    assert result == Decimal("4")

