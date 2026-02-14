from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_FLOOR, ROUND_HALF_UP
import ast
import math
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from lark import Lark, Token, Tree


class DSLError(Exception):
    """Базовый класс исключений для ошибок интерпретатора DSL.
    
    Хранит сообщение об ошибке и опциональную позицию в исходном коде (строка и столбец).
    """
    
    def __init__(self, message: str, line: Optional[int] = None, column: Optional[int] = None) -> None:
        super().__init__(message)
        self.message = message
        self.line = line
        self.column = column

    def __str__(self) -> str:
        if self.line is None or self.column is None:
            return self.message
        return f"{self.message} (line {self.line}, column {self.column})"


class DivisionByZeroError(DSLError):
    """Исключение для ошибок деления на ноль или mod на ноль."""
    pass


class VariableNotFoundError(DSLError):
    """Исключение для обращения к неопределённой переменной."""
    pass


@dataclass(frozen=True)
class PowerValue:
    """Значение степени для оптимизации модульного возведения в степень.
    
    Хранит основание, показатель степени и вычисленное значение.
    Используется для оптимизации выражений вида a**b mod p через pow(a, b, p).
    """
    base: Decimal
    exponent: Decimal
    value: Decimal


class Interpreter:
    """Интерпретатор DSL для математических вычислений.
    
    Поддерживает:
    - Арифметику произвольной точности (Decimal)
    - Математические функции (sin, cos, ln, sqrt, nrt и др.)
    - Модульную арифметику с корректной семантикой для отрицательных чисел
    - Циклы for с шагом
    - Блоки как выражения
    - Управление точностью вычислений
    - Трассировку выполнения для отладки
    """
    
    def __init__(self, initial_env: Optional[Dict[str, Any]] = None, trace: bool = False) -> None:
        """Инициализация интерпретатора.
        
        Args:
            initial_env: Начальные значения переменных (словарь имя -> значение)
            trace: Включить режим трассировки для отладки выполнения
        """
        grammar_path = Path(__file__).with_name("grammar.lark")
        grammar_text = grammar_path.read_text(encoding="utf-8")
        self._parser = Lark(
            grammar_text,
            parser="earley",
            propagate_positions=True,
            maybe_placeholders=False,
        )
        self._precision = 10
        self._env = {
            "pi": self._round_value(Decimal(str(math.pi))),
            "e": self._round_value(Decimal(str(math.e))),
        }
        if initial_env:
            for name, value in initial_env.items():
                self._env[name] = value
        self._trace = trace
        self._source_lines: list[str] = []

    @property
    def precision(self) -> int:
        """Текущая точность вычислений (количество знаков после запятой)."""
        return self._precision

    def parse(self, text: str) -> Tree:
        """Разобрать исходный код в синтаксическое дерево.
        
        Args:
            text: Исходный код программы на DSL
            
        Returns:
            Синтаксическое дерево (Lark Tree)
        """
        return self._parser.parse(text)

    def execute(self, text: str) -> Any:
        """Выполнить программу на DSL.
        
        Args:
            text: Исходный код программы
            
        Returns:
            Результат последнего выражения или None
        """
        tree = self.parse(text)
        self._source_lines = text.splitlines()
        return self._eval(tree)

    def set_variable(self, name: str, value: Any) -> None:
        """Установить значение переменной в окружении.
        
        Args:
            name: Имя переменной
            value: Значение переменной
        """
        self._env[name] = value

    def format_value(self, value: Any) -> str:
        """Форматировать значение в строку с учётом текущей точности.
        
        Args:
            value: Значение для форматирования
            
        Returns:
            Строковое представление с нужным количеством знаков
        """
        return self._format_value(value)

    def _eval(self, node: Any) -> Any:
        """Вычислить узел синтаксического дерева.
        
        Args:
            node: Узел дерева (Tree, Token или примитивное значение)
            
        Returns:
            Результат вычисления узла
        """
        if isinstance(node, Tree):
            method = getattr(self, f"_eval_{node.data}", None)
            if method is None:
                raise DSLError(f"Unsupported syntax node: {node.data}")
            return method(node)
        if isinstance(node, Token):
            if node.type == "NUMBER":
                return self._to_decimal(node.value)
            if node.type == "NAME":
                return self._get_var(node)
            if node.type == "STRING":
                return ast.literal_eval(node.value)
            return node.value
        return node

    def _eval_start(self, node: Tree) -> Any:
        result = None
        for child in node.children:
            if isinstance(child, Token) and child.type == "SEP":
                continue
            if isinstance(child, Tree) and child.data in {"sep", "seps"}:
                continue
            # Trace top-level statements (when not already traced via _eval_statement)
            if self._trace and isinstance(child, Tree) and child.data == "statement":
                pass  # Will be traced in _eval_statement
            result = self._eval(child)
        return result

    def _eval_statement_list(self, node: Tree) -> Any:
        result = None
        for child in node.children:
            if isinstance(child, Token) and child.type == "SEP":
                continue
            if isinstance(child, Tree) and child.data == "sep":
                continue
            
            # Trace statement before execution
            if self._trace and isinstance(child, Tree):
                self._trace_statement(child)
            
            result = self._eval(child)
            
            # Trace statement output after execution
            if self._trace and isinstance(child, Tree):
                if child.data == "assignment":
                    # Check if assignment is for a for_expr (RHS is for loop)
                    rhs = child.children[2] if len(child.children) > 2 else None
                    is_for_assignment = isinstance(rhs, Tree) and rhs.data == "for_expr"
                    if not is_for_assignment:
                        # Regular assignment: print '+ var = value'
                        name = child.children[0].value
                        print(f"+ {name} = {self._format_value(self._env[name])}")
                    else:
                        # For-assignment: only print after the loop completes
                        name = child.children[0].value
                        print(f"+ {name} = {self._format_value(self._env[name])}")
                elif child.data not in {"print_call", "for_expr"}:
                    # Expression (not print, not for): print '+ value'
                    if result is not None:
                        print(f"+ {self._format_value(result)}")
        return result

    def _eval_statement(self, node: Tree) -> Any:
        child = node.children[0]
        result = self._eval(child)
        return result

    def _eval_assignment(self, node: Tree) -> None:
        """Выполнить присваивание: =, +=, -=, /=, mod=.
        
        Args:
            node: Узел присваивания
            
        Returns:
            None (присваивание не возвращает значение)
        """
        name_token = node.children[0]
        op_tree = node.children[1]
        value = self._eval(node.children[2])
        op = self._assign_op(op_tree)

        if op == "=":
            self._env[name_token.value] = value
            return None

        if name_token.value not in self._env:
            raise VariableNotFoundError(
                f"Variable not found: {name_token.value}",
                line=name_token.line,
                column=name_token.column,
            )

        current = self._env[name_token.value]
        if op == "+=":
            self._env[name_token.value] = self._round_value(self._to_decimal(current) + self._to_decimal(value))
        elif op == "-=":
            self._env[name_token.value] = self._round_value(self._to_decimal(current) - self._to_decimal(value))
        elif op == "/=":
            self._env[name_token.value] = self._div(self._to_decimal(current), self._to_decimal(value), node.meta)
        elif op == "mod=":
            self._env[name_token.value] = self._mod(self._to_decimal(current), self._to_decimal(value), node.meta)
        else:
            raise DSLError(f"Unsupported assignment operator: {op}", line=node.meta.line, column=node.meta.column)
        return None

    def _assign_op(self, node: Tree) -> str:
        token = node.children[0]
        return token.value

    def _eval_expr(self, node: Tree) -> Any:
        return self._eval(node.children[0])

    def _eval_for_expr(self, node: Tree) -> Any:
        """Выполнить цикл for с диапазоном и опциональным шагом.
        
        Семантика видимости переменной цикла:
        - Если переменная существовала до цикла, сохраняет последнее значение
        - Если цикл не выполнился, переменная сохраняет исходное значение
        - Если переменная новая, удаляется после цикла
        
        Args:
            node: Узел for-выражения
            
        Returns:
            Результат последнего выражения в последней итерации
        """
        name_token = node.children[0]
        start = self._to_decimal(self._eval(node.children[1]))
        end = self._to_decimal(self._eval(node.children[2]))
        block = node.children[-1]
        step = Decimal(1)
        if len(node.children) == 5:
            step = self._to_decimal(self._eval(node.children[3]))

        if step == 0:
            raise DSLError("Step cannot be zero", line=node.meta.line, column=node.meta.column)

        existed_before = name_token.value in self._env
        original_value = self._env.get(name_token.value)
        self._env[name_token.value] = self._round_value(start)

        last_result = None
        last_valid_value = None
        iterations = 0

        if step > 0:
            condition = lambda i: i <= end
        else:
            condition = lambda i: i >= end

        while condition(self._to_decimal(self._env[name_token.value])):
            # Trace loop iteration entry
            if self._trace and iterations == 0:
                # First iteration: print loop header with actual values
                source = self._get_source_line(node.meta.line)
                step_str = f" by {self._format_value(step)}" if len(node.children) == 5 else ""
                print(f"- {node.meta.line}: for {name_token.value} in {self._format_value(start)} .. {self._format_value(end)}{step_str}")
                print(f"+ {name_token.value} = {self._format_value(self._env[name_token.value])}")
            elif self._trace:
                # Subsequent iterations: just print updated loop variable
                print(f"+ {name_token.value} = {self._format_value(self._env[name_token.value])}")
            
            last_result = self._eval(block)
            iterations += 1
            last_valid_value = self._to_decimal(self._env[name_token.value])
            self._env[name_token.value] = self._round_value(self._to_decimal(self._env[name_token.value]) + step)

        if existed_before:
            if iterations == 0:
                self._env[name_token.value] = original_value
            else:
                self._env[name_token.value] = last_valid_value
        else:
            if name_token.value in self._env:
                del self._env[name_token.value]

        return last_result

    def _eval_block(self, node: Tree) -> Any:
        result = None
        for child in node.children:
            if isinstance(child, Token) and child.type == "SEP":
                continue
            if isinstance(child, Tree) and child.data in {"sep", "seps"}:
                continue
            if isinstance(child, Tree) and child.data == "statement_list":
                return self._eval_statement_list(child)
            result = self._eval(child)
        return result

    def _eval_print_call(self, node: Tree) -> None:
        """Выполнить вызов print() для вывода значений и строк.
        
        Args:
            node: Узел вызова print
            
        Returns:
            None
        """
        args = []
        if node.children:
            args = self._eval_print_args(node.children[0])
        printable = [self._format_value(arg) for arg in args]
        print(" ".join(printable))
        return None

    def _eval_print_args(self, node: Tree) -> Iterable[Any]:
        args = []
        for child in node.children:
            if isinstance(child, Tree) and child.data == "print_arg":
                args.append(self._eval_print_arg(child))
        return args

    def _eval_print_arg(self, node: Tree) -> Any:
        child = node.children[0]
        if isinstance(child, Token) and child.type == "STRING":
            return ast.literal_eval(child.value)
        return self._eval(child)

    def _eval_sum(self, node: Tree) -> Any:
        value = self._eval(node.children[0])
        idx = 1
        while idx < len(node.children):
            op_token = node.children[idx]
            right = self._eval(node.children[idx + 1])
            if op_token.value == "+":
                value = self._round_value(self._to_decimal(value) + self._to_decimal(right))
            else:
                value = self._round_value(self._to_decimal(value) - self._to_decimal(right))
            idx += 2
        return value

    def _eval_product(self, node: Tree) -> Any:
        left = self._eval(node.children[0])
        idx = 1
        while idx < len(node.children):
            op_token = node.children[idx]
            right = self._eval(node.children[idx + 1])
            if op_token.value == "*":
                left = self._round_value(self._to_decimal(self._unwrap_value(left)) * self._to_decimal(right))
            elif op_token.value == "/":
                left = self._div(self._to_decimal(self._unwrap_value(left)), self._to_decimal(right), node.meta)
            else:
                left = self._mod_op(left, right, node.meta)
            idx += 2
        return left

    def _mod_op(self, left: Any, right: Any, meta: Any) -> Any:
        """Вычислить модуль с оптимизацией для степени.
        
        Если левый операнд - PowerValue (результат a**b), использует
        оптимизированный pow(a, b, p) для модульной степени.
        
        Args:
            left: Левый операнд (может быть PowerValue)
            right: Модуль (правый операнд)
            meta: Метаданные узла для позиции ошибки
            
        Returns:
            Результат операции mod
        """
        if isinstance(left, PowerValue):
            base = left.base
            exp = left.exponent
            modulus = self._to_decimal(right)
            if self._is_int(base) and self._is_int(exp) and self._is_int(modulus):
                return self._mod_pow(base, exp, modulus, meta)
            return self._mod(left.value, self._to_decimal(right), meta)
        return self._mod(self._to_decimal(left), self._to_decimal(right), meta)

    def _eval_power(self, node: Tree) -> Any:
        base = self._to_decimal(self._eval(node.children[0]))
        if len(node.children) == 1:
            return base
        exponent = self._to_decimal(self._eval(node.children[2]))
        value = self._pow(base, exponent, node.meta)
        return PowerValue(base=base, exponent=exponent, value=value)

    def _eval_unary(self, node: Tree) -> Any:
        if len(node.children) == 1:
            return self._eval(node.children[0])
        op_token = node.children[0]
        value = self._to_decimal(self._eval(node.children[1]))
        if op_token.value == "+":
            return value
        return self._round_value(-value)

    def _eval_atom(self, node: Tree) -> Any:
        return self._eval(node.children[0])

    def _eval_number(self, node: Tree) -> Any:
        return self._to_decimal(node.children[0].value)

    def _eval_var(self, node: Tree) -> Any:
        return self._get_var(node.children[0])

    def _eval_func_call(self, node: Tree) -> Any:
        name_token = node.children[0]
        args = []
        if len(node.children) > 1:
            args = self._eval_arg_list(node.children[1])
        return self._call_function(name_token, args)

    def _eval_arg_list(self, node: Tree) -> Iterable[Any]:
        return [self._eval(child) for child in node.children]

    def _get_var(self, token: Token) -> Any:
        if token.value not in self._env:
            raise VariableNotFoundError(
                f"Variable not found: {token.value}",
                line=token.line,
                column=token.column,
            )
        return self._env[token.value]

    def _call_function(self, token: Token, args: Iterable[Any]) -> Any:
        """Вызвать встроенную функцию по имени.
        
        Поддерживаемые функции:
        - Управление точностью: set_precision, get_precision
        - Логарифмы: ln, log2, log10
        - Тригонометрия: sin, cos, tg, ctg
        - Корни: sqrt, nrt
        
        Args:
            token: Токен с именем функции
            args: Аргументы функции
            
        Returns:
            Результат вызова функции
        """
        name = token.value
        if name == "set_precision":
            return self._set_precision(args, token)
        if name == "get_precision":
            return self._round_value(Decimal(self._precision))

        if name == "ln":
            return self._apply_math_1(math.log, args, token)
        if name == "log2":
            return self._apply_math_1(math.log2, args, token)
        if name == "log10":
            return self._apply_math_1(math.log10, args, token)
        if name == "sin":
            return self._apply_math_1(math.sin, args, token)
        if name == "cos":
            return self._apply_math_1(math.cos, args, token)
        if name == "tg":
            return self._apply_math_1(math.tan, args, token)
        if name == "ctg":
            return self._apply_ctg(args, token)
        if name == "sqrt":
            return self._apply_sqrt(args, token)
        if name == "nrt":
            return self._apply_nrt(args, token)

        raise DSLError(f"Unknown function: {name}", line=token.line, column=token.column)

    def _set_precision(self, args: Iterable[Any], token: Token) -> Any:
        """Установить точность вычислений (количество знаков после запятой).
        
        Args:
            args: Список из одного аргумента - новая точность (целое >= 0)
            token: Токен для позиции ошибки
            
        Returns:
            Старое значение точности (до изменения)
        """
        args_list = list(args)
        if len(args_list) != 1:
            raise DSLError("set_precision expects 1 argument", line=token.line, column=token.column)
        value = self._to_decimal(args_list[0])
        if not self._is_int(value) or value < 0:
            raise DSLError("set_precision expects integer >= 0", line=token.line, column=token.column)
        old_precision = self._precision
        self._precision = int(value)
        return Decimal(old_precision)

    def _apply_math_1(self, func: Any, args: Iterable[Any], token: Token) -> Any:
        args_list = list(args)
        if len(args_list) != 1:
            raise DSLError(f"{token.value} expects 1 argument", line=token.line, column=token.column)
        value = float(self._to_decimal(args_list[0]))
        try:
            result = func(value)
        except ValueError as exc:
            raise DSLError(str(exc), line=token.line, column=token.column) from exc
        return self._round_value(Decimal(str(result)))

    def _apply_ctg(self, args: Iterable[Any], token: Token) -> Any:
        args_list = list(args)
        if len(args_list) != 1:
            raise DSLError("ctg expects 1 argument", line=token.line, column=token.column)
        value = float(self._to_decimal(args_list[0]))
        tan_value = math.tan(value)
        if tan_value == 0:
            raise DivisionByZeroError("ctg division by zero", line=token.line, column=token.column)
        return self._round_value(Decimal(str(1 / tan_value)))

    def _apply_sqrt(self, args: Iterable[Any], token: Token) -> Any:
        args_list = list(args)
        if len(args_list) != 1:
            raise DSLError("sqrt expects 1 argument", line=token.line, column=token.column)
        value = self._to_decimal(args_list[0])
        if value < 0:
            raise DSLError("sqrt domain error", line=token.line, column=token.column)
        return self._round_value(Decimal(str(math.sqrt(float(value)))))

    def _apply_nrt(self, args: Iterable[Any], token: Token) -> Any:
        args_list = list(args)
        if len(args_list) != 2:
            raise DSLError("nrt expects 2 arguments", line=token.line, column=token.column)
        x = self._to_decimal(args_list[0])
        n = self._to_decimal(args_list[1])
        if n == 0:
            raise DivisionByZeroError("nrt division by zero", line=token.line, column=token.column)
        if self._is_int(n) and int(n) % 2 == 0 and x < 0:
            raise DSLError("nrt domain error", line=token.line, column=token.column)
        result = Decimal(str(float(x) ** (1.0 / float(n))))
        return self._round_value(result)

    def _pow(self, base: Decimal, exponent: Decimal, meta: Any) -> Decimal:
        if self._is_int(exponent):
            try:
                return self._round_value(base ** int(exponent))
            except (OverflowError, ValueError) as exc:
                raise DSLError(str(exc), line=meta.line, column=meta.column) from exc
        result = Decimal(str(float(base) ** float(exponent)))
        return self._round_value(result)

    def _mod_pow(self, base: Decimal, exponent: Decimal, modulus: Decimal, meta: Any) -> Decimal:
        if modulus == 0:
            raise DivisionByZeroError("mod division by zero", line=meta.line, column=meta.column)
        return self._round_value(Decimal(pow(int(base), int(exponent), int(abs(modulus)))))

    def _div(self, left: Decimal, right: Decimal, meta: Any) -> Decimal:
        if right == 0:
            raise DivisionByZeroError("division by zero", line=meta.line, column=meta.column)
        return self._round_value(left / right)

    def _mod(self, left: Decimal, right: Decimal, meta: Any) -> Decimal:
        """Вычислить модуль с математической семантикой (неотрицательный остаток).
        
        Формула: result = left - floor(left / |right|) * |right|
        Результат всегда в диапазоне [0, |right|)
        
        Примеры:
            -5 mod 3 = 1 (не -2)
            5 mod -3 = 2
        
        Args:
            left: Делимое
            right: Делитель (модуль)
            meta: Метаданные для позиции ошибки
            
        Returns:
            Неотрицательный остаток от деления
        """
        if right == 0:
            raise DivisionByZeroError("mod division by zero", line=meta.line, column=meta.column)
        modulus = abs(right)
        quotient = (left / modulus).to_integral_value(rounding=ROUND_FLOOR)
        result = left - (quotient * modulus)
        return self._round_value(result)

    def _to_decimal(self, value: Any) -> Decimal:
        """Преобразовать значение в Decimal.
        
        Args:
            value: Значение для преобразования (Decimal, int, float, str)
            
        Returns:
            Значение типа Decimal
            
        Raises:
            DSLError: Если тип значения не поддерживается
        """
        if isinstance(value, Decimal):
            return value
        if isinstance(value, (int, float)):
            return Decimal(str(value))
        if isinstance(value, str):
            return Decimal(value)
        raise DSLError(f"Expected numeric value, got {type(value).__name__}")

    def _is_int(self, value: Decimal) -> bool:
        """Проверить, является ли Decimal целым числом."""
        return value == value.to_integral_value()

    def _round_value(self, value: Decimal) -> Decimal:
        """Округлить значение до текущей точности.
        
        Использует ROUND_HALF_UP (математическое округление).
        
        Args:
            value: Значение для округления
            
        Returns:
            Округлённое значение
        """
        quant = Decimal(1).scaleb(-self._precision)
        return value.quantize(quant, rounding=ROUND_HALF_UP)

    def _format_value(self, value: Any) -> str:
        """Форматировать значение в строку с текущей точностью.
        
        При точности 0 форматирует как целое число без точки.
        
        Args:
            value: Значение для форматирования
            
        Returns:
            Строковое представление
        """
        if isinstance(value, Decimal):
            quant = Decimal(1).scaleb(-self._precision)
            fixed = value.quantize(quant, rounding=ROUND_HALF_UP)
            return format(fixed, f".{self._precision}f")
        return str(value)

    def _unwrap_value(self, value: Any) -> Decimal:
        if isinstance(value, PowerValue):
            return value.value
        return self._to_decimal(value)
    
    def _get_source_line(self, line_num: int) -> str:
        """Получить строку исходного кода по номеру (нумерация с 1).
        
        Args:
            line_num: Номер строки (1-based)
            
        Returns:
            Текст строки без лишних пробелов или пустая строка
        """
        if 1 <= line_num <= len(self._source_lines):
            return self._source_lines[line_num - 1].strip()
        return ""
    
    def _trace_statement(self, node: Tree, prefix: str = "-") -> None:
        """Напечатать трассировочную строку для отладки.
        
        Формат: '- номер_строки: текст_инструкции'
        Работает только если режим трассировки включён.
        
        Args:
            node: Узел дерева для трассировки
            prefix: Префикс строки трассировки (по умолчанию '-')
        """
        if not self._trace:
            return
        if hasattr(node, "meta") and node.meta.line:
            source = self._get_source_line(node.meta.line)
            print(f"{prefix} {node.meta.line}: {source}")

