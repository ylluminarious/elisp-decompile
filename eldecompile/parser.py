"""Spark Earley Algorithm parser ELISP
"""
from spark_parser import GenericASTBuilder, DEFAULT_DEBUG as PARSER_DEFAULT_DEBUG

class ElispParser(GenericASTBuilder):
    def __init__(self, AST, start='exprs', debug=PARSER_DEFAULT_DEBUG):
        super(ElispParser, self).__init__(AST, start, debug)
        self.collect = frozenset(['exprs'])

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
        exprs ::= exprs expr opt_discard
        exprs ::= expr opt_discard

        expr  ::= setq_expr
        expr  ::= return_expr
        expr  ::= binary_expr
        expr  ::= unary_expr
        expr  ::= name_expr

        expr  ::= if_expr

        expr  ::= call_expr0
        expr  ::= call_expr1
        expr  ::= call_expr2
        expr  ::= call_expr3
        # FIXME: add custom rule for things after 3

        if_expr ::= expr GOTO-IF-NIL-ELSE-POP expr


        call_expr0 ::= name_expr CALL_0
        call_expr1 ::= expr name_expr CALL_1
        call_expr2 ::= expr expr name_expr CALL_2
        call_expr3 ::= expr expr expr name_expr CALL_3

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

        setq_expr ::= expr VARSET
        setq_expr ::= expr DUP VARSET
        return_expr ::= RETURN

        opt_discard ::= DISCARD
        opt_discard ::=
        '''
        return
    pass
