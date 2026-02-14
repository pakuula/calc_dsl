#!/usr/bin/env python3
from interpreter import Interpreter

interp = Interpreter()
tree = interp.parse("x = 5\ny = 10")
print(tree.pretty())
