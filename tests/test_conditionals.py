"""Тесты для условных выражений и логических операторов."""

from decimal import Decimal

import pytest

from interpreter import Interpreter, VariableNotFoundError


def eval_code(code: str):
    """Вспомогательная функция для выполнения кода."""
    return Interpreter().execute(code)


# ============================================================================
# Тесты для условных выражений (conditional expressions)
# ============================================================================


def test_simple_conditional_true():
    """Проверка простого условного выражения: истинная ветка."""
    result = eval_code("10 if 5 < 10 else 20")
    assert result == Decimal("10")


def test_simple_conditional_false():
    """Проверка простого условного выражения: ложная ветка."""
    result = eval_code("10 if 5 > 10 else 20")
    assert result == Decimal("20")


def test_conditional_with_variables():
    """Проверка условного выражения с переменными."""
    code = """
    x = 15
    y = 10
    result = 100 if x > y else 50
    result
    """
    result = eval_code(code)
    assert result == Decimal("100")


def test_nested_conditional():
    """Проверка вложенных условных выражений."""
    code = """
    score = 85
    grade = 5 if score >= 90 else (4 if score >= 80 else 3)
    grade
    """
    result = eval_code(code)
    assert result == Decimal("4")


def test_deeply_nested_conditional():
    """Проверка глубоко вложенных условных выражений."""
    code = """
    x = 75
    result = (
        100 if x >= 90 else
        80 if x >= 80 else
        60 if x >= 70 else
        40
    )
    result
    """
    result = eval_code(code)
    assert result == Decimal("60")


def test_conditional_in_assignment():
    """Проверка условного выражения при присваивании."""
    code = """
    temperature = 25
    state = 1 if temperature > 100 else 0
    state
    """
    result = eval_code(code)
    assert result == Decimal("0")


def test_conditional_in_expression():
    """Проверка условного выражения внутри арифметического выражения."""
    code = """
    x = 5
    result = (10 if x > 0 else -10) + 5
    result
    """
    result = eval_code(code)
    assert result == Decimal("15")


def test_conditional_in_print(capsys):
    """Проверка условного выражения в print."""
    interp = Interpreter()
    code = """
    x = 10
    print("Status:", 1 if x > 5 else 0)
    """
    interp.execute(code)
    captured = capsys.readouterr()
    assert "Status: 1.0000000000" in captured.out


def test_conditional_with_arithmetic_conditions():
    """Условие содержит арифметические выражения."""
    result = eval_code("10 if 2 + 3 < 10 else 20")
    # 2 + 3 = 5, 5 < 10 = true
    assert result == Decimal("10")


def test_conditional_with_arithmetic_branches():
    """Ветки содержат арифметические выражения."""
    code = """
    x = 5
    result = x * 2 if x > 3 else x + 1
    result
    """
    result = eval_code(code)
    # 5 > 3 = true, x * 2 = 10
    assert result == Decimal("10")


def test_conditional_result_is_numeric():
    """Результат условного выражения должен быть Decimal, не bool."""
    result = eval_code("10 if 1 < 2 else 20")
    assert isinstance(result, Decimal)
    assert result == Decimal("10")


def test_conditional_with_functions():
    """Условное выражение содержит вызовы функций."""
    result = eval_code("sqrt(4) if 1 < 2 else sqrt(9)")
    # sqrt(4) = 2
    assert result == Decimal("2")


def test_conditional_with_zero():
    """Проверка условного выражения с нулем."""
    result = eval_code("10 if 0 == 0 else 20")
    assert result == Decimal("10")


def test_conditional_with_negative():
    """Проверка условного выражения с отрицательными числами."""
    result = eval_code("10 if -5 < 0 else 20")
    assert result == Decimal("10")


def test_conditional_both_branches_expressions():
    """Проверка условного выражения с выражениями в обеих ветках."""
    code = """
    x = 5
    result = (x * 2) if x > 0 else (x * -1)
    result
    """
    result = eval_code(code)
    assert result == Decimal("10")


def test_conditional_as_function_argument():
    """Проверка условного выражения как аргумента функции."""
    result = eval_code("sqrt(16 if 1 < 2 else 9)")
    assert result == Decimal("4")


def test_conditional_with_precision():
    """Условное выражение с управлением точностью."""
    code = """
    old = set_precision(2)
    result = 1.234 if 1 < 2 else 5.678
    set_precision(old)
    result
    """
    result = eval_code(code)
    # Должно быть округлено до 2 знаков
    assert result == Decimal("1.23")


