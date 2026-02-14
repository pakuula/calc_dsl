# Диаграмма приоритетов операторов

## Визуальное представление иерархии

```
                    LOWEST PRIORITY
                          ↑
                          |
┌──────────────────────────────────────────┐
│  9️⃣ Conditional (if-else)                │
│     form: A if B else C                  │
│     RIGHT-ASSOCIATIVE                    │
│     Result: Decimal (NOT boolean)        │
└──────────────────────────────────────────┘
                          ↑
                          |
┌──────────────────────────────────────────┐
│  8️⃣ Logical OR                           │
│     A or B or C                          │
│     LEFT-ASSOCIATIVE, SHORT-CIRCUIT      │
│     Result: boolean                      │
└──────────────────────────────────────────┘
                          ↑
                          |
┌──────────────────────────────────────────┐
│  7️⃣ Logical AND                          │
│     A and B and C                        │
│     LEFT-ASSOCIATIVE, SHORT-CIRCUIT      │
│     Result: boolean                      │
└──────────────────────────────────────────┘
                          ↑
                          |
┌──────────────────────────────────────────┐
│  6️⃣ Logical NOT                          │
│     not A                                │
│     PREFIX OPERATOR                      │
│     Result: boolean                      │
└──────────────────────────────────────────┘
                          ↑
                          |
┌──────────────────────────────────────────┐
│  5️⃣ Comparison                           │
│     ==, !=, <, <=, >, >=                │
│     CHAINING: 1 < x < 10 → (1<x)∧(x<10)│
│     Result: boolean                      │
└──────────────────────────────────────────┘
                          ↑
                          |
┌──────────────────────────────────────────┐
│  4️⃣ Addition/Subtraction                 │
│     +, -                                 │
│     LEFT-ASSOCIATIVE                     │
│     Result: Decimal                      │
└──────────────────────────────────────────┘
                          ↑
                          |
┌──────────────────────────────────────────┐
│  3️⃣ Multiplication/Division/Modulo       │
│     *, /, mod                            │
│     LEFT-ASSOCIATIVE                     │
│     Result: Decimal                      │
└──────────────────────────────────────────┘
                          ↑
                          |
┌──────────────────────────────────────────┐
│  2️⃣ Power (Exponentiation)               │
│     **                                   │
│     RIGHT-ASSOCIATIVE                    │
│     Result: Decimal                      │
└──────────────────────────────────────────┘
                          ↑
                          |
┌──────────────────────────────────────────┐
│  1️⃣ Unary +/- and function calls         │
│     -x, +x, sin(x), sqrt(x)              │
│     PREFIX OPERATORS                     │
│     Result: Decimal                      │
└──────────────────────────────────────────┘
                          ↑
                          |
                    HIGHEST PRIORITY
```

## Примеры парсинга с приоритетами

### Пример 1: `1 + 2 < 3 and 4 > 0`

```
Разбор слева направо:
1. 1 + 2              → sum: 3
2. 3 < 3              → comparison: false
3. 4 > 0              → comparison: true
4. false and true     → and_expr: false

Результат: false
```

### Пример 2: `not x < 5 or y == 10`

```
Лево-право: not (x < 5) or (y == 10)
            
1. x < 5              → comparison: boolean
2. not (...)          → not_expr: boolean
3. y == 10            → comparison: boolean
4. (...) or (...)     → or_expr: boolean

Результат: boolean
```

### Пример 3: `10 if x > 5 and y < 20 else x * 2`

```
1. x > 5              → comparison: boolean
2. y < 20             → comparison: boolean
3. boolean and boolean → and_expr: boolean
4. 10 if (...) else x*2 → conditional_expr: Decimal

Результат: Decimal
```

### Пример 4: `2 ** 3 - 1`

```
1. 2 ** 3             → power: 8
2. 8 - 1              → sum: 7

Результат: 7
```

### Пример 5: `-x + 2 * 3`

```
1. -x                 → unary: -x
2. 2 * 3              → product: 6
3. (-x) + 6           → sum: -x + 6

Результат: Decimal
```

## Правила вывода типов

```
TYPE(sum)                   = Decimal
TYPE(product)               = Decimal
TYPE(power)                 = Decimal
TYPE(unary)                 = Decimal
TYPE(atom)                  = Decimal | bool  ❌ ОШИБКА если bool

TYPE(comparison)            = boolean
TYPE(not_expr)              = boolean
TYPE(and_expr)              = boolean
TYPE(or_expr)               = boolean

TYPE(conditional_expr)      = Decimal  (никогда не boolean!)
  • Условие: boolean
  • Then-ветка: Decimal
  • Else-ветка: Decimal
```

## Ошибки типизации

| Выражение | Результат |
|-----------|-----------|
| `x = (1 < 2)` | ❌ Cannot assign boolean |
| `(1 < 2) + 5` | ❌ Boolean in arithmetic |
| `print(1 < 2)` | ❌ Boolean not allowed here (может быть нужно проверить print) |
| `10 if 1 < 2 else 20` | ✅ Decimal |
| `1 < 2 and 3 < 4` | ✅ Decimal (в условии) |

---

**Примечание**: В текущем дизайне булевские значения допустимы ТОЛЬКО в условных выражениях (в `if-else` условиях и логических операциях). Нельзя передавать их куда-либо еще.
