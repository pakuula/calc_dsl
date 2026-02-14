# Дизайн: Условные выражения и булевские операторы

## 1. Требования

- Условные выражения: `expr-A if cond-expr else expr-B`
- Оператор сравнения: `==`, `<`, `<=`, `>`, `>=`, `!=`
- Логические операторы: `and`, `or`, `not`
- **Ограничение**: булевские значения допустимы **ТОЛЬКО** в условных выражениях (нельзя присваивать переменным)

## 2. Приоритеты операторов (от высшего к низшему)

```
1. unary          : (-), (+)
2. power          : **
3. product        : *, /, mod
4. sum            : +, -
5. comparison     : ==, !=, <, <=, >, >=
6. logical_and    : and
7. logical_or     : or
8. not            : not
9. conditional    : if else
```

**Примеры:**
- `1 + 2 < 3` → `(1 + 2) < 3` → `3 < 3` → false
- `x = 5 * 2 + 3` → `x = (5 * 2) + 3` (ок, sum возвращает Decimal)
- `x = (1 < 2)` → ошибка (нельзя присваивать boolean)
- `1 < 2 and 3 < 4` → `(1 < 2) and (3 < 4)` → true and true → true
- `not x < 5` → `not (x < 5)` (not имеет высший приоритет!)

❗ **Важно**: `not` привязывается слабее, чем `<`. Т.е. `not x < 5` означает `not (x < 5)`.

## 3. Грамматика (Lark)

### Новая иерархия выражений

```lark
?expr: conditional_expr

?conditional_expr: or_expr
                 | or_expr "if" or_expr "else" conditional_expr

?or_expr: and_expr ("or" and_expr)*

?and_expr: not_expr ("and" not_expr)*

?not_expr: "not" not_expr
         | comparison

?comparison: sum ((COMP_OP) sum)*

?sum: product ((PLUS | MINUS) product)*
?product: power ((STAR | SLASH | MOD) power)*
?power: unary (POW power)?
?unary: (PLUS | MINUS) unary
      | atom

COMP_OP: "==" | "!=" | "<" | "<=" | ">" | ">="
```

**Примечание о `conditional_expr`:**
- Это не регулярная бинарная операция
- Форма 1: `expr` (без условия)
- Форма 2: `or_expr "if" or_expr "else" conditional_expr`
- Рекурсивна вправо для поддержки вложенных условий: `A if B else C if D else E`

## 4. Архитектура интерпретатора

### Типы значений

В интерпретаторе существуют:
- `Decimal` — числовые значения
- `bool` (Python native) — булевские значения (используются только внутри условных выражений)

### Узлы дерева разбора

Новые типы узлов:

```python
# Tree.data == "conditional_expr"
#   children: [or_expr, or_expr, conditional_expr]  # condition, then_expr, else_expr
#   OR
#   children: [or_expr]  # just expression without condition

# Tree.data == "or_expr"
#   children: [and_expr, ...]

# Tree.data == "and_expr"
#   children: [not_expr, ...]

# Tree.data == "not_expr"
#   children: [not_expr | comparison]

# Tree.data == "comparison"
#   children: [sum, COMP_OP, sum, COMP_OP, sum, ...]
#   (может быть цепочка: 1 < 2 < 3, но эту семантику нужно определить)
```

### Методы интерпретатора

Новые методы:

```python
def _eval_conditional_expr(self, node: Tree) -> Any:
    """Выполнить условное выражение."""
    # Если только одно выражение → вернуть результат
    # Если три → вычислить условие (bool), выбрать ветку

def _eval_or_expr(self, node: Tree) -> bool:
    """Выполнить логический OR."""
    # Лево-ассоциативный: (A or B) or C

def _eval_and_expr(self, node: Tree) -> bool:
    """Выполнить логический AND."""
    # Лево-ассоциативный: (A and B) and C

def _eval_not_expr(self, node: Tree) -> bool:
    """Выполнить логический NOT."""

def _eval_comparison(self, node: Tree) -> bool:
    """Выполнить сравнение."""
    # Может быть цепочка: 1 < 2 < 3 → (1 < 2) and (2 < 3)
```

### Семантика булевских значений

```python
def _is_boolean_context(self, node: Tree) -> bool:
    """Проверить, находится ли узел в булевском контексте."""
    # Булевский контекст = внутри условного выражения, логических операций, сравнений

def _ensure_numeric(self, value: Any) -> Decimal:
    """Убедиться, что значение - число. Если bool → ошибка."""
    if isinstance(value, bool):
        raise DSLError(f"Cannot use boolean value as number")
    return self._to_decimal(value)
```

## 5. Примеры синтаксиса и семантики

### Условные выражения

```clc
# Простое условие
result = 10 if 5 < 10 else 20
# result = 10.0000000000

# Вложенные условия
grade = 
    "A" if score >= 90 else
    "B" if score >= 80 else
    "C"
# Ошибка: нельзя присваивать строки!

# Правильно (в выводе)
print(
    "Good" if x > 5 else "Bad"
)

# Условие в цикле
for i in 1 .. 10 (
    x = i * 2 if i <= 5 else i
)
```

### Сравнения

