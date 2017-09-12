#!/usr/bin/env python
from collections import namedtuple
import re
from spark_parser import GenericASTTraversal
from spark_parser.ast import AST

from eldecompile.scanner import fn_scanner
from eldecompile.parser import ElispParser

Instruction = namedtuple("Instruction",
     "offset opname operand")

try:
    from io import StringIO
except:
    from StringIO import StringIO


TAB = ' ' *4   # is less spacy than "\t"
INDENT_PER_LEVEL = ' ' # additional intent per pretty-print level
TABLE_R = {
}

TABLE_R0 = {
}

TABLE_DIRECT = {
    'setq_expr':	( '%|(setq %c %c)\n', -1, 0),
    'plus_expr':	( '(+ %c %c)', 1, 0),

    'call_expr1':	( '%|(%c %c)\n', 0, 1),

    'CONSTANT':	        ( '%{attr}', ),
    'VARSET':	        ( '%{attr}', ),
    'VARREF':	        ( '%{attr}', ),
}

MAP_DIRECT = (TABLE_DIRECT, )

escape = re.compile(r'''
            (?P<prefix> [^%]* )
            % ( \[ (?P<child> -? \d+ ) \] )?
                ((?P<type> [^{] ) |
                 ( [{] (?P<expr> [^}]* ) [}] ))
        ''', re.VERBOSE)

class SourceWalkerError(Exception):
    def __init__(self, errmsg):
        self.errmsg = errmsg

    def __str__(self):
        return self.errmsg

class SourceWalker(GenericASTTraversal, object):

    indent = property(lambda s: s.params['indent'],
                 lambda s, x: s.params.__setitem__('indent', x),
                 lambda s: s.params.__delitem__('indent'),
                 None)

    def __init__(self, ast):
        GenericASTTraversal.__init__(self, ast=None)
        params = {
            'indent': '',
            }
        self.params = params
        self.ERROR = None
        self.pending_newlines = 0
        self.hide_internal = True
        return

    f = property(lambda s: s.params['f'],
                 lambda s, x: s.params.__setitem__('f', x),
                 lambda s: s.params.__delitem__('f'),
                 None)

    def n_CONSTANT(self, node):
        if re.match(r'[0-9"]', node.attr[0]):
            # Integer or string
            self.f.write(node.attr.decode('utf-8'))
        else:
            # Assume we have a LISP symbol
            self.f.write(u"'")
            self.f.write(node.attr.decode('utf-8'))

    def indentMore(self, indent=TAB):
        self.indent += indent

    def indentLess(self, indent=TAB):
        self.indent = self.indent[:-len(indent)]

    def traverse(self, node, indent=None, isLambda=False):
        if indent is None: indent = self.indent
        p = self.pending_newlines
        self.pending_newlines = 0
        self.params = {
            'f': StringIO(),
            'indent': indent,
            }
        self.preorder(node)
        self.f.write(u'\n'*self.pending_newlines)
        result = self.f.getvalue()
        self.pending_newlines = p
        return result


    def engine(self, entry, startnode):
        """The format template interpetation engine.  See the comment at the
        beginning of this module for the how we interpret format specifications such as
        %c, %C, and so on.
        """

        # self.println("-----")
        # print("XXX", startnode)

        fmt = entry[0]
        arg = 1
        i = 0

        m = escape.search(fmt)
        while m:
            i = m.end()
            self.write(m.group('prefix'))

            typ = m.group('type') or '{'
            node = startnode
            try:
                if m.group('child'):
                    node = node[int(m.group('child'))]
            except:
                print(node.__dict__)
                raise

            if   typ == '%':	self.write('%')
            elif typ == '+':	self.indentMore()
            elif typ == '-':	self.indentLess()
            elif typ == '|':	self.write(self.indent)
            elif typ == 'c':
                if isinstance(entry[arg], int):
                    self.preorder(node[entry[arg]])
                arg += 1
            elif typ == 'p':
                (index, self.prec) = entry[arg]
                self.preorder(node[index])
                arg += 1
            elif typ == 'C':
                low, high, sep = entry[arg]
                remaining = len(node[low:high])
                for subnode in node[low:high]:
                    self.preorder(subnode)
                    remaining -= 1
                    if remaining > 0:
                        self.write(sep)
                arg += 1
            elif typ == 'D':
                low, high, sep = entry[arg]
                remaining = len(node[low:high])
                for subnode in node[low:high]:
                    remaining -= 1
                    if len(subnode) > 0:
                        self.preorder(subnode)
                        if remaining > 0:
                            self.write(sep)
                            pass
                        pass
                    pass
                arg += 1
            elif typ == 'x':
                # This code is only used in fragments
                assert isinstance(entry[arg], tuple)
                arg += 1
            elif typ == 'P':
                p = self.prec
                low, high, sep, self.prec = entry[arg]
                remaining = len(node[low:high])
                # remaining = len(node[low:high])
                for subnode in node[low:high]:
                    self.preorder(subnode)
                    remaining -= 1
                    if remaining > 0:
                        self.write(sep)
                self.prec = p
                arg += 1
            elif typ == '{':
                d = node.__dict__
                expr = m.group('expr')
                try:
                    self.write(eval(expr, d, d))
                except:
                    print(node)
                    raise
            m = escape.search(fmt, i)
        self.write(fmt[i:])

    def default(self, node):
        table = MAP_DIRECT[0]
        key = node

        for i in MAP_DIRECT[1:]:
            key = key[i]

        if key.type in table:
            self.engine(table[key.type], node)
            self.prune()

    def write(self, *data):
        udata = [d.decode('utf-8') for d in data]
        self.f.write(*udata)
        return

# import sys
# with open(sys.argv[1], 'r') as fp:
with open('assign.dis', 'r') as fp:
    header, fn_args, tokens, constants = fn_scanner(fp)
    pass

p = ElispParser(AST)
parser_debug = {'rules': False, 'transition': False, 'reduce' : True,
               'errorstack': 'full', 'dups': False }

ast = p.parse(tokens, debug=parser_debug)
print(ast)
formatter = SourceWalker(ast)
result = formatter.traverse(ast)
print(result)
