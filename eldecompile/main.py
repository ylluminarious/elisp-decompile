#!/usr/bin/env python
from spark_parser.ast import AST

from eldecompile.scanner import fn_scanner
from eldecompile.parser import ElispParser
from eldecompile.semantics import SourceWalker
from eldecompile.bb import basic_blocks
from eldecompile.cfg import ControlFlowGraph
from eldecompile.dominators import DominatorTree, build_df


import os, sys

def flow_control(name, tokens):
#  Flow control analysis of instruction
    bblocks, tokens = basic_blocks(tokens)
    for bb in bblocks.bb_list:
        print("\t", bb)
    cfg = ControlFlowGraph(bblocks.bb_list)
    dot_path = '/tmp/flow-%s.dot' % name
    png_path = '/tmp/flow-%s.png' % name
    open(dot_path, 'w').write(cfg.graph.to_dot())
    print("%s written" % dot_path)
    os.system("dot -Tpng %s > %s" % (dot_path, png_path))
    try:
        dom_tree = DominatorTree(cfg).tree()
        dom_tree = build_df(dom_tree)
        dot_path = '/tmp/flow-dom-%s.dot' % name
        png_path = '/tmp/flow-dom-%s.png' % name
        open(dot_path, 'w').write(dom_tree.to_dot())
        print("%s written" % dot_path)
        os.system("dot -Tpng %s > %s" % (dot_path, png_path))
        print('=' * 30)
        return tokens
    except:
        import traceback
        traceback.print_exc()
        print("Unexpected error:", sys.exc_info()[0])
        print("%s had an error" % name)
        return tokens

def deparse(path):
    # Scan...
    with open(path, 'r') as fp:
        fn_def, tokens, customize = fn_scanner(fp)
        pass

    import os.path as osp
    name = osp.basename(path)
    tokens = flow_control(name, tokens)

    # Parse...
    p = ElispParser(AST, tokens)
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


def main():
    if len(sys.argv) == 2:
        path = sys.argv[1]
    else:
        # path = '../testdata/binops.dis'
        # path = '../testdata/control.dis'
        path = '../testdata/unary-ops.dis'
    deparse(path)

if __name__ == '__main__':
    main()
