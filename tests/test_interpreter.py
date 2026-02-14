from decimal import Decimal

import pytest

from interpreter import DivisionByZeroError, Interpreter, VariableNotFoundError


def eval_code(code: str):
    return Interpreter().execute(code)


def test_operator_precedence():
    result = eval_code("2 + 2 * 2")
    assert result == Decimal("6")


def test_power_mod_precedence():
    result = eval_code("2 ** 3 mod 5")
    assert result == Decimal("3")


def test_assignments_sequence():
    result = eval_code("x = 5; x += 10; x mod= 4; x")
    assert result == Decimal("3")


def test_math_functions():
    result = eval_code("sqrt(4)")
    assert result == Decimal("2")
    result = eval_code("sin(pi/2)")
    assert result == Decimal("1")
    result = eval_code("ln(e)")
    assert result == Decimal("1")
    result = eval_code("nrt(27, 3)")
    assert result == Decimal("3")


def test_division_by_zero():
    with pytest.raises(DivisionByZeroError):
        eval_code("1 / 0")


def test_domain_errors():
    with pytest.raises(Exception):
        eval_code("sqrt(-1)")


def test_undefined_variable():
    with pytest.raises(VariableNotFoundError):
        eval_code("x + 1")


def test_negative_mod_semantics():
    result = eval_code("-5 mod 3")
    assert result == Decimal("1")


def test_for_expression_result():
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
    code = """
    i = 10
    for i in 1..3 (i)
    i
    """
    result = eval_code(code)
    assert result == Decimal("3")


def test_loop_variable_not_visible_when_new():
    code = """
    for i in 1..1 (i)
    i
    """
    with pytest.raises(VariableNotFoundError):
        eval_code(code)


def test_loop_not_run_keeps_original_value():
    code = """
    i = 7
    for i in 5..1 by -2 (i)
    i
    """
    result = eval_code(code)
    assert result == Decimal("1")


def test_print_allows_strings(capsys):
    interp = Interpreter()
    interp.execute('print("x =", 2 + 2)')
    captured = capsys.readouterr()
    assert captured.out.strip() == "x = 4.0000000000"


def test_precision_control():
    """Test get_precision and set_precision functions."""
    interp = Interpreter()
    
    # Default precision is 10
    result = interp.execute("get_precision()")
    assert result == Decimal("10")
    
    # Set precision to 5
    interp.execute("set_precision(5)")
    result = interp.execute("get_precision()")
    assert result == Decimal("5")
    
    # Set precision to 0 (allowed)
    interp.execute("set_precision(0)")
    result = interp.execute("get_precision()")
    assert result == Decimal("0")
    
    # Restore precision
    interp.execute("set_precision(10)")
    result = interp.execute("get_precision()")
    assert result == Decimal("10")


def test_precision_affects_formatting(capsys):
    """Test that precision affects print output formatting."""
    interp = Interpreter()
    code = """
x = 2 + 2 * 2
set_precision(4)
p = get_precision()
set_precision(0)
print("2 + 2 * 2 =", x)
set_precision(p)
print("2 + 2 * 2 =", x)
    """
    interp.execute(code)
    captured = capsys.readouterr()
    lines = captured.out.strip().split('\n')
    
    # First line: precision 0, should print "6" without decimal point
    assert lines[0] == "2 + 2 * 2 = 6"
    
    # Second line: precision 4, should print "6.0000" with 4 decimal places
    assert lines[1] == "2 + 2 * 2 = 6.0000"


def test_precision_zero_formats_as_integer(capsys):
    """Test that precision 0 formats numbers as integers."""
    interp = Interpreter()
    interp.execute("set_precision(0)")
    interp.execute('print("result:", 123.456789)')
    captured = capsys.readouterr()
    assert captured.out.strip() == "result: 123"
    
    # Test with whole number expression
    interp.execute('print(10 / 2)')
    captured = capsys.readouterr()
    assert captured.out.strip() == "5"


def test_precision_affects_calculations():
    """Test that precision affects calculation results."""
    interp = Interpreter()
    
    # With precision 2
    interp.execute("set_precision(2)")
    result = interp.execute("1 / 3")
    # Should be rounded to 2 decimal places
    assert result == Decimal("0.33")
    
    # With precision 5
    interp.execute("set_precision(5)")
    result = interp.execute("1 / 3")
    assert result == Decimal("0.33333")


def test_set_precision_returns_old_value():
    """Test that set_precision returns the old precision value."""
    interp = Interpreter()
    
    # Test exact user scenario: set_precision(10); p = set_precision(0); p
    code = """set_precision(10)
p = set_precision(0)
p"""
    result = interp.execute(code)
    assert result == Decimal("10")
    
    # Test chaining
    code = """set_precision(5)
old = set_precision(3)
old"""
    result = interp.execute(code)
    assert result == Decimal("5")
