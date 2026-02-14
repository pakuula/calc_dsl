# Архитектура реализации: Условные выражения и булевские операторы

## Файл 1: grammar.lark (обновленная версия)

Новая иерархия выражений должна быть вставлена после `?expr:` и перед `?sum:`:

```lark
?expr: conditional_expr

?conditional_expr: or_expr
                 | or_expr "if" or_expr "else" conditional_expr

?or_expr: and_expr ("or" and_expr)*

?and_expr: not_expr ("and" not_expr)*

?not_expr: "not" not_expr
         | comparison

?comparison: sum (COMP_OP sum)*

?sum: product ((PLUS | MINUS) product)*

// ... rest remains the same
```

## Файл 2: interpreter.py (Новые методы и изменения)

### 2.1 Новый класс исключения

```python
class BooleanContextError(DSLError):
    """Булевское значение использовано в недопустимом контексте."""
    pass
```

### 2.2 Новые методы в классе Interpreter

```python
def _eval_conditional_expr(self, node: Tree) -> Any:
    """Выполнить условное выражение: expr if cond else expr.
    
    Форма 1: or_expr                              → просто вернуть значение
    Форма 2: or_expr "if" or_expr "else" rest    → условное выражение
    
    Args:
        node: Tree с node.data == "conditional_expr"
    
    Returns:
        Результат then-ветки или else-ветки (только Decimal!)
        
    Raises:
        RuntimeError: Если условие имеет тип Decimal вместо bool
    """
    if len(node.children) == 1:
        # Форма 1: just or_expr
        return self._eval(node.children[0])
    
    # Форма 2: or_expr "if" or_expr "else" conditional_expr
    # Структура: [or_expr_then, or_expr_cond, conditional_expr_else]
    then_expr = node.children[0]
    cond_expr = node.children[1]
    else_expr = node.children[2]
    
    # Вычислить условие - должно быть bool
    condition = self._eval(cond_expr)
    if not isinstance(condition, bool):
        raise DSLError(
            f"Condition in if-else must be boolean, got {type(condition).__name__}",
            line=cond_expr.meta.line if hasattr(cond_expr, 'meta') else None,
            column=cond_expr.meta.column if hasattr(cond_expr, 'meta') else None,
        )
    
    # Выбрать и вычислить нужную ветку
    if condition:
        result = self._eval(then_expr)
    else:
        result = self._eval(else_expr)
    
    # Результат должен быть Decimal (не boolean!)
    if isinstance(result, bool):
        raise BooleanContextError(
            f"Result of conditional expression must be numeric, got boolean",
            line=node.meta.line if hasattr(node, 'meta') else None,
            column=node.meta.column if hasattr(node, 'meta') else None,
        )
    
    return result


def _eval_or_expr(self, node: Tree) -> bool:
    """Выполнить логическое OR: A or B or C.
    
    Семантика: левая ассоциативность, short-circuit evaluation.
    
    Args:
        node: Tree с node.data == "or_expr"
    
    Returns:
        bool (True если хотя бы один operand == True)
        
    Raises:
        RuntimeError: Если operand имеет тип Decimal
    """
    # Если один child → это просто and_expr
    if len(node.children) == 1:
        return self._eval(node.children[0])
    
    # Несколько children: [and_expr, "or", and_expr, "or", and_expr, ...]
    # На четных индексах (0, 2, 4, ...) - выражения
    # На нечётных индексах (1, 3, 5, ...) - операторы "or" (Token)
    
    result = False
    for i in range(0, len(node.children), 2):
        operand = self._eval(node.children[i])
        if not isinstance(operand, bool):
            raise BooleanContextError(
                f"Operand of 'or' must be boolean, got {type(operand).__name__}",
                line=node.children[i].meta.line if hasattr(node.children[i], 'meta') else None,
            )
        result = result or operand
        # Short-circuit: если result уже True, дальше не вычисляем
        if result:
            break
    
    return result


def _eval_and_expr(self, node: Tree) -> bool:
    """Выполнить логическое AND: A and B and C.
    
    Семантика: левая ассоциативность, short-circuit evaluation.
    
    Returns:
        bool (True если все operands == True)
    """
    if len(node.children) == 1:
        return self._eval(node.children[0])
    
    result = True
    for i in range(0, len(node.children), 2):
        operand = self._eval(node.children[i])
        if not isinstance(operand, bool):
            raise BooleanContextError(
                f"Operand of 'and' must be boolean, got {type(operand).__name__}",
                line=node.children[i].meta.line if hasattr(node.children[i], 'meta') else None,
            )
        result = result and operand
        # Short-circuit: если result уже False, дальше не вычисляем
        if not result:
            break
    
    return result


def _eval_not_expr(self, node: Tree) -> bool:
    """Выполнить логическое NOT: not A.
    
    Returns:
        bool (!operand)
    """
    if len(node.children) == 1:
        # Нет "not", это просто comparison
        return self._eval(node.children[0])
    
    # Есть "not": [Token("not"), not_expr | comparison]
    operand = self._eval(node.children[1])
    if not isinstance(operand, bool):
        raise BooleanContextError(
            f"Operand of 'not' must be boolean, got {type(operand).__name__}",
        )
    return not operand


def _eval_comparison(self, node: Tree) -> Any:
    """Выполнить сравнение: A < B < C (цепочка сравнений) или просто sum.
    
    Если нет операторов сравнения → вернуть результат sum (Decimal).
    Если есть операторы → вернуть bool.
    
    Семантика цепочек: 1 < x < 10 → (1 < x) and (x < 10)
    
    Returns:
        Decimal если это просто sum, иначе bool
    """
    # Если один child → это просто sum
    if len(node.children) == 1:
        return self._eval(node.children[0])
    
    # Несколько children: [sum, COMP_OP, sum, COMP_OP, sum, ...]
    # На четных индексах (0, 2, 4, ...) - выражения (sum)
    # На нечётных индексах (1, 3, 5, ...) - операторы сравнения (Token)
    
    result = True
    for i in range(0, len(node.children) - 2, 2):
        left = self._to_decimal(self._eval(node.children[i]))
        op_token = node.children[i + 1]
        right = self._to_decimal(self._eval(node.children[i + 2]))
        
        op = op_token.value  # "==", "<", ">=" и т.д.
        
        if op == "==":
            cmp_result = left == right
        elif op == "!=":
            cmp_result = left != right
        elif op == "<":
            cmp_result = left < right
        elif op == "<=":
            cmp_result = left <= right
        elif op == ">":
            cmp_result = left > right
        elif op == ">=":
            cmp_result = left >= right
        else:
            raise DSLError(f"Unknown comparison operator: {op}")
        
        result = result and cmp_result
        if not result:
            break
    
    return result
```

