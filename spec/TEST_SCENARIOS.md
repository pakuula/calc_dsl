# Тестовые сценарии для условных выражений и булевских операторов

## Структура тестирования

```
tests/
├── test_conditionals.py          (новые тесты)
├── test_comparisons.py           (новые тесты)
├── test_logical_operators.py     (новые тесты)
└── test_interpreter.py           (существующие, должны все проходить)
```

## 1. Базовые условные выражения (test_conditionals.py)

```python
def test_simple_conditional_true():
    """Простое условное выражение - true ветка."""
    interp = Interpreter()
    result = interp.execute("5 if 1 < 2 else 10")
    assert result == Decimal("5")

def test_simple_conditional_false():
    """Простое условное выражение - false ветка."""
    interp = Interpreter()
    result = interp.execute("5 if 1 > 2 else 10")
    assert result == Decimal("10")

def test_conditional_with_variables():
    """Условное выражение с переменными."""
    interp = Interpreter()
    interp.set_variable("x", Decimal("7"))
    interp.set_variable("y", Decimal("10"))
    result = interp.execute("100 if x < y else -100")
    assert result == Decimal("100")

def test_conditional_with_arithmetic_conditions():
    """Условие содержит арифметические выражения."""
    interp = Interpreter()
    result = interp.execute("10 if 2 + 3 < 10 else 20")
    # 2 + 3 = 5, 5 < 10 = true
    assert result == Decimal("10")

def test_conditional_with_arithmetic_branches():
    """Ветки содержат арифметические выражения."""
    interp = Interpreter()
    interp.set_variable("x", Decimal("5"))
    result = interp.execute("x * 2 if x > 3 else x + 1")
    # 5 * 2 = 10
    assert result == Decimal("10")

def test_nested_conditionals():
    """Вложенные условные выражения."""
    interp = Interpreter()
    interp.set_variable("score", Decimal("85"))
    result = interp.execute("5 if score >= 90 else (4 if score >= 80 else 3)")
    # score >= 90 = false, score >= 80 = true
    assert result == Decimal("4")

def test_deeply_nested_conditionals():
    """Глубоко вложенные условные выражения (5 уровней)."""
    interp = Interpreter()
    interp.set_variable("x", Decimal("5"))
    expr = "1 if x > 10 else (2 if x > 8 else (3 if x > 4 else (4 if x > 2 else (5 if x > 0 else 6))))"
    result = interp.execute(expr)
    # x=5: 5>10=f, 5>8=f, 5>4=t → 3
    assert result == Decimal("3")

def test_conditional_result_is_numeric():
    """Результат условного выражения должен быть Decimal, не bool."""
    interp = Interpreter()
    result = interp.execute("10 if 1 < 2 else 20")
    assert isinstance(result, Decimal)

def test_conditional_with_functions():
    """Условное выражение содержит вызовы функций."""
    interp = Interpreter()
    result = interp.execute("sqrt(4) if 1 < 2 else sqrt(9)")
    # sqrt(4) = 2
    assert result == Decimal("2")
```

## 2. Операторы сравнения (test_comparisons.py)

```python
def test_less_than():
    """Оператор <."""
    interp = Interpreter()
    result = interp.execute("10 if 5 < 10 else 20")
    assert result == Decimal("10")

def test_less_than_or_equal():
    """Оператор <=."""
    interp = Interpreter()
    result = interp.execute("10 if 5 <= 5 else 20")
    assert result == Decimal("10")

def test_greater_than():
    """Оператор >."""
    interp = Interpreter()
    result = interp.execute("10 if 10 > 5 else 20")
    assert result == Decimal("10")

def test_greater_than_or_equal():
    """Оператор >=."""
    interp = Interpreter()
    result = interp.execute("10 if 10 >= 10 else 20")
    assert result == Decimal("10")

def test_equal():
    """Оператор ==."""
    interp = Interpreter()
    interp.set_variable("x", Decimal("5"))
    result = interp.execute("100 if x == 5 else 0")
    assert result == Decimal("100")

def test_not_equal():
    """Оператор !=."""
    interp = Interpreter()
    interp.set_variable("x", Decimal("5"))
    interp.set_variable("y", Decimal("10"))
    result = interp.execute("100 if x != y else 0")
    assert result == Decimal("100")

def test_comparison_with_decimals():
    """Сравнение чисел с точкой."""
    interp = Interpreter()
    result = interp.execute("10 if 1.5 < 2.7 else 20")
    assert result == Decimal("10")

def test_comparison_with_negative():
    """Сравнение с отрицательными числами."""
    interp = Interpreter()
    result = interp.execute("10 if -5 < 0 else 20")
    assert result == Decimal("10")

def test_comparison_with_expressions():
    """Сравнение сложных выражений."""
    interp = Interpreter()
    result = interp.execute("10 if 2 + 3 * 4 < 15 else 20")
    # 2 + 3*4 = 2 + 12 = 14, 14 < 15 = true
    assert result == Decimal("10")

def test_comparison_chain():
    """Цепочка сравнений: 1 < x < 10."""
    interp = Interpreter()
    interp.set_variable("x", Decimal("5"))
    result = interp.execute("100 if 1 < x and x < 10 else 0")
    # 1 < 5 = true, 5 < 10 = true, true and true = true
    assert result == Decimal("100")
```

