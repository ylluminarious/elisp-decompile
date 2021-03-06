"""Spark Earley Algorithm parser ELISP
"""

import re
from spark_parser import GenericASTBuilder, DEFAULT_DEBUG as PARSER_DEFAULT_DEBUG

nop_func = lambda self, args: None

class ParserError(Exception):
    def __init__(self, token, offset):
        self.token = token
        self.offset = offset

    def __str__(self):
        return "Parse error at or near `%r' instruction at offset %s\n" % \
               (self.token, self.offset)

class ElispParser(GenericASTBuilder):
    def __init__(self, AST, tokens, start='fn_body', debug=PARSER_DEFAULT_DEBUG):
        self.tokens = tokens
        super(ElispParser, self).__init__(AST, start, debug)
        self.collect = frozenset(['exprs', 'varlist' 'labeled_clauses'])
        self.new_rules = set()

    def error(self, tokens, index):
        # Find the last label
        start, finish = -1, -1
        n = len(tokens)
        for start in range(index, -1, -1):
            if tokens[start].label:  break
            pass
        for finish in range(index+1, len(tokens)):
            if tokens[finish].label:  break
            pass
        if start == finish == -1:
            start, finish = (0, n)
        elif start == -1:
            start = 0
        elif finish == -1:
            finish = n

        err_token = tokens[index]
        print("Instruction context:")
        for i in range(start, finish):
            if i != index:
                indent = '   '
            else:
                indent = '-> '
            print("%s%s" % (indent, tokens[i]))
        raise ParserError(err_token, err_token.offset)
        return

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
        '''# The start or goal symbol
        fn_body ::= body opt_return

        # expr_stmt is an expr where the value it produces
        # might not be needed. List-like things like
        # progn or let fall into this category.
        expr_stmt  ::= expr opt_discard

        # By its very nature of being sequenced
        # exprs must use a list-like or stmt_expr

        exprs ::= expr_stmt+


        progn ::= body

        expr  ::= DUP
        expr  ::= setq_expr
        expr  ::= set_expr
        expr  ::= STACK-REF
        expr  ::= VARREF

        # Function related
        expr  ::= binary_expr
        expr  ::= unary_expr
        expr  ::= nullary_expr
        expr  ::= name_expr
        expr  ::= pop_expr

        # Control-flow related
        expr  ::= if_expr
        expr  ::= if_else_expr
        expr  ::= when_expr
        expr  ::= cond_expr
        expr  ::= or_expr
        expr  ::= and_expr
        expr  ::= not_expr
        expr  ::= dolist_expr
        expr  ::= dolist_expr_result
        expr  ::= while_expr
        expr  ::= while_expr_stacked

        # Block related
        expr  ::= let_expr_star
        expr  ::= let_expr_stacked

        # Buffer related
        expr  ::= save_excursion
        expr  ::= save_current_buffer
        expr  ::= set_buffer

        body  ::= exprs

        body_stacked  ::= expr_stacked exprs
        body_stacked  ::= expr_stacked

        expr_stacked ::= unary_expr_stacked
        expr_stacked ::= binary_expr_stacked
        expr_stacked ::= setq_expr_stacked

        save_excursion      ::= SAVE-EXCURSION body UNBIND
        save_current_buffer ::= SAVE-CURRENT-BUFFER body UNBIND
        set_buffer          ::= expr SET-BUFFER

        unary_expr_stacked  ::= unary_op
        unary_expr_stacked  ::= expr_stacked unary_op
        binary_expr_stacked ::= expr binary_op


        # if_expr ::= expr GOTO-IF-NIL-ELSE-POP expr LABEL
        # if_expr ::= expr GOTO-IF-NIL-ELSE-POP progn LABEL
        if_expr ::= expr GOTO-IF-NIL expr COME_FROM LABEL

        # We keep nonterminals at position 0 and 2
        filler  ::=
        if_expr ::= expr GOTO-IF-NIL expr COME_FROM LABEL
        if_expr ::= expr filler expr COME_FROM LABEL

        while_expr_stacked ::= expr COME_FROM LABEL expr_stacked
                       GOTO-IF-NIL-ELSE-POP body
                       GOTO COME_FROM LABEL

        while_expr ::= COME_FROM LABEL expr
                       GOTO-IF-NIL-ELSE-POP body
                       GOTO COME_FROM LABEL

        when_expr ::= expr GOTO-IF-NIL body COME_FROM LABEL


        # Note: the VARSET's have special names which we could
        # check in a reduce rule.
        dolist_expr ::= dolist_list dolist_init_var
                        GOTO-IF-NIL-ELSE-POP COME_FROM LABEL
                        dolist_loop_iter_set body
                        DUP VARSET GOTO-IF-NOT-NIL
                        CONSTANT COME_FROM LABEL
                        UNBIND

        dolist_expr ::= dolist_list dolist_init_var
                        GOTO-IF-NIL-ELSE-POP COME_FROM LABEL
                        dolist_loop_iter_set_stacking body_stacked
                        DUP VARSET GOTO-IF-NOT-NIL
                        CONSTANT COME_FROM LABEL
                        UNBIND


        dolist_expr_result ::= dolist_list dolist_init_var
                        GOTO-IF-NIL COME_FROM LABEL
                        dolist_loop_iter_set body
                        VARREF CDR DUP VARSET GOTO-IF-NOT-NIL
                        COME_FROM LABEL CONSTANT VARSET expr
                        UNBIND

        dolist_loop_iter_set ::= VARREF CAR VARSET
        dolist_loop_iter_set_stacking ::= VARREF CAR DUP VARSET
        dolist_init_var      ::= varbind DUP VARBIND
        dolist_list          ::= expr


        # if_else_expr ::= expr GOTO-IF-NIL expr RETURN LABEL
        # if_else_expr ::= expr_stacked GOTO-IF-NIL progn RETURN LABEL

        # Keep nonterminals at positions  0 and 2
        or_expr    ::= expr GOTO-IF-NOT-NIL-ELSE-POP expr opt_come_from opt_label
        or_expr    ::= expr GOTO-IF-NOT-NIL          expr GOTO-IF-NIL-ELSE-POP COME_FROM LABEL

        # "not_expr" is (not expr) or (null expr). We use
        # not_ instead of null_ to to avoid confusion with nil
        not_expr   ::= expr GOTO-IF-NOT-NIL

        and_expr   ::= expr GOTO-IF-NIL-ELSE-POP expr COME_FROM LABEL
        # and_expr ::= expr GOTO-IF-NIL expr opt_label

        call_expr0 ::= name_expr CALL_0
        call_expr1 ::= name_expr expr CALL_1
        call_expr2 ::= name_expr expr exp_stacked CALL_2
        call_expr3 ::= name_expr expr expr expr CALL_3

        name_expr ::= CONSTANT

        expr_stacking ::= setq_expr_stacking binary_op

        binary_expr ::= expr expr binary_op
        binary_expr ::= expr_stacking binary_op

        binary_op ::= DIFF
        binary_op ::= EQLSIGN
        binary_op ::= EQ
        binary_op ::= EQUAL
        binary_op ::= GEQ
        binary_op ::= GTR
        binary_op ::= LEQ
        binary_op ::= LSS
        binary_op ::= MULT
        binary_op ::= PLUS
        binary_op ::= QUO
        binary_op ::= REM
        binary_op ::= TIMES

        unary_expr ::= expr unary_op

        unary_op ::= ADD1
        unary_op ::= CAR
        unary_op ::= CAR-SAFE
        unary_op ::= CDR
        unary_op ::= CDR-SAFE
        unary_op ::= CONSP
        unary_op ::= INSERT
        unary_op ::= INTEGERP
        unary_op ::= KEYWORDP
        unary_op ::= LISTP
        unary_op ::= NATNUMP
        unary_op ::= NLISTP
        unary_op ::= NOT
        unary_op ::= NUMBERP
        unary_op ::= NULL
        unary_op ::= RECORDP
        unary_op ::= SEQUENCEP
        unary_op ::= STACK-SET
        unary_op ::= STRINGP
        unary_op ::= SUBR-ARITY
        unary_op ::= SUB1
        unary_op ::= SUBRP
        unary_op ::= SYMBOL-FUNCTION
        unary_op ::= SYMBOL-NAME
        unary_op ::= SYMBOL-PLIST
        unary_op ::= SYMBOLP
        unary_op ::= THREADP
        unary_op ::= TYPE-OF
        unary_op ::= USER-PTRP
        unary_op ::= VECTOR_OR_CHAR-TABLEP
        unary_op ::= VECTORP

        nullary_expr ::= nullary_op

        nullary_op ::= BOLP
        nullary_op ::= CURRENT-BUFFER
        nullary_op ::= CURRENT-COLUMN
        nullary_op ::= EOLP
        nullary_op ::= FOLLOWING-CHAR
        nullary_op ::= POINT
        nullary_op ::= POINT-MAX
        nullary_op ::= POINT-MIN
        nullary_op ::= PRECEDING-CHAR
        nullary_op ::= WIDEN

        # We could have a checking rule that the VARREF and VARSET refer to the same thing
        pop_expr ::= VARREF DUP CDR VARSET CAR-SAFE

        setq_expr ::= expr VARSET
        setq_expr ::= expr DUP VARSET
        setq_expr_stacked ::= expr_stacked DUP VARSET
        setq_expr_stacking ::= expr DUP VARSET

        set_expr  ::= expr expr SET
        set_expr  ::= expr expr STACK-SET SET


        # FIXME: this is probably to permissive
        end_clause ::= GOTO COME_FROM
        end_clause ::= RETURN COME_FROM
        end_clause ::= RETURN

        cond_expr  ::= clause labeled_clauses come_froms LABEL
        cond_expr  ::= clause labeled_clauses

        opt_come_froms ::= come_froms?
        come_froms ::= COME_FROM+

        # We use labeled_clause+ rather than labeled_clause* because
        # labeled_clause* wreaks havoc in reductions and gives
        # produces things like (cond (t 5)) when what we want is just
        # 5. labeled_clause+ won't match (cond (foo bar baz)) where
        # there is a single cond clause but we'll handle that as an
        # "if" rule, e.g. (if foo (progn bar baz))

        labeled_clauses ::= labeled_clause labeled_clauses
        labeled_clauses ::= labeled_clause
        labeled_clauses ::= labeled_final_clause

        labeled_clause  ::= LABEL clause

        # The "opt_come_from opt_label" below reflects the fact that
        # expr might be a short-circuit expression like "and" or "or"
        # which acts like and early false on the GOTO-IF-NIL

        condition       ::= expr GOTO-IF-NIL opt_come_from opt_label
        condition       ::= expr GOTO-IF-NIL-ELSE-POP opt_come_from opt_label

        clause          ::= condition body end_clause

        # The final clause of a cond doesn't need a GOTO or a return.
        # But it must have a label, and must have several COME_FROMs for
        # each of the clauses in the cond.
        labeled_final_clause    ::= LABEL condition body come_froms

        # clause          ::= body end_clause

        # cond (t *body*) compiles to no condition
        # If this is the first clause, then possibly
        # no label
        clause          ::= opt_label body end_clause

        opt_come_from ::= COME_FROM?
        opt_label     ::= LABEL?

        let_expr_stacked ::= varlist_stacked body_stacked UNBIND

        varlist_stacked ::= expr varlist_stacked_inner DUP VARBIND
        varlist_stacked_inner ::= expr varlist_stacked_inner VARBIND
        varlist_stacked_inner ::=

        let_expr_star ::= varlist body UNBIND
        # Sometimes the last item in "body" is "UNBIND" so we don't need
        # to add it here. We could have a reduce check to ensure this.
        let_expr_star ::= varlist body

        varlist  ::= varbind varlist
        varlist  ::= varbind
        varbind  ::= expr VARBIND

        opt_discard ::= DISCARD?
        opt_return  ::= RETURN?

        '''
        return

    def add_unique_rule(self, rule, opname):
        """Add rule to grammar, but only if it hasn't been added previously
           opname and count are used in the customize() semantic the actions
           to add the semantic action rule. Often, count is not used.
        """
        if rule not in self.new_rules:
            self.new_rules.add(rule)
            self.addRule(rule, nop_func)
            pass
        return

    def add_custom_rules(self, tokens, customize):
        for opname, v in customize.items():
            if re.match(r'^LIST|CONCAT|CALL', opname):
                opname_base = opname[:opname.index('_')]
                if opname_base[-1] == 'N':
                    opname_base = opname_base[:-1]
                nt = "%s_exprn" % (opname_base.lower())
                rule = '%s ::= %s%s' % (nt, ('expr ' * v), opname)
                self.add_unique_rule(rule, opname_base)
                rule = 'expr  ::= %s' % nt
                self.add_unique_rule(rule, opname_base)
            pass
        # self.check_reduce['progn'] = 'AST'
        self.check_reduce['clause'] = 'AST'
        self.check_reduce['cond_expr'] = 'AST'
        return

    def debug_reduce(self, rule, tokens, parent, last_token_pos):
        """Customized format and print for our kind of tokens
        which gets called in debugging grammar reduce rules
        """
        prefix = ''
        if parent and tokens:
            p_token = tokens[parent]
            if hasattr(p_token, 'offset'):
                prefix += "%3s" % p_token.offset
                if len(rule[1]) > 1:
                    prefix += '-%-5s ' % tokens[last_token_pos-1].offset
                else:
                    prefix += '       '
        else:
            prefix = '          '

        print("%s%s ::= %s (%d)" % (prefix, rule[0], ' '.join(rule[1]), last_token_pos))

    def reduce_is_invalid(self, rule, ast, tokens, first, last):
        lhs = rule[0]
        if lhs == 'clause' and len(ast) == 3 and ast[0] != 'opt_label':
            # Check that either:
            #   if we have a condition there is a COME_FROM in the end_clause or
            #   if we don't have a condition there is no COME_FROM in the end_clause
            end_clause = ast[2]
            if ast[0].kind == 'condition' and len(end_clause) == 1:
                if (end_clause[0] not in ('COME_FROM', 'RETURN')
                    and tokens[last] != 'RETURN'):
                    return True
            if ast[0].kind != 'condition' and end_clause[-1] == 'COME_FROM':
                return True
        if rule == ('cond_expr', ('clause', 'labeled_clauses')):
            # Since there are no come froms, each of the clauses
            # must end in a return.
            for n in ast:
                if n == 'labeled_clauses':
                    n = n[0]
                if n == 'labeled_clause':
                    clause = n[1]
                elif n == 'clause':
                    clause = n
                else:
                    return False
                end_clause = clause[-1]
                if end_clause[0].kind != 'RETURN':
                    return True
                pass
        return False
    pass