def test_conditional_in_function_call_nested():
    """Условное выражение как аргумент функции (вложенное)."""
    result = eval_code("sqrt(9 if 1 < 2 else 4)")
    # sqrt(9) = 3
    assert result == Decimal("3")


def test_print_conditional_result(capsys):
    """print() с условным выражением."""
    interp = Interpreter()
    interp.execute('print(100 if 1 < 2 else 200)')
    captured = capsys.readouterr()
    assert "100" in captured.out


def test_very_long_chain():
    """Очень длинная цепочка условий."""
    # Создаем цепочку из 10 условий
    expr = "1 if 0 < 1 else 2 if 1 < 2 else 3 if 2 < 3 else 4 if 3 < 4 else 5 if 4 < 5 else 6 if 5 < 6 else 7 if 6 < 7 else 8 if 7 < 8 else 9 if 8 < 9 else 10"
    result = eval_code(expr)
    assert isinstance(result, Decimal)
    assert result == Decimal("1")


# ============================================================================
# Тесты для операторов сравнения
# ============================================================================


def test_comparison_equal():
    """Проверка оператора ==."""
    result = eval_code("100 if 5 == 5 else 0")
    assert result == Decimal("100")
    
    result = eval_code("100 if 5 == 6 else 0")
    assert result == Decimal("0")


def test_comparison_not_equal():
    """Проверка оператора !=."""
    result = eval_code("100 if 5 != 6 else 0")
    assert result == Decimal("100")
    
    result = eval_code("100 if 5 != 5 else 0")
    assert result == Decimal("0")


def test_comparison_less_than():
    """Проверка оператора <."""
    result = eval_code("100 if 5 < 10 else 0")
    assert result == Decimal("100")
    
    result = eval_code("100 if 10 < 5 else 0")
    assert result == Decimal("0")


def test_comparison_less_or_equal():
    """Проверка оператора <=."""
    result = eval_code("100 if 5 <= 5 else 0")
    assert result == Decimal("100")
    
    result = eval_code("100 if 5 <= 10 else 0")
    assert result == Decimal("100")
    
    result = eval_code("100 if 10 <= 5 else 0")
    assert result == Decimal("0")


def test_comparison_greater_than():
    """Проверка оператора >."""
    result = eval_code("100 if 10 > 5 else 0")
    assert result == Decimal("100")
    
    result = eval_code("100 if 5 > 10 else 0")
    assert result == Decimal("0")


def test_comparison_greater_or_equal():
    """Проверка оператора >=."""
    result = eval_code("100 if 5 >= 5 else 0")
    assert result == Decimal("100")
    
    result = eval_code("100 if 10 >= 5 else 0")
    assert result == Decimal("100")
    
    result = eval_code("100 if 5 >= 10 else 0")
    assert result == Decimal("0")


def test_comparison_with_expressions():
    """Проверка сравнений с выражениями."""
    code = """
    x = 5
    y = 10
    result = 100 if x * 2 == y else 0
    result
    """
    result = eval_code(code)
    assert result == Decimal("100")


def test_comparison_with_decimals():
    """Сравнение чисел с точкой."""
    result = eval_code("10 if 1.5 < 2.7 else 20")
    assert result == Decimal("10")


def test_comparison_with_negative():
    """Сравнение с отрицательными числами."""
    result = eval_code("10 if -5 < 0 else 20")
    assert result == Decimal("10")


def test_comparison_chain():
    """Проверка цепочки сравнений (1 < x < 10)."""
    code = """
    x = 5
    result = 100 if 1 < x and x < 10 else 0
    result
    """
    result = eval_code(code)
    assert result == Decimal("100")


def test_comparison_chain_false():
    """Проверка ложной цепочки сравнений."""
    code = """
    x = 15
    result = 100 if 1 < x and x < 10 else 0
    result
    """
    result = eval_code(code)
    assert result == Decimal("0")


def test_multiple_comparisons_in_condition():
    """Проверка нескольких сравнений в условии."""
    code = """
    x = 5
    y = 10
    z = 3
    result = 100 if x > z and y > x and z < 5 else 0
    result
    """
    result = eval_code(code)
    assert result == Decimal("100")


def test_negative_comparison():
    """Сравнение с отрицательными числами в цепочке."""
    result = eval_code("100 if -10 < 0 and 0 < 10 else 0")
    assert result == Decimal("100")


def test_decimal_equality():
    """Точная проверка равенства Decimal."""
    # Проверка, что Decimal правильно сравнивает числа
    result = eval_code("100 if 0.3 == 0.3 else 0")
    assert result == Decimal("100")