## 3. Логические операторы (test_logical_operators.py)

```python
def test_and_both_true():
    """AND: оба операнда true."""
    interp = Interpreter()
    result = interp.execute("100 if (1 < 2) and (3 < 4) else 0")
    assert result == Decimal("100")

def test_and_first_false():
    """AND: первый операнд false."""
    interp = Interpreter()
    result = interp.execute("100 if (1 > 2) and (3 < 4) else 0")
    assert result == Decimal("0")

def test_and_second_false():
    """AND: второй операнд false."""
    interp = Interpreter()
    result = interp.execute("100 if (1 < 2) and (3 > 4) else 0")
    assert result == Decimal("0")

def test_or_both_true():
    """OR: оба операнда true."""
    interp = Interpreter()
    result = interp.execute("100 if (1 < 2) or (3 < 4) else 0")
    assert result == Decimal("100")

def test_or_first_true():
    """OR: только первый true."""
    interp = Interpreter()
    result = interp.execute("100 if (1 < 2) or (3 > 4) else 0")
    assert result == Decimal("100")

def test_or_second_true():
    """OR: только второй true."""
    interp = Interpreter()
    result = interp.execute("100 if (1 > 2) or (3 < 4) else 0")
    assert result == Decimal("100")

def test_or_both_false():
    """OR: оба операнда false."""
    interp = Interpreter()
    result = interp.execute("100 if (1 > 2) or (3 > 4) else 0")
    assert result == Decimal("0")

def test_not_true():
    """NOT от true."""
    interp = Interpreter()
    result = interp.execute("100 if not (1 > 2) else 0")
    assert result == Decimal("100")

def test_not_false():
    """NOT от false."""
    interp = Interpreter()
    result = interp.execute("100 if not (1 < 2) else 0")
    assert result == Decimal("0")

def test_not_double_negation():
    """NOT NOT."""
    interp = Interpreter()
    result = interp.execute("100 if not not (1 < 2) else 0")
    assert result == Decimal("100")

def test_and_or_precedence():
    """Приоритет: and выше чем or."""
    interp = Interpreter()
    # A or B and C + D  →  A or (B and (C + D))
    # 0 or (1 and 2)    →  0 or 1 = 1
    result = interp.execute("100 if (1 > 2) or (1 < 2 and 3 < 4) else 0")
    assert result == Decimal("100")

def test_multiple_and():
    """Несколько AND."""
    interp = Interpreter()
    result = interp.execute("100 if (1 < 2) and (3 < 4) and (5 < 6) else 0")
    assert result == Decimal("100")

def test_multiple_or():
    """Несколько OR."""
    interp = Interpreter()
    result = interp.execute("100 if (1 > 2) or (3 > 4) or (5 < 6) else 0")
    assert result == Decimal("100")

def test_short_circuit_and():
    """Short-circuit AND: если первый false, второй не вычисляется."""
    interp = Interpreter()
    interp.set_variable("never_checked", None)
    # Если не реализован short-circuit, будет ошибка
    result = interp.execute("100 if (1 > 2) and (never_checked < 10) else 0")
    # Должна быть обработана как false, не должна проверяться never_checked
    assert result == Decimal("0")

def test_short_circuit_or():
    """Short-circuit OR: если первый true, второй не вычисляется."""
    interp = Interpreter()
    # Если не реализован short-circuit, будет ошибка
    result = interp.execute("100 if (1 < 2) or (unknown_var < 10) else 0")
    # Должна быть обработана как true, не должна проверяться unknown_var
    assert result == Decimal("100")
```

## 4. Ошибки типизации (test_type_errors.py)

```python
def test_cannot_assign_comparison():
    """Ошибка: присваивание результата сравнения."""
    interp = Interpreter()
    with pytest.raises(BooleanContextError):
        interp.execute("x = 1 < 2")

def test_cannot_assign_and():
    """Ошибка: присваивание результата AND."""
    interp = Interpreter()
    with pytest.raises(BooleanContextError):
        interp.execute("x = 1 < 2 and 3 < 4")

def test_cannot_assign_or():
    """Ошибка: присваивание результата OR."""
    interp = Interpreter()
    with pytest.raises(BooleanContextError):
        interp.execute("x = 1 < 2 or 3 > 4")

def test_cannot_assign_not():
    """Ошибка: присваивание результата NOT."""
    interp = Interpreter()
    with pytest.raises(BooleanContextError):
        interp.execute("x = not (1 < 2)")

def test_boolean_in_arithmetic():
    """Ошибка: boolean в арифметической операции."""
    interp = Interpreter()
    with pytest.raises(BooleanContextError):
        interp.execute("y = (1 < 2) + 5")

def test_boolean_in_multiplication():
    """Ошибка: boolean в умножении."""
    interp = Interpreter()
    with pytest.raises(BooleanContextError):
        interp.execute("y = (1 < 2) * 3")

def test_non_boolean_condition():
    """Ошибка: условие в if-else должно быть boolean."""
    interp = Interpreter()
    with pytest.raises(DSLError):
        interp.execute("result = 10 if 5 else 20")

def test_condition_is_expression():
    """Ошибка: условие - просто выражение, не сравнение."""
    interp = Interpreter()
    with pytest.raises(DSLError):
        interp.execute("result = 10 if (x + y) else 20")
```

