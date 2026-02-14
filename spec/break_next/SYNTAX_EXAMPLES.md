# Примеры синтаксиса и семантики условных выражений

## 1. Основные условные выражения

### Простой if-else

```clc
# Пример 1: Выбор значения
result = 10 if 5 < 10 else 20
# result = 10.0000000000

# Пример 2: С переменными
x = 7
y = x * 2 if x > 5 else x
# y = 14.0000000000

# Пример 3: Условие в параметре
max_val = 100 if 50 > 30 else 50
# max_val = 100.0000000000
```

### Вложенные if-else

```clc
# Вложенные условия: оценка
score = 85
grade = 5 if score >= 90 else (
    4 if score >= 80 else (
    3 if score >= 70 else 2
    )
)
# grade = 4.0000000000

# Альтернативно (более читаемо):
grade_alt = 
    5 if score >= 90 else
    4 if score >= 80 else
    3 if score >= 70 else
    2
# grade_alt = 4.0000000000
```

### if-else в циклах

```clc
# Условие в теле цикла
sum = 0
for i in 1 .. 10 (
    sum += i if i mod 2 == 0 else 0
)
# sum = 30.0000000000 (2+4+6+8+10)

# Условие в диапазоне (работает!)
for i in 1 .. (5 if 1 < 10 else 3) (
    print(i)
)
# Выведет: 1.0000000000  2.0000000000  3.0000000000  4.0000000000  5.0000000000
```

## 2. Операторы сравнения

### Простые сравнения

```clc
x = 5
y = 10

# Все работают в условиях
a = 100 if x < y else 0        # x < y = true, a = 100
b = 100 if x <= y else 0       # x <= y = true, b = 100
c = 100 if x > y else 0        # x > y = false, c = 0
d = 100 if x >= y else 0       # x >= y = false, d = 0
e = 100 if x == 5 else 0       # x == 5 = true, e = 100
f = 100 if x != y else 0       # x != y = true, f = 100
```

### Сравнение выражений

```clc
# Сравнение арифметических выражений
result = 10 if 2 * 3 + 1 < 10 else 20
# 2*3+1 = 7, 7 < 10 = true, result = 10.0000000000

# Сравнение с функциями
n = 4
is_small = 1 if sqrt(n) < 3 else 0
# sqrt(4) = 2, 2 < 3 = true, is_small = 1.0000000000
```

### Цепочки сравнений

```clc
x = 5
# 1 < x < 10  →  (1 < x) and (x < 10)  →  true and true  →  true
in_range = 100 if 1 < x and x < 10 else -1
# in_range = 100.0000000000

# Более сложная цепочка
n = 15
# 10 <= n <= 20
valid = 1 if 10 <= n and n <= 20 else 0
# valid = 1.0000000000
```

## 3. Логические операторы

### and (логическое И)

```clc
# Распределение по возрастным группам
age = 25

student = 100 if age >= 18 and age < 65 else 0
# true and true → 100
# student = 100.0000000000

# Несколько условий
x = 10
y = 5
z = 3
valid = 1 if x > y and y > z and z > 0 else 0
# true and true and true → 1
# valid = 1.0000000000
```

### or (логическое ИЛИ)

```clc
# Выходные дни и праздники
day = "Saturday"  # ⚠️ Строки не поддерживаются! Только для примера

# Надо работать с числами:
day_num = 6  # 6 = Saturday, 7 = Sunday, 1 = Monday
is_day_off = 100 if day_num == 6 or day_num == 7 else 0
# true or true → true
# is_day_off = 100.0000000000

# ИЛИ с тремя условиями
error_code = 0
action = 1 if error_code == 404 or error_code == 500 or error_code == 503 else 0
# true or true or true → 1
# action = 1.0000000000
```

### not (логическое НЕ)

```clc
# Инверсия условия
x = 5
y = 10

is_not_equal = 100 if not (x == y) else 0
# not (5 == 10) → not false → true
# is_not_equal = 100.0000000000

# not в выражении
is_not_small = 1 if not (x < 0) else 0
# not (5 < 0) → not false → true
# is_not_small = 1.0000000000

# Приоритет: not x < 5  →  not (x < 5)
x = 3
result = 100 if not x < 5 else -100
# not (3 < 5) → not true → false
# result = -100.0000000000
```

## 4. Комбинированные выражения

### Комбинирование and/or/not

```clc
x = 10
y = 5
z = 15

# (x > y) and (z > x)
cond1 = 1 if x > y and z > x else 0
# (10 > 5) and (15 > 10) → true and true → true
# cond1 = 1.0000000000

# (x < y) or (z > 10)
cond2 = 1 if x < y or z > 10 else 0
# (10 < 5) or (15 > 10) → false or true → true
# cond2 = 1.0000000000

# not ((x < 5) or (y > 20))
cond3 = 1 if not (x < 5 or y > 20) else 0
# not (false or false) → not false → true
# cond3 = 1.0000000000

# Сложное: (x > 0 and x < 20) or (z > 100)
cond4 = 1 if (x > 0 and x < 20) or z > 100 else 0
# (true and true) or false → true or false → true
# cond4 = 1.0000000000
```