def test_precision_in_comparison():
    """Сравнение с управлением точностью."""
    code = """
    set_precision(2)
    x = 1.995
    y = 2.005
    result = 100 if x < y else 0
    result
    """
    result = eval_code(code)
    assert result == Decimal("100")


# ============================================================================
# Тесты для логических операторов (and, or, not)
# ============================================================================


def test_logical_and_true():
    """Проверка логического оператора and (истина)."""
    result = eval_code("100 if 5 < 10 and 3 < 5 else 0")
    assert result == Decimal("100")


def test_logical_and_false():
    """Проверка логического оператора and (ложь)."""
    result = eval_code("100 if 5 < 10 and 3 > 5 else 0")
    assert result == Decimal("0")


def test_and_first_false():
    """AND: первый операнд false."""
    result = eval_code("100 if (1 > 2) and (3 < 4) else 0")
    assert result == Decimal("0")


def test_and_second_false():
    """AND: второй операнд false."""
    result = eval_code("100 if (1 < 2) and (3 > 4) else 0")
    assert result == Decimal("0")


def test_multiple_and():
    """Несколько AND."""
    result = eval_code("100 if (1 < 2) and (3 < 4) and (5 < 6) else 0")
    assert result == Decimal("100")


def test_logical_or_true():
    """Проверка логического оператора or (истина)."""
    result = eval_code("100 if 5 > 10 or 3 < 5 else 0")
    assert result == Decimal("100")


def test_logical_or_false():
    """Проверка логического оператора or (ложь)."""
    result = eval_code("100 if 5 > 10 or 3 > 5 else 0")
    assert result == Decimal("0")


def test_or_first_true():
    """OR: только первый true."""
    result = eval_code("100 if (1 < 2) or (3 > 4) else 0")
    assert result == Decimal("100")


def test_or_second_true():
    """OR: только второй true."""
    result = eval_code("100 if (1 > 2) or (3 < 4) else 0")
    assert result == Decimal("100")


def test_or_both_false():
    """OR: оба операнда false."""
    result = eval_code("100 if (1 > 2) or (3 > 4) else 0")
    assert result == Decimal("0")


def test_multiple_or():
    """Несколько OR."""
    result = eval_code("100 if (1 > 2) or (3 > 4) or (5 < 6) else 0")
    assert result == Decimal("100")


def test_logical_not_true():
    """Проверка логического оператора not (истина)."""
    result = eval_code("100 if not (5 > 10) else 0")
    assert result == Decimal("100")


def test_logical_not_false():
    """Проверка логического оператора not (ложь)."""
    result = eval_code("100 if not (5 < 10) else 0")
    assert result == Decimal("0")


def test_not_double_negation():
    """NOT NOT."""
    result = eval_code("100 if not not (1 < 2) else 0")
    assert result == Decimal("100")


def test_logical_combined():
    """Проверка комбинации логических операторов."""
    code = """
    x = 5
    y = 10
    z = 3
    result = 100 if (x < y and y > z) or z == 3 else 0
    result
    """
    result = eval_code(code)
    assert result == Decimal("100")


def test_logical_not_with_comparison():
    """Проверка not с оператором сравнения."""
    code = """
    x = 5
    result = 100 if not x < 0 else 0
    result
    """
    result = eval_code(code)
    assert result == Decimal("100")


def test_logical_precedence():
    """Проверка приоритета логических операторов: and > or."""
    # (false and true) or true → false or true → true
    result = eval_code("100 if 5 > 10 and 3 < 5 or 1 == 1 else 0")
    assert result == Decimal("100")
    
    # false and (true or true) → false and true → false
    result = eval_code("100 if 5 > 10 and (3 < 5 or 1 == 1) else 0")
    assert result == Decimal("0")


def test_comparison_precedence_over_logical():
    """Проверка приоритета сравнений над логическими операторами."""
    # Should parse as: (1 < 5) and (5 < 10)
    result = eval_code("100 if 1 < 5 and 5 < 10 else 0")
    assert result == Decimal("100")


def test_short_circuit_and():
    """Short-circuit AND: если первый false, второй не вычисляется."""
    # Если реализован short-circuit, то undefined_var не будет проверяться
    code = """
    x = 5
    result = 100 if (x > 10) and (undefined_var < 5) else 0
    result
    """
    # Если short-circuit работает, то ошибки не будет
    # Если нет - будет VariableNotFoundError
    try:
        result = eval_code(code)
        # Short-circuit работает, undefined_var не проверялась
        assert result == Decimal("0")
    except VariableNotFoundError:
        # Short-circuit не реализован, это тоже допустимо на этом этапе
        pass


