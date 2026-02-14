"""Интерпретатор DSL для математических вычислений."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_FLOOR, ROUND_HALF_UP, getcontext
import ast
import math
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from lark import Lark, Token, Tree


class DSLError(Exception):
    """Базовый класс исключений для ошибок интерпретатора DSL.

    Хранит сообщение об ошибке и опциональную позицию в исходном коде (строка и столбец).
    """

    def __init__(
        self, message: str, line: Optional[int] = None, column: Optional[int] = None
    ) -> None:
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

    pass  # pylint: disable=unnecessary-pass


class VariableNotFoundError(DSLError):
    """Исключение для обращения к неопределённой переменной."""

    pass  # pylint: disable=unnecessary-pass


class BooleanError(DSLError):
    """Исключение для попытки использовать булевское значение в неправильном контексте."""

    pass  # pylint: disable=unnecessary-pass


class BreakException(Exception):
    """Исключение для выхода из цикла через break."""

    def __init__(self, loop_var: str, result: Any) -> None:
        self.loop_var = loop_var
        self.result = result
        super().__init__(f"break from {loop_var}")


class NextException(Exception):
    """Исключение для перехода на следующую итерацию."""

    def __init__(self, loop_var: str) -> None:
        self.loop_var = loop_var
        super().__init__(f"next {loop_var}")


class BreakOutsideLoopError(DSLError):
    """Break используется вне цикла."""

    pass  # pylint: disable=unnecessary-pass


class NextOutsideLoopError(DSLError):
    """Next используется вне цикла."""

    pass  # pylint: disable=unnecessary-pass


class DuplicateLoopVariableError(DSLError):
    """Переменная цикла уже используется."""

    pass  # pylint: disable=unnecessary-pass


class LoopNotFoundError(DSLError):
    """Цикл по переменной не найден."""

    pass  # pylint: disable=unnecessary-pass


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

    def __init__(
        self, initial_env: Optional[Dict[str, Any]] = None, trace: bool = False
    ) -> None:
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
        self._loop_stack: list[str] = []  # стек активных переменных циклов

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
            return method(node)  # pylint: disable=not-callable
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
                        name_tok = child.children[0]
                        assert isinstance(name_tok, Token)
                        print(
                            f"+ {name_tok.value} = {self._format_value(self._env[name_tok.value])}"
                        )
                    else:
                        # For-assignment: only print after the loop completes
                        name_tok = child.children[0]
                        assert isinstance(name_tok, Token)
                        print(
                            f"+ {name_tok.value} = {self._format_value(self._env[name_tok.value])}"
                        )
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
        assert isinstance(name_token, Token)
        op_tree = node.children[1]
        assert isinstance(op_tree, Tree)
        value = self._eval(node.children[2])
        op = self._assign_op(op_tree)

        # Проверить, что значение не булевское
        if isinstance(value, bool):
            raise BooleanError(
                f"Cannot assign boolean value to variable {name_token.value}",
                line=name_token.line,
                column=name_token.column,
            )

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
            self._env[name_token.value] = self._round_value(
                self._ensure_numeric(current, "compound assignment") + 
                self._ensure_numeric(value, "compound assignment")
            )
        elif op == "-=":
            self._env[name_token.value] = self._round_value(
                self._ensure_numeric(current, "compound assignment") - 
                self._ensure_numeric(value, "compound assignment")
            )
        elif op == "/=":
            self._env[name_token.value] = self._div(
                self._ensure_numeric(current, "compound assignment"), 
                self._ensure_numeric(value, "compound assignment"), 
                node.meta
            )
        elif op == "mod=":
            self._env[name_token.value] = self._mod(
                self._ensure_numeric(current, "compound assignment"), 
                self._ensure_numeric(value, "compound assignment"), 
                node.meta
            )
        else:
            raise DSLError(
                f"Unsupported assignment operator: {op}",
                line=node.meta.line,
                column=node.meta.column,
            )
        return None

    def _assign_op(self, node: Tree) -> str:
        token = node.children[0]
        assert isinstance(token, Token)
        return token.value

    def _eval_expr(self, node: Tree) -> Any:
        return self._eval(node.children[0])

    def _enter_loop(self, var: str, meta: Any) -> None:
        """Вход в цикл с переменной var.

        Args:
            var: Имя переменной цикла
            meta: Метаданные узла для позиции ошибки

        Raises:
            DuplicateLoopVariableError: Если переменная уже используется в активном цикле
        """
        if var in self._loop_stack:
            raise DuplicateLoopVariableError(
                f"Loop variable '{var}' is already in use",
                line=meta.line,
                column=meta.column,
            )
        self._loop_stack.append(var)

    def _exit_loop(self, var: str) -> None:
        """Выход из цикла.

        Args:
            var: Имя переменной цикла
        """
        if self._loop_stack and self._loop_stack[-1] == var:
            self._loop_stack.pop()

    def _eval_break_stmt(self, node: Tree) -> None:
        """Обработка break конструкции.

        Args:
            node: Узел break_stmt

        Raises:
            BreakOutsideLoopError: Если break используется вне цикла
            LoopNotFoundError: Если указанный цикл не найден
            BreakException: Для выхода из цикла
        """
        if not self._loop_stack:
            raise BreakOutsideLoopError(
                "break statement used outside loop",
                line=node.meta.line,
                column=node.meta.column,
            )

        # Получить переменную цикла для выхода (по умолчанию - ближайший)
        loop_var = None
        from_clause_nodes = list(node.find_data("from_clause"))
        if from_clause_nodes:
            from_clause = from_clause_nodes[0]
            name_token = from_clause.children[0]
            assert isinstance(name_token, Token)
            loop_var = name_token.value
        else:
            loop_var = self._loop_stack[-1]  # ближайший цикл

        # Проверить, что цикл существует
        if loop_var not in self._loop_stack:
            raise LoopNotFoundError(
                f"Loop with variable '{loop_var}' not found",
                line=node.meta.line,
                column=node.meta.column,
            )

        # Получить условие (опционально)
        when_clause_nodes = list(node.find_data("when_clause"))
        if when_clause_nodes:
            when_clause = when_clause_nodes[0]
            condition = self._eval(when_clause.children[0])
            if not condition:
                return None  # условие ложно, break не выполняется

        # Вычислить результат (последний child - это expr после with)
        result = self._eval(node.children[-1])

        # Выбросить исключение
        raise BreakException(loop_var, result)

    def _eval_next_stmt(self, node: Tree) -> None:
        """Обработка next конструкции.

        Args:
            node: Узел next_stmt

        Raises:
            NextOutsideLoopError: Если next используется вне цикла
            LoopNotFoundError: Если указанный цикл не найден
            NextException: Для перехода на следующую итерацию
        """
        if not self._loop_stack:
            raise NextOutsideLoopError(
                "next statement used outside loop",
                line=node.meta.line,
                column=node.meta.column,
            )

        # Получить переменную цикла (по умолчанию - ближайший)
        loop_var = None
        loop_var_nodes = list(node.find_data("loop_var"))
        if loop_var_nodes:
            loop_var_node = loop_var_nodes[0]
            name_token = loop_var_node.children[0]
            assert isinstance(name_token, Token)
            loop_var = name_token.value
        else:
            loop_var = self._loop_stack[-1]  # ближайший цикл

        # Проверить, что цикл существует
        if loop_var not in self._loop_stack:
            raise LoopNotFoundError(
                f"Loop with variable '{loop_var}' not found",
                line=node.meta.line,
                column=node.meta.column,
            )

        # Получить условие (опционально)
        when_clause_nodes = list(node.find_data("when_clause"))
        if when_clause_nodes:
            when_clause = when_clause_nodes[0]
            condition = self._eval(when_clause.children[0])
            if not condition:
                return None  # условие ложно, next не выполняется

        # Выбросить исключение
        raise NextException(loop_var)

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
        assert isinstance(name_token, Token)
        var_name = name_token.value
        
        # Вход в цикл (проверка на дубликаты переменных)
        self._enter_loop(var_name, node.meta)
        
        try:
            start = self._ensure_numeric(self._eval(node.children[1]), "for loop start")
            end = self._ensure_numeric(self._eval(node.children[2]), "for loop end")
            block = node.children[-1]
            step = Decimal(1)
            if len(node.children) == 5:
                step = self._ensure_numeric(self._eval(node.children[3]), "for loop step")

            if step == 0:
                raise DSLError(
                    "Step cannot be zero", line=node.meta.line, column=node.meta.column
                )

            existed_before = var_name in self._env
            original_value: Any = self._env.get(var_name)
            self._env[var_name] = self._round_value(start)

            last_result = None
            last_valid_value: Optional[Decimal] = None
            iterations = 0

            if step > 0:
                condition = lambda i: i <= end # pylint: disable=unnecessary-lambda-assignment
            else:
                condition = lambda i: i >= end # pylint: disable=unnecessary-lambda-assignment

            while condition(self._to_decimal(self._env[var_name])):
                # Trace loop iteration entry
                if self._trace and iterations == 0:
                    # First iteration: print loop header with actual values
                    source = self._get_source_line(node.meta.line)
                    step_str = (
                        f" by {self._format_value(step)}" if len(node.children) == 5 else ""
                    )
                    print(
                        f"- {node.meta.line}: for {var_name} in "
                        f"{self._format_value(start)} .. {self._format_value(end)}{step_str}"
                    )
                    print(
                        f"+ {var_name} = {self._format_value(self._env[var_name])}"
                    )
                elif self._trace:
                    # Subsequent iterations: just print updated loop variable
                    print(
                        f"+ {var_name} = {self._format_value(self._env[var_name])}"
                    )

                try:
                    # Выполнить тело цикла
                    last_result = self._eval(block)
                    iterations += 1
                    last_valid_value = self._to_decimal(self._env[var_name])
                    
                except NextException as ne:
                    # Проверить, что это next для нашего цикла
                    if ne.loop_var == var_name:
                        # Next для текущего цикла - переходим к следующей итерации
                        iterations += 1
                        last_valid_value = self._to_decimal(self._env[var_name])
                        # Продолжаем выполнение (обновляем переменную цикла ниже)
                    else:
                        # Next для внешнего цикла - пробрасываем исключение дальше
                        raise
                
                except BreakException as be:
                    # Проверить, что это break для нашего цикла
                    if be.loop_var == var_name:
                        # Break для текущего цикла - выходим с результатом
                        last_result = be.result
                        iterations += 1
                        last_valid_value = self._to_decimal(self._env[var_name])
                        break
                    else:
                        # Break для внешнего цикла - пробрасываем исключение дальше
                        raise
                
                # Обновить переменную цикла для следующей итерации
                self._env[var_name] = self._round_value(
                    self._to_decimal(self._env[var_name]) + step
                )

            # Восстановить или удалить переменную цикла согласно семантике
            if existed_before:
                if iterations == 0:
                    self._env[var_name] = original_value
                else:
                    assert last_valid_value is not None
                    self._env[var_name] = last_valid_value
            else:
                if var_name in self._env:
                    del self._env[var_name]

            return last_result
        
        finally:
            # Выход из цикла
            self._exit_loop(var_name)

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
        args: list[Any] = []
        if node.children:
            print_args_node = node.children[0]
            assert isinstance(print_args_node, Tree)
            args = list(self._eval_print_args(print_args_node))
        printable = [self._format_value(arg) for arg in args]
        print(" ".join(printable))
        return None

    def _eval_print_args(self, node: Tree) -> Iterable[Any]:
        args: list[Any] = []
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
        value = self._ensure_numeric(value, "arithmetic operation (sum)")
        idx = 1
        while idx < len(node.children):
            op_token = node.children[idx]
            assert isinstance(op_token, Token)
            right = self._eval(node.children[idx + 1])
            right = self._ensure_numeric(right, "arithmetic operation (sum)")
            if op_token.value == "+":
                value = self._round_value(value + right)
            else:
                value = self._round_value(value - right)
            idx += 2
        return value

    def _eval_product(self, node: Tree) -> Any:
        left = self._eval(node.children[0])
        left = self._ensure_numeric(self._unwrap_value(left), "arithmetic operation (product)")
        idx = 1
        while idx < len(node.children):
            op_token = node.children[idx]
            assert isinstance(op_token, Token)
            right = self._eval(node.children[idx + 1])
            right = self._ensure_numeric(right, "arithmetic operation (product)")
            if op_token.value == "*":
                left = self._round_value(left * right)
            elif op_token.value == "/":
                left = self._div(left, right, node.meta)
            else:
                left = self._mod(left, right, node.meta)
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
        base = self._eval(node.children[0])
        base = self._ensure_numeric(base, "power operation (base)")
        if len(node.children) == 1:
            return base
        exponent = self._eval(node.children[2])
        exponent = self._ensure_numeric(exponent, "power operation (exponent)")
        value = self._pow(base, exponent, node.meta)
        return PowerValue(base=base, exponent=exponent, value=value)

    def _eval_unary(self, node: Tree) -> Any:
        if len(node.children) == 1:
            return self._eval(node.children[0])
        op_token = node.children[0]
        assert isinstance(op_token, Token)
        value = self._eval(node.children[1])
        value = self._ensure_numeric(value, "unary operation")
        if op_token.value == "+":
            return value
        return self._round_value(-value)

    def _eval_atom(self, node: Tree) -> Any:
        return self._eval(node.children[0])

    def _eval_number(self, node: Tree) -> Any:
        token = node.children[0]
        assert isinstance(token, Token)
        value = self._to_decimal(token.value)
        # Apply current precision to the number
        return self._round_value(value)

    def _eval_var(self, node: Tree) -> Any:
        token = node.children[0]
        assert isinstance(token, Token)
        return self._get_var(token)

    def _eval_func_call(self, node: Tree) -> Any:
        name_token = node.children[0]
        assert isinstance(name_token, Token)
        args: list[Any] = []
        if len(node.children) > 1:
            arg_list_node = node.children[1]
            assert isinstance(arg_list_node, Tree)
            args = list(self._eval_arg_list(arg_list_node))
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

        raise DSLError(
            f"Unknown function: {name}", line=token.line, column=token.column
        )

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
            raise DSLError(
                "set_precision expects 1 argument", line=token.line, column=token.column
            )
        value = self._to_decimal(args_list[0])
        if not self._is_int(value) or value < 0:
            raise DSLError(
                "set_precision expects integer >= 0",
                line=token.line,
                column=token.column,
            )
        old_precision = self._precision
        self._precision = int(value)
        
        # Обновить контекст Decimal чтобы поддерживать требуемую точность
        # Нужно установить prec больше чем количество десятичных знаков
        # Добавляем запас для целой части и промежуточных вычислений
        ctx = getcontext()
        ctx.prec = max(28, self._precision + 10)  # минимум 28, или precision + запас
        
        return Decimal(old_precision)

    def _apply_math_1(self, func: Any, args: Iterable[Any], token: Token) -> Any:
        args_list = list(args)
        if len(args_list) != 1:
            raise DSLError(
                f"{token.value} expects 1 argument",
                line=token.line,
                column=token.column,
            )
        value = float(self._to_decimal(args_list[0]))
        try:
            result = func(value)
        except ValueError as exc:
            raise DSLError(str(exc), line=token.line, column=token.column) from exc
        return self._round_value(Decimal(str(result)))

    def _apply_ctg(self, args: Iterable[Any], token: Token) -> Any:
        args_list = list(args)
        if len(args_list) != 1:
            raise DSLError(
                "ctg expects 1 argument", line=token.line, column=token.column
            )
        value = float(self._to_decimal(args_list[0]))
        tan_value = math.tan(value)
        if tan_value == 0:
            raise DivisionByZeroError(
                "ctg division by zero", line=token.line, column=token.column
            )
        return self._round_value(Decimal(str(1 / tan_value)))

    def _apply_sqrt(self, args: Iterable[Any], token: Token) -> Any:
        args_list = list(args)
        if len(args_list) != 1:
            raise DSLError(
                "sqrt expects 1 argument", line=token.line, column=token.column
            )
        value = self._to_decimal(args_list[0])
        if value < 0:
            raise DSLError("sqrt domain error", line=token.line, column=token.column)
        return self._round_value(Decimal(str(math.sqrt(float(value)))))

    def _apply_nrt(self, args: Iterable[Any], token: Token) -> Any:
        args_list = list(args)
        if len(args_list) != 2:
            raise DSLError(
                "nrt expects 2 arguments", line=token.line, column=token.column
            )
        x = self._to_decimal(args_list[0])
        n = self._to_decimal(args_list[1])
        if n == 0:
            raise DivisionByZeroError(
                "nrt division by zero", line=token.line, column=token.column
            )
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

    def _mod_pow(
        self, base: Decimal, exponent: Decimal, modulus: Decimal, meta: Any
    ) -> Decimal:
        if modulus == 0:
            raise DivisionByZeroError(
                "mod division by zero", line=meta.line, column=meta.column
            )
        return self._round_value(
            Decimal(pow(int(base), int(exponent), int(abs(modulus))))
        )

    def _div(self, left: Decimal, right: Decimal, meta: Any) -> Decimal:
        if right == 0:
            raise DivisionByZeroError(
                "division by zero", line=meta.line, column=meta.column
            )
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
            raise DivisionByZeroError(
                "mod division by zero", line=meta.line, column=meta.column
            )
        modulus = abs(right)
        quotient = (left / modulus).to_integral_value(rounding=ROUND_FLOOR)
        result = left - (quotient * modulus)
        return self._round_value(result)

    def _to_decimal(self, value: Any) -> Decimal:
        """Преобразовать значение в Decimal.

        Args:
            value: Значение для преобразования (Decimal, int, float, str, PowerValue)

        Returns:
            Значение типа Decimal

        Raises:
            DSLError: Если тип значения не поддерживается
        """
        if isinstance(value, PowerValue):
            return value.value
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

    def _ensure_numeric(self, value: Any, context: str = "operation") -> Decimal:
        """Убедиться, что значение - число, не булевское.

        Args:
            value: Значение для проверки
            context: Описание контекста (для сообщения об ошибке)

        Returns:
            Числовое значение (Decimal)

        Raises:
            BooleanError: Если значение - булевское
        """
        if isinstance(value, bool):
            raise BooleanError(
                f"Cannot use boolean value in {context}"
            )
        return self._to_decimal(value)

    def _eval_conditional_expr(self, node: Tree) -> Any:
        """Выполнить условное выражение: or_expr if or_expr else conditional_expr.

        Или просто или_выражение без условия.

        Args:
            node: Узел условного выражения

        Returns:
            Результат вычисления выражения
        """
        # Filter out SEP tokens
        children = [child for child in node.children if not (isinstance(child, Token) and child.type == "SEP")]
        
        if len(children) == 1:
            # Просто выражение без условия: conditional_expr -> or_expr
            return self._eval(children[0])
        
        # Условное выражение: or_expr if or_expr else conditional_expr
        # children: [then_expr_or_expr, condition_or_expr, else_expr_conditional_expr]
        then_expr = children[0]
        condition = children[1]
        else_expr = children[2]
        
        cond_result = self._eval(condition)
        if isinstance(cond_result, bool):
            if cond_result:
                return self._eval(then_expr)
            else:
                return self._eval(else_expr)
        
        raise BooleanError(
            "Condition in conditional expression must evaluate to boolean"
        )

    def _eval_or_expr(self, node: Tree) -> bool:
        """Выполнить логический OR с short-circuit evaluation.

        Args:
            node: Узел или-выражения

        Returns:
            Результат логического OR
        """
        # and_expr (OR and_expr)*
        result = self._eval(node.children[0])
        if not isinstance(result, bool):
            raise BooleanError(
                f"Left operand of 'or' must be boolean, got {type(result).__name__}"
            )
        
        # Iterate over operands: [operand, OP, operand, OP, operand, ...]
        for i in range(2, len(node.children), 2):
            if result:
                # Short-circuit: если уже true, не вычисляем дальше
                return True
            
            value = self._eval(node.children[i])
            if not isinstance(value, bool):
                raise BooleanError(
                    f"Right operand of 'or' must be boolean, got {type(value).__name__}"
                )
            result = value
        
        return result

    def _eval_and_expr(self, node: Tree) -> bool:
        """Выполнить логический AND с short-circuit evaluation.

        Args:
            node: Узел и-выражения

        Returns:
            Результат логического AND
        """
        # not_expr (AND not_expr)*
        result = self._eval(node.children[0])
        if not isinstance(result, bool):
            raise BooleanError(
                f"Left operand of 'and' must be boolean, got {type(result).__name__}"
            )
        
        # Iterate over operands: [operand, OP, operand, OP, operand, ...]
        for i in range(2, len(node.children), 2):
            if not result:
                # Short-circuit: если уже false, не вычисляем дальше
                return False
            
            value = self._eval(node.children[i])
            if not isinstance(value, bool):
                raise BooleanError(
                    f"Right operand of 'and' must be boolean, got {type(value).__name__}"
                )
            result = value
        
        return result

    def _eval_not_expr(self, node: Tree) -> Any:
        """Выполнить логический NOT или вернуть сравнение.

        Args:
            node: Узел not-выражения

        Returns:
            Результат логического NOT или сравнения
        """
        if len(node.children) == 1:
            # comparison -> просто возвращаем результат
            return self._eval(node.children[0])
        
        # len(node.children) == 2: "not" not_expr
        # First child is Token("not"), second is the not_expr to negate
        value = self._eval(node.children[1])
        if not isinstance(value, bool):
            raise BooleanError(
                f"Operand of 'not' must be boolean, got {type(value).__name__}"
            )
        return not value

    def _eval_comparison(self, node: Tree) -> bool:
        """Выполнить сравнение, поддерживая цепочки сравнений.

        Семантика: 1 < x < 10 -> (1 < x) and (x < 10)

        Args:
            node: Узел сравнения

        Returns:
            Результат сравнения (boolean)
        """
        children = node.children
        
        if len(children) == 1:
            # Просто выражение без сравнения: sum
            # Это не булевское значение в условном смысле, 
            # так что мы возвращаем его как есть или как true?
            # Согласно дизайну, в условиях должны быть булевские значения
            value = self._eval(children[0])
            # Если это не результат сравнения, это ошибка в условном контексте
            # Но здесь мы просто в правиле comparison, которое может быть использовано
            # не только в условиях. На самом деле, если нет операторов сравнения,
            # это просто number/atom. Вернем это значение.
            return value
        
        # Цепочка сравнений: sum COMP_OP sum COMP_OP sum ...
        # children: [sum, COMP_OP, sum, COMP_OP, sum, ...]
        result = True
        
        # Iterate over comparisons: [operand, OP, operand, OP, operand, ...]
        for i in range(0, len(children) - 2, 2):
            left = self._ensure_numeric(self._eval(children[i]))
            op_token = children[i + 1]
            assert isinstance(op_token, Token)
            op = op_token.value
            right = self._ensure_numeric(self._eval(children[i + 2]))
            
            if not self._compare(left, op, right):
                result = False
                break
        
        return result

    def _compare(self, left: Decimal, op: str, right: Decimal) -> bool:
        """Выполнить операцию сравнения.

        Args:
            left: Левый операнд
            op: Оператор сравнения (==, !=, <, <=, >, >=)
            right: Правый операнд

        Returns:
            Результат сравнения
        """
        if op == "==":
            return left == right
        if op == "!=":
            return left != right
        if op == "<":
            return left < right
        if op == "<=":
            return left <= right
        if op == ">":
            return left > right
        if op == ">=":
            return left >= right
        raise DSLError(f"Unknown comparison operator: {op}")

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