### Вложенные условия + логика

```clc
# Категория риска по возрасту и здоровью
age = 45
risk = 2  # 0=низкий, 1=средний, 2=высокий

category = 
    "HIGH_RISK" if age > 60 and risk >= 2 else
    "MEDIUM_RISK" if age > 60 or risk >= 1 else
    "LOW_RISK"

# ⚠️ Строковые значения не поддерживаются!
# Правильно с числами:

category = 
    3 if age > 60 and risk >= 2 else
    2 if age > 60 or risk >= 1 else
    1
# true and true → 3
# category = 3.0000000000
```

## 5. Ошибки и граничные случаи

### ❌ Ошибка 1: Присваивание boolean переменной

```clc
x = (1 < 2)
# ❌ ERROR: Cannot assign boolean value to variable 'x'
```

### ❌ Ошибка 2: Использование boolean в арифметике

```clc
y = (1 < 2) + 5
# ❌ ERROR: Boolean value cannot be used in arithmetic operation
```

### ❌ Ошибка 3: Условие не boolean

```clc
z = 10 if 5 else 20
# ❌ ERROR: Condition in if-else must be boolean
```

### ✅ Правильно: Условие должно быть boolean

```clc
# Правильно: сравнение возвращает boolean
result = 10 if 5 < 10 else 20
# ✅ result = 10.0000000000

# Правильно: логическое выражение
result2 = 10 if (5 < 10) and (3 > 1) else 20
# ✅ result2 = 10.0000000000
```

### ✅ Правильно: Булево значение только в условиях

```clc
# В условном выражении - ОК
x = 5 if (true_condition) else 10

# В логических операциях - ОК
result = a and b and c where a, b, c = boolean

# В print - ОК (если это внутри условия)
print(10 if condition else 20)
```

## 6. Практические примеры

### Пример 1: Расчет налога

```clc
# Налог: 10% если доход > 10000, иначе 5%
income = 15000
tax_rate = 0.1 if income > 10000 else 0.05
tax = income * tax_rate
# tax_rate = 0.1000000000
# tax = 1500.0000000000
```

### Пример 2: Квадратный корень с проверкой

```clc
# sqrt(x) если x >= 0, иначе 0
x = 16
result = sqrt(x) if x >= 0 else 0
# result = 4.0000000000

x = -9
result = sqrt(x) if x >= 0 else 0
# ✅ result = 0.0000000000 (не ошибка!)
```

### Пример 3: Факториал (цикл + условие)

```clc
# Вычислить 5! = 120
n = 5
fact = 1
for i in 1 .. n (
    fact *= i
)
# fact = 120.0000000000

# Условно: вычислить n! если n >= 0, иначе вернуть -1
n = 5
fact = 1 if n >= 0 else -1
for i in 1 .. n (
    fact *= i if n >= 0 else 1  # Защита от отрицательных
)
# fact = 120.0000000000
```

### Пример 4: Алгоритм Евклида с условиями

```clc
# GCD двух чисел
a = 48
b = 18

# Обмен если a < b
tmp = a
a = b if b > a else a
b = tmp if tmp > a else b

# Теперь a >= b
gcd = a
remainder = a mod b

while remainder != 0 (
    a = b
    b = remainder
    remainder = a mod b
)
# ⚠️ while не существует! Нужен for или рекурсия
```

### Пример 5: Скидка по количеству

```clc
# Скидка: 0% < 10 шт, 5% ≥ 10 шт, 10% ≥ 100 шт
quantity = 50
unit_price = 100

discount = 0.0 if quantity < 10 else (
    0.05 if quantity < 100 else 0.1
)

total_price = quantity * unit_price
final_price = total_price * (1 - discount)
# discount = 0.0500000000
# final_price = 4750.0000000000
```

## 7. Таблица тестовых выражений

| Выражение | Ожидаемый результат | Примечание |
|-----------|---|---|
| `5 if 1 < 2 else 10` | 5.0 | ✅ базовый |
| `5 if 1 > 2 else 10` | 10.0 | ✅ else-ветка |
| `5 if 1 == 1 else 10` | 5.0 | ✅ == |
| `5 if 1 != 2 else 10` | 5.0 | ✅ != |
| `5 if 1 <= 2 else 10` | 5.0 | ✅ <= |
| `5 if 1 >= 2 else 10` | 10.0 | ✅ >= |
| `5 if 1 < 2 and 3 < 4 else 10` | 5.0 | ✅ and |
| `5 if 1 < 2 or 3 > 4 else 10` | 5.0 | ✅ or |
| `5 if not (1 > 2) else 10` | 5.0 | ✅ not |
| `x = 1 < 2` | ERROR | ❌ no boolean assign |
| `y = (1 < 2) + 5` | ERROR | ❌ no boolean arithmetic |

---

**Статус**: Примеры и тесты готовы