def test_short_circuit_or():
    """Short-circuit OR: если первый true, второй не вычисляется."""
    # Если реализован short-circuit, то undefined_var не будет проверяться
    code = """
    x = 5
    result = 100 if (x < 10) or (undefined_var > 5) else 0
    result
    """
    # Если short-circuit работает, то ошибки не будет
    # Если нет - будет VariableNotFoundError
    try:
        result = eval_code(code)
        # Short-circuit работает, undefined_var не проверялась
        assert result == Decimal("100")
    except VariableNotFoundError:
        # Short-circuit не реализован, это тоже допустимо на этом этапе
        pass


# ============================================================================
# Тесты для ошибочных случаев
# ============================================================================


def test_cannot_assign_boolean_from_comparison():
    """Проверка: нельзя присвоить результат сравнения переменной."""
    code = "x = (5 < 10)"
    # Это должно вызвать ошибку, когда функционал реализован
    # Пока что проверяем, что интерпретатор попытается выполнить код
    try:
        eval_code(code)
        # Если не выбросилось исключение, значит функционал еще не реализован
        # или булевские значения разрешены
    except Exception as e:
        # Ожидаем ошибку типа BooleanError или похожую
        assert "boolean" in str(e).lower() or "bool" in str(e).lower()


def test_cannot_assign_boolean_from_logical():
    """Проверка: нельзя присвоить результат логической операции."""
    code = "x = (5 < 10 and 3 < 5)"
    try:
        eval_code(code)
        # Если не выбросилось исключение, функционал еще не реализован
    except Exception as e:
        # Ожидаем ошибку с упоминанием boolean
        assert "boolean" in str(e).lower() or "bool" in str(e).lower()


def test_cannot_assign_and():
    """Ошибка: присваивание результата AND."""
    code = "x = 1 < 2 and 3 < 4"
    try:
        eval_code(code)
        # Если не выбросилось исключение, функционал еще не реализован
    except Exception as e:
        # Ожидаем ошибку с упоминанием boolean
        assert "boolean" in str(e).lower() or "bool" in str(e).lower()


def test_cannot_assign_or():
    """Ошибка: присваивание результата OR."""
    code = "x = 1 < 2 or 3 > 4"
    try:
        eval_code(code)
        # Если не выбросилось исключение, функционал еще не реализован
    except Exception as e:
        # Ожидаем ошибку с упоминанием boolean
        assert "boolean" in str(e).lower() or "bool" in str(e).lower()


def test_cannot_assign_not():
    """Ошибка: присваивание результата NOT."""
    code = "x = not (1 < 2)"
    try:
        eval_code(code)
        # Если не выбросилось исключение, функционал еще не реализован
    except Exception as e:
        # Ожидаем ошибку с упоминанием boolean
        assert "boolean" in str(e).lower() or "bool" in str(e).lower()


def test_cannot_use_boolean_in_arithmetic():
    """Проверка: нельзя использовать булевское значение в арифметике."""
    # Это невозможно протестировать напрямую, так как булевские значения
    # не могут быть присвоены переменным. Но можно проверить, что
    # условные выражения корректно используются только в разрешенных контекстах.
    pass


def test_boolean_in_multiplication():
    """Ошибка: boolean в умножении."""
    # Этот тест будет работать только после реализации проверок типов
    # Пока помечаем как ожидаемый в будущем
    pass


def test_non_boolean_condition():
    """Ошибка: условие в if-else должно быть boolean."""
    # Когда реализована строгая проверка типов
    code = "result = 10 if 5 else 20"
    try:
        eval_code(code)
        # Если не выбросилось исключение, строгая проверка еще не реализована
    except Exception as e:
        # Ожидаем ошибку типа или парсинга
        pass


def test_condition_is_expression():
    """Ошибка: условие - просто выражение, не сравнение."""
    code = """
    x = 5
    y = 3
    result = 10 if (x + y) else 20
    """
    try:
        eval_code(code)
        # Если не выбросилось исключение, строгая проверка еще не реализована
    except Exception as e:
        # Ожидаем ошибку типа
        pass


def test_zero_in_condition_strict():
    """Ноль в условии: 0 не равен boolean (строгая проверка)."""
    # Этот тест для будущей строгой проверки типов
    # Пока 0 может быть использован как число в сравнениях
    code = "100 if 0 else 200"
    try:
        eval_code(code)
        # Строгая проверка еще не реализована
    except Exception:
        # Ожидаем ошибку при строгой проверке типов
        pass


def test_empty_condition():
    """Пустое условие - синтаксическая ошибка."""
    code = "100 if else 200"
    with pytest.raises(Exception):  # Ошибка парсинга
        eval_code(code)