```clc
x = 5
y = 10

# Простые сравнения
print(x < y)        # true
print(x == 5)       # true
print(x != y)       # true

# Цепочки сравнений
print(1 < x and x < y)   # true
print(x >= 5 and x <= 10)  # true
```

### Логические операции

```clc
# AND / OR
x = 5 if 3 < 5 and 5 < 10 else 0

# NOT
y = 20 if not (x < 0) else 10

# Приоритеты
# not x < 5    →  not (x < 5)
# x and y < 5  →  x and (y < 5)  — но x должен быть bool!
# x < 5 and y  →  (x < 5) and y   — а y должен быть bool!
```

### Ошибки

```clc
# ❌ Ошибка: попытка присвоить boolean
x = (1 < 2)
# DSLError: Cannot assign boolean value to variable

# ❌ Ошибка: попытка использовать boolean в арифметике
z = (1 < 2) + 5
# DSLError: Boolean value cannot be used in arithmetic

# ✅ Правильно: boolean только в условных выражениях
z = 10 if (1 < 2) else 5
```

## 6. План реализации (для @coder)

### Фаза 1: Грамматика
1. Обновить `grammar.lark` с новой иерархией выражений
2. Добавить токены для операторов сравнения и логических операций
3. Добавить правила для `conditional_expr`, `or_expr`, `and_expr`, `not_expr`, `comparison`

### Фаза 2: Интерпретатор — базовая структура
1. Добавить методы: `_eval_conditional_expr`, `_eval_or_expr`, `_eval_and_expr`, `_eval_not_expr`, `_eval_comparison`
2. Обновить `_eval()` для обработки новых типов узлов
3. Добавить проверки для отклонения булевских значений в неправильных контекстах

### Фаза 3: Оптимизация логических операций
1. Реализовать short-circuit evaluation для `and` и `or`
2. Добавить tests для edge cases

### Фаза 4: Тестирование и документация
1. Написать тесты для условных выражений
2. Написать тесты для сравнений
3. Написать тесты для логических операций
4. Обновить примеры и README

## 7. Цепочки сравнений: Дизайн решения

**Вопрос**: Поддерживать ли цепочки вроде `1 < x < 10`?

**Решение**: ДА, поддерживать.

**Семантика**: `1 < x < 10` → `(1 < x) and (x < 10)`

**Реализация в грамматике**:
```lark
?comparison: sum ((COMP_OP sum)+)?
             # Может быть:
             # sum              (если нет операторов)
             # sum COMP_OP sum  (один оператор)
             # sum COMP_OP sum COMP_OP sum  (цепочка)
```

**Реализация в интерпретаторе**:
```python
def _eval_comparison(self, node: Tree) -> Any:
    children = node.children
    if len(children) == 1:
        # Просто выражение: sum
        return self._eval(children[0])
    
    # Цепочка: sum OP sum OP sum ...
    result = True
    for i in range(0, len(children) - 1, 2):
        left = self._to_decimal(self._eval(children[i]))
        op = children[i + 1].value
        right = self._to_decimal(self._eval(children[i + 2]))
        
        if not self._compare(left, op, right):
            result = False
            break
    
    return result
```

## 8. Ошибки и обработка

### Новые ошибки

```python
class BooleanError(DSLError):
    """Попытка использовать булево значение в неправильном контексте."""
    pass
```

### Проверка типов

**Во время присваивания:**
```python
def _eval_assignment(self, node: Tree) -> None:
    # ...
    value = self._eval(rhs)
    if isinstance(value, bool):
        raise BooleanError(
            f"Cannot assign boolean value to variable {name_token.value}",
            line=name_token.line,
            column=name_token.column,
        )
```

**В арифметических операциях:**
```python
def _eval_sum(self, node: Tree) -> Decimal:
    # ...
    for i in range(1, len(children), 2):
        left = self._eval(children[i - 1])
        if isinstance(left, bool):
            raise BooleanError(...)
```

## 9. Примеры тестов

```python
def test_simple_conditional():
    interp = Interpreter()
    result = interp.execute("10 if 5 < 10 else 20")
    assert result == Decimal("10")

def test_nested_conditional():
    interp = Interpreter()
    interp.set_variable("x", Decimal("85"))
    result = interp.execute("5 if x >= 90 else (4 if x >= 80 else 3)")
    assert result == Decimal("4")

def test_comparison_chain():
    interp = Interpreter()
    interp.set_variable("x", Decimal("5"))
    result = interp.execute("1 < x and x < 10")
    # Should be true, but for now we test individual comparisons

def test_cannot_assign_bool():
    interp = Interpreter()
    with pytest.raises(BooleanError):
        interp.execute("x = (1 < 2)")

def test_logical_operators():
    interp = Interpreter()
    # Test and
    result = interp.execute("5 if (3 < 5 and 5 < 10) else 0")
    assert result == Decimal("5")
```

## 10. Обпечение обратной совместимости

- Все существующие скрипты должны продолжать работать
- Новые операторы не конфликтуют с существующим синтаксисом
- Нижайшие приоритета условного выражения гарантируют правильный разбор

---

**Статус**: Draft, готово к реализации