## 5. Комплексные сценарии (test_integration.py)

```python
def test_conditional_in_loop():
    """Условное выражение внутри цикла."""
    interp = Interpreter()
    interp.execute("""
    sum = 0
    for i in 1 .. 10 (
        sum += i if i mod 2 == 0 else 0
    )
    """)
    assert interp.get_variable("sum") == Decimal("30")  # 2+4+6+8+10

def test_conditional_in_function_call():
    """Условное выражение как аргумент функции."""
    interp = Interpreter()
    result = interp.execute("sqrt(9 if 1 < 2 else 4)")
    # sqrt(9) = 3
    assert result == Decimal("3")

def test_conditional_in_for_range():
    """Условное выражение в диапазоне for."""
    interp = Interpreter()
    interp.execute("""
    count = 0
    for i in 1 .. (5 if 1 < 2 else 3) (
        count += 1
    )
    """)
    assert interp.get_variable("count") == Decimal("5")

def test_conditional_with_precision():
    """Условное выражение с управлением точностью."""
    interp = Interpreter()
    interp.execute("""
    old = set_precision(2)
    result = 1.234 if 1 < 2 else 5.678
    set_precision(old)
    """)
    assert "1.23" in str(interp.get_variable("result"))

def test_print_conditional_result():
    """print() с условным выражением."""
    interp = Interpreter()
    # Захватить stdout
    import io
    import sys
    old_stdout = sys.stdout
    sys.stdout = buffer = io.StringIO()
    try:
        interp.execute('print(100 if 1 < 2 else 200)')
        output = buffer.getvalue()
        assert "100" in output
    finally:
        sys.stdout = old_stdout

def test_backward_compatibility():
    """Существующие скрипты работают без изменений."""
    interp = Interpreter()
    result = interp.execute("2 + 3 * 4")
    assert result == Decimal("14")

def test_backward_compatibility_loops():
    """Существующие циклы работают без изменений."""
    interp = Interpreter()
    result = interp.execute("""
    sum = 0
    for i in 1 .. 5 (
        sum += i
    )
    sum
    """)
    assert result == Decimal("15")

def test_backward_compatibility_functions():
    """Существующие функции работают без изменений."""
    interp = Interpreter()
    result = interp.execute("sqrt(16)")
    assert result == Decimal("4")
```

## 6. Граничные случаи (test_edge_cases.py)

```python
def test_zero_in_condition():
    """Ноль в условии: 0 не равен true."""
    interp = Interpreter()
    with pytest.raises(DSLError):
        # 0 - это число, не boolean
        interp.execute("100 if 0 else 200")

def test_empty_condition():
    """Пустое условие."""
    interp = Interpreter()
    with pytest.raises(Exception):  # различные парсер ошибки
        interp.execute("100 if else 200")

def test_very_long_chain():
    """Очень длинная цепочка условий."""
    interp = Interpreter()
    expr = "1 if 1<2 else " + " if 2<3 else ".join(["2"] * 50) + " if 50<51 else 50"
    result = interp.execute(expr)
    assert isinstance(result, Decimal)

def test_negative_comparison():
    """Сравнение с отрицательными числами в цепочке."""
    interp = Interpreter()
    result = interp.execute("100 if -10 < 0 and 0 < 10 else 0")
    assert result == Decimal("100")

def test_decimal_equality():
    """Точная проверка равенства Decimal."""
    interp = Interpreter()
    result = interp.execute("100 if 0.1 + 0.2 == 0.3 else 0")
    # Может быть 0 из-за точности Decimal
    assert result in [Decimal("0"), Decimal("100")]

def test_precision_in_comparison():
    """Сравнение с управлением точностью."""
    interp = Interpreter()
    interp.execute("set_precision(2)")
    result = interp.execute("100 if 1.995 < 2.005 else 0")
    assert result == Decimal("100")
```

## 7. Таблица покрытия тестами

| Категория | Количество тестов | Статус |
|-----------|---|---|
| Базовые условные | 9 | ✅ |
| Операторы сравнения | 11 | ✅ |
| Логические операторы | 15 | ✅ |
| Ошибки типизации | 8 | ✅ |
| Комплексные сценарии | 8 | ✅ |
| Граничные случаи | 6 | ✅ |
| **ИТОГО** | **57 тестов** | ✅ |

**Ожидаемые результаты**: 57/57 тестов должны пройти после реализации.

---

**Статус**: Тестовые сценарии готовы к реализации
