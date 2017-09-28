#!/usr/bin/env python
from spark_parser.ast import AST

from eldecompile.scanner import fn_scanner
from eldecompile.parser import ElispParser
from eldecompile.semantics import SourceWalker

import sys

if len(sys.argv) == 2:
    path = sys.argv[1]
else:
    # path = '../testdata/binops.dis'
    # path = '../testdata/control.dis'
    path = '../testdata/unary-ops.dis'

# Scan...
with open(path, 'r') as fp:
    fn_def, tokens, customize = fn_scanner(fp)
    pass

# Parse...
p = ElispParser(AST)
p.add_custom_rules(tokens, customize)

parser_debug = {'rules': False, 'transition': False, 'reduce' : True,
               'errorstack': 'full', 'dups': False }

ast = p.parse(tokens, debug=parser_debug)
print(ast)

# .. and Generate Elisp
formatter = SourceWalker(ast)
indent = '  '
result = formatter.traverse(ast, indent)
result = result.rstrip()
header = "(%s %s%s%s" % (fn_def.fn_type, fn_def.name, fn_def.args,
                             fn_def.docstring)
if (not header.endswith("\n")
        and not result.startswith("\n") or fn_def.interactive):
    header += "\n"
if fn_def.interactive is not None:
    print("%s%s(interactive %s)\n%s%s)" %
          (header, indent, fn_def.interactive, indent, result))
else:
    print("%s%s%s)" % (header, indent, result))
