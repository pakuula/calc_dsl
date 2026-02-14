# Примеры кода DSL

## Простая арифметика и mod

x = 10
print("x =", x)
print("2 + 2 *2 =", 2 + 2* 2)
print("2 **3 mod 5 =", 2** 3 mod 5)

## Функции и константы

print("pi =", pi)
print("e =", e)
print("sin(pi/2) =", sin(pi / 2))
print("ln(e) =", ln(e))
print("nrt(27, 3) =", nrt(27, 3))

## Управление точностью

print("precision =", get_precision())
set_precision(5)
print("precision =", get_precision())
print("1/3 =", 1 / 3)

## Блок как выражение

x = (a = 2; b = 3; a * b)
print("block result =", x)

## Fibonacci через цикл

# F(n) при n >= 0

n = 10

# F(0)=0, F(1)=1

prev = 0
curr = 1

fib = for i in 2..n (
    next = prev + curr
    prev = curr
    curr = next
    curr
)
print("F(", n, ") =", fib)

## Сумма ряда 1..N

n = 5
sum = 0
for i in 1..n (sum += i)
print("sum =", sum)