### 2.3 Обновить метод _eval()

```python
def _eval(self, node: Any) -> Any:
    """Обновленный метод, добавить обработку новых типов узлов."""
    # ... существующий код ...
    
    # Добавить в основной if-elif блок:
    elif isinstance(node, Tree):
        if node.data == "conditional_expr":
            return self._eval_conditional_expr(node)
        elif node.data == "or_expr":
            return self._eval_or_expr(node)
        elif node.data == "and_expr":
            return self._eval_and_expr(node)
        elif node.data == "not_expr":
            return self._eval_not_expr(node)
        elif node.data == "comparison":
            return self._eval_comparison(node)
        # ... остальные elif блоки ...
```

### 2.4 Обновить методы арифметических операции

**В методе `_eval_sum()` и других арифметических методах добавить проверку:**

```python
def _eval_sum(self, node: Tree) -> Decimal:
    """Обновленный метод с проверкой типов."""
    children = node.children
    if len(children) == 1:
        result = self._eval(children[0])
        if isinstance(result, bool):
            raise BooleanContextError(
                "Boolean value cannot be used in arithmetic operation",
                line=node.meta.line if hasattr(node, 'meta') else None,
            )
        return self._to_decimal(result)
    
    # ... остальной код ...
```

Аналогично для `_eval_product()`, `_eval_power()`.

### 2.5 Обновить _eval_assignment()

```python
def _eval_assignment(self, node: Tree) -> None:
    """Обновленный метод, отклонить булевские значения."""
    name_token = node.children[0]
    # ... вычислить value ...
    
    if isinstance(value, bool):
        raise BooleanContextError(
            f"Cannot assign boolean value to variable '{name_token.value}'",
            line=name_token.line,
            column=name_token.column,
        )
    
    # ... остальной код присваивания ...
```

## Файл 3: Токены в grammar.lark

Добавить после существующих операторов:

```lark
// Comparison operators
COMP_OP: "==" | "!=" | "<" | "<=" | ">" | ">="

// Keywords
%import common.WS
%ignore WS
```

**Важно**: `"if"`, `"else"`, `"and"`, `"or"`, `"not"` — это зарезервированные слова (Keywords), которые Lark обрабатывает как встроенные строки в правилах.

## Таблица трансформации синтаксиса

| Старый синтаксис | Новый узел | Тип |
|---|---|---|
| `1 + 2` | sum → product → ... | numeric |
| `1 < 2` | comparison → sum → ... | **boolean** |
| `x if 1 < 2 else y` | conditional_expr | numeric |
| `1 < 2 and 3 < 4` | or_expr → and_expr → comparison | **boolean** |
| `not (x < 5)` | not_expr → comparison | **boolean** |

## Диаграмма парсинга примера

Для кода: `10 if x < 5 and y > 3 else 20`

```
conditional_expr
├── or_expr (evaluation of 10)
│   └── and_expr
│       └── not_expr
│           └── comparison
│               └── sum → ... → NUMBER(10)
├── "if"
├── or_expr (condition evaluation)
│   └── and_expr
│       ├── not_expr
│       │   └── comparison (x < 5)
│       │       ├── sum → NAME(x)
│       │       ├── COMP_OP(<)
│       │       └── sum → NUMBER(5)
│       ├── "and"
│       └── not_expr
│           └── comparison (y > 3)
│               ├── sum → NAME(y)
│               ├── COMP_OP(>)
│               └── sum → NUMBER(3)
├── "else"
└── conditional_expr
    └── or_expr
        └── ... → NUMBER(20)
```

## Проверочный лист для реализации

- [ ] Обновить `grammar.lark`: добавить новые правила для `conditional_expr`, `or_expr`, `and_expr`, `not_expr`, `comparison`
- [ ] Добавить класс `BooleanContextError`
- [ ] Реализовать 5 новых методов: `_eval_conditional_expr`, `_eval_or_expr`, `_eval_and_expr`, `_eval_not_expr`, `_eval_comparison`
- [ ] Обновить `_eval()` для обработки новых типов узлов
- [ ] Добавить проверки типов в арифметические операции
- [ ] Обновить `_eval_assignment()` для отклонения булевских значений
- [ ] Написать тесты (15+ тестов)
- [ ] Проверить обратную совместимость (старые тесты должны работать)
- [ ] Обновить README и примеры
- [ ] Обновить docstrings

---

**Статус**: Готово к реализации
