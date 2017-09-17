"""Spark Earley Algorithm parser ELISP
"""

import re
from spark_parser import GenericASTBuilder, DEFAULT_DEBUG as PARSER_DEFAULT_DEBUG

nop_func = lambda self, args: None

class ElispParser(GenericASTBuilder):
    def __init__(self, AST, start='fn_exprs', debug=PARSER_DEFAULT_DEBUG):
        super(ElispParser, self).__init__(AST, start, debug)
        self.collect = frozenset(['exprs', 'varbinds'])
        self.new_rules = set()

    def nonterminal(self, nt, args):
        if nt in self.collect and len(args) > 1:
            #
            #  Collect iterated thingies together. That is rather than
            #  stmts -> stmts stmt -> stmts stmt -> ...
            #  stmms -> stmt stmt ...
            #
            rv = args[0]
            rv.append(args[1])
        else:
            rv = GenericASTBuilder.nonterminal(self, nt, args)
        return rv

    def p_elisp_grammar(self, args):
        '''
        # The start or goal symbol
        fn_exprs ::= exprs RETURN

        exprs ::= exprs expr opt_discard
        exprs ::= expr opt_discard
        exprs ::= expr_stacked opt_discard

        progn ::= expr exprs

        expr  ::= setq_expr
        expr  ::= binary_expr
        expr  ::= unary_expr
        expr  ::= name_expr

        expr  ::= if_expr
        expr  ::= if_else_expr

        expr  ::= call_expr0
        expr  ::= call_expr1
        expr  ::= call_expr2
        expr  ::= call_expr3

        expr  ::= list_expr3

        expr_stacked ::= unary_expr_stacked
        expr_stacked ::= setq_expr_stacked

        unary_expr_stacked ::= unary_op
        binary_expr_stacked ::= expr binary_op


        expr  ::= let_expr
        # FIXME: add custom rule for things after 3

        if_expr ::= expr GOTO-IF-NIL-ELSE-POP expr opt_discard LABEL
        if_expr ::= expr GOTO-IF-NIL-ELSE-POP progn opt_discard LABEL
        if_expr ::= expr GOTO-IF-NIL expr opt_discard LABEL
        if_expr ::= expr GOTO-IF-NIL progn opt_discard LABEL

        if_else_expr ::= expr GOTO-IF-NIL expr opt_discard RETURN LABEL expr
        if_else_expr ::= expr GOTO-IF-NIL progn opt_discard RETURN LABEL expr


        call_expr0 ::= name_expr CALL_0
        call_expr1 ::= name_expr expr CALL_1
        call_expr2 ::= name_expr expr expr CALL_2
        call_expr3 ::= name_expr expr expr expr CALL_3

        name_expr ::= CONSTANT
        name_expr ::= VARREF

        binary_expr ::= expr expr bin_op

        bin_op ::= DIFF
        bin_op ::= EQLSIGN
        bin_op ::= GEQ
        bin_op ::= GTR
        bin_op ::= LEQ
        bin_op ::= LSS
        bin_op ::= MULT
        bin_op ::= PLUS
        bin_op ::= QUO
        bin_op ::= REM
        bin_op ::= TIMES

        unary_expr ::= expr unary_op

        unary_op ::= ADD1
        unary_op ::= CAR
        unary_op ::= CDR
        unary_op ::= INTEGERP
        unary_op ::= NOT

        setq_expr ::= expr VARSET
        setq_expr ::= expr DUP VARSET
        setq_expr ::= expr DUP VARSET
        setq_expr_stacked ::= expr_stacked DUP VARSET


        let_expr ::= varbind exprs UNBIND


        opt_discard ::= DISCARD
        opt_discard ::=

        # varbinds ::= varbinds varbind
        varbind  ::= expr VARBIND
        varbind  ::= expr DUP VARBIND
        '''
        return

    def add_unique_rule(self, rule, opname):
        """Add rule to grammar, but only if it hasn't been added previously
           opname and count are used in the customize() semantic the actions
           to add the semantic action rule. Often, count is not used.
        """
        if rule not in self.new_rules:
            print("XXX ", rule) # debug
            self.new_rules.add(rule)
            self.addRule(rule, nop_func)
            pass
        return

    def add_custom_rules(self, tokens, customize):
        for opname, v in customize.items():
            if opname.startswith('LIST'):
                m = re.match(r'([^0-9]+)\d', opname)
                opname_base = m.group(1)
                nt = "%s_expr%d" % (opname_base.lower(), v)
                rule = '%s ::= expr expr %s' % (nt, opname)
                self.add_unique_rule(rule, opname_base)
                rule = 'expr  ::= %s' % nt
                self.add_unique_rule(rule, opname_base)
            pass
        return
    pass
