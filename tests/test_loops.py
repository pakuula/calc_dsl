"""Тесты для циклов for."""

from decimal import Decimal

import pytest

from interpreter import Interpreter, VariableNotFoundError


def eval_code(code: str):
    """Вспомогательная функция для выполнения кода."""
    return Interpreter().execute(code)


def test_for_expression_result():
    """Проверка результата выражения for."""
    code = """
    n = 5
    prev = 0
    curr = 1
    fib = for i in 2..n (
        next = prev + curr
        prev = curr
        curr = next
        curr
    )
    fib
    """
    result = eval_code(code)
    assert result == Decimal("5")


def test_for_expression_with_range_expression():
    """Проверка выражения for с выражением диапазона."""
    code = """
    n = 9
    prev = 0
    curr = 1

    fib = for i in 2..(n+1) (
        next = curr + prev
        print("i=", i, "next=", next)
        prev = curr
        curr = next
        curr
    )

    fib
    """
    result = eval_code(code)
    assert result == Decimal("55")


def test_loop_variable_visibility_when_predefined():
    """Проверка видимости переменной цикла, если она уже определена."""
    code = """
    i = 10
    for i in 1..3 (i)
    i
    """
    result = eval_code(code)
    assert result == Decimal("3")


def test_loop_variable_not_visible_when_new():
    """Проверка видимости переменной цикла, если она новая."""
    code = """
    for i in 1..1 (i)
    i
    """
    with pytest.raises(VariableNotFoundError):
        eval_code(code)


def test_loop_not_run_keeps_original_value():
    """Проверка, что если цикл не выполняется, сохраняется исходное значение переменной."""
    code = """
    i = 7
    for i in 5..1 by -2 (i)
    i
    """
    result = eval_code(code)
    assert result == Decimal("1")


def test_conditional_in_for_range():
    """Условное выражение в диапазоне for."""
    code = """
    count = 0
    for i in 1 .. (5 if 1 < 2 else 3) (
        count += 1
    )
    count
    """
    result = eval_code(code)
    assert result == Decimal("5")


def test_conditional_in_loop():
    """Проверка условного выражения внутри цикла."""
    code = """
    sum = 0
    for i in 1..5 (
        value = i * 2 if i <= 3 else i
        sum += value
        value
    )
    sum
    """
    result = eval_code(code)
    assert result == Decimal("21")  # (2 + 4 + 6 + 4 + 5)


def test_conditional_in_loop_with_mod():
    """Условное выражение внутри цикла с mod."""
    code = """
    sum = 0
    for i in 1 .. 10 (
        sum += i if i mod 2 == 0 else 0
    )
    sum
    """
    result = eval_code(code)
    assert result == Decimal("30")  # 2 + 4 + 6 + 8 + 10


def test_backward_compatibility_loops():
    """Существующие циклы работают без изменений."""
    code = """
    sum = 0
    for i in 1 .. 5 (
        sum += i
    )
    sum
    """
    result = eval_code(code)
    assert result == Decimal("15")
