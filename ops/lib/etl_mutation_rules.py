"""What a mutation IS, for the curvature oracle's modules. The runner is ops/lib/etl_mutation.py.

Split from it because these change for different reasons: this file grows when somebody finds a new shape of
evasion; the runner grows when the way a run is judged changes. It needs nothing but `ast`.

THE RULE SET IS AUDITED AGAINST THE EVASIONS THAT BEAT T-0074, not against a textbook list:

    E4   delete `or near_tagged_node(ours, grid)`      -> operand
    E5   size dodge `< (1 << 20)` -> `< (2 << 20)`     -> constant, compare
    E8   delete `if not same_geometry(...): continue`  -> continue, not
    E9   delete `if len(rows) != 1: continue`          -> continue, compare
    X6   `cap: int = 400` -> `cap: int = 4`            -> constant
    X11  drop one entry from NODE_TAGS                 -> dictkey, setmember

The one shape deliberately absent, stated rather than faked: E6 replaced `_sha256`'s streaming loop with a
single `fh.read(1 << 20)`. Replacing an arbitrary statement with an arbitrary other one is not an enumerable
mutation - it is writing a different program - so no rule attempts it. That shape belongs to a test that reads
a file larger than one block, which is T-0074's own outstanding correction.
"""
import ast


CMP_SWAP = {
    ast.Lt: ast.GtE, ast.GtE: ast.Lt,
    ast.Gt: ast.LtE, ast.LtE: ast.Gt,
    ast.Eq: ast.NotEq, ast.NotEq: ast.Eq,
    ast.In: ast.NotIn, ast.NotIn: ast.In,
    ast.Is: ast.IsNot, ast.IsNot: ast.Is,
}
BOOL_SWAP = {ast.And: ast.Or, ast.Or: ast.And}


class Collector(ast.NodeVisitor):
    """Every mutation this harness knows how to make, as (line, rule, description, applier)."""

    def __init__(self):
        self.found = []

    def _add(self, node, rule, desc, mutate):
        self.found.append((getattr(node, "lineno", 0), rule, desc, mutate))

    def visit_Compare(self, node):
        for i, op in enumerate(node.ops):
            new = CMP_SWAP.get(type(op))
            if new is None:
                continue
            def mutate(tree, _l=node.lineno, _c=node.col_offset, _i=i, _n=new):
                for t in ast.walk(tree):
                    if isinstance(t, ast.Compare) and t.lineno == _l and t.col_offset == _c:
                        t.ops[_i] = _n()
                        return True
                return False
            self._add(node, "compare", f"{type(op).__name__} -> {new.__name__}", mutate)
        self.generic_visit(node)

    def visit_BoolOp(self, node):
        new = BOOL_SWAP.get(type(node.op))
        if new is not None:
            def mutate(tree, _l=node.lineno, _c=node.col_offset, _n=new):
                for t in ast.walk(tree):
                    if isinstance(t, ast.BoolOp) and t.lineno == _l and t.col_offset == _c:
                        t.op = _n()
                        return True
                return False
            self._add(node, "boolop", f"{type(node.op).__name__} -> {new.__name__}", mutate)
        self.visit_BoolOp_operands(node)
        self.generic_visit(node)

    def visit_BoolOp_operands(self, node):
        """Drop one operand of an `and`/`or`. This is E4, the first evasion that beat T-0074: deleting
        `or near_tagged_node(ours, grid)` left the guard looking intact and excluding nothing."""
        if len(node.values) < 2:
            return
        for k in range(len(node.values)):
            def mutate(tree, _l=node.lineno, _c=node.col_offset, _k=k):
                for x in ast.walk(tree):
                    if isinstance(x, ast.BoolOp) and x.lineno == _l and x.col_offset == _c \
                            and len(x.values) > 1:
                        del x.values[_k]
                        if len(x.values) == 1:
                            for parent in ast.walk(tree):
                                for field, val in ast.iter_fields(parent):
                                    if val is x:
                                        setattr(parent, field, x.values[0]); return True
                                    if isinstance(val, list):
                                        for i, item in enumerate(val):
                                            if item is x:
                                                val[i] = x.values[0]; return True
                        return True
                return False
            self._add(node, "operand", f"drop operand {k} of {type(node.op).__name__}", mutate)

    def visit_Dict(self, node):
        """Drop one key from a dict literal - X11 narrowed NODE_TAGS instead of touching the code."""
        for k in range(len(node.keys)):
            key = node.keys[k]
            label = getattr(key, "value", "?") if isinstance(key, ast.Constant) else "<expr>"
            def mutate(tree, _l=node.lineno, _c=node.col_offset, _k=k):
                for x in ast.walk(tree):
                    if isinstance(x, ast.Dict) and x.lineno == _l and x.col_offset == _c \
                            and len(x.keys) > _k:
                        del x.keys[_k]; del x.values[_k]
                        return True
                return False
            self._add(node, "dictkey", f"drop key {label!r}", mutate)
        self.generic_visit(node)

    def visit_Set(self, node):
        """Drop one member of a set literal - the `highway` value-set half of X11."""
        for k in range(len(node.elts)):
            el = node.elts[k]
            label = getattr(el, "value", "?") if isinstance(el, ast.Constant) else "<expr>"
            def mutate(tree, _l=node.lineno, _c=node.col_offset, _k=k):
                for x in ast.walk(tree):
                    if isinstance(x, ast.Set) and x.lineno == _l and x.col_offset == _c \
                            and len(x.elts) > _k:
                        del x.elts[_k]
                        return True
                return False
            self._add(node, "setmember", f"drop member {label!r}", mutate)
        self.generic_visit(node)

    def visit_UnaryOp(self, node):
        if isinstance(node.op, ast.Not):
            def mutate(tree, _l=node.lineno, _c=node.col_offset):
                for t in ast.walk(tree):
                    for field, val in ast.iter_fields(t):
                        if isinstance(val, ast.UnaryOp) and isinstance(val.op, ast.Not) \
                                and val.lineno == _l and val.col_offset == _c:
                            setattr(t, field, val.operand)
                            return True
                        if isinstance(val, list):
                            for i, item in enumerate(val):
                                if isinstance(item, ast.UnaryOp) and isinstance(item.op, ast.Not) \
                                        and item.lineno == _l and item.col_offset == _c:
                                    val[i] = item.operand
                                    return True
                return False
            self._add(node, "not", "drop `not`", mutate)
        self.generic_visit(node)

    def visit_Constant(self, node):
        v = node.value
        if isinstance(v, bool):
            new = not v
        elif isinstance(v, int) and not isinstance(v, bool):
            new = v + 1
        elif isinstance(v, float):
            new = v + 1.0
        else:
            self.generic_visit(node); return
        def mutate(tree, _l=node.lineno, _c=node.col_offset, _n=new):
            for t in ast.walk(tree):
                if isinstance(t, ast.Constant) and t.lineno == _l and t.col_offset == _c:
                    t.value = _n
                    return True
            return False
        self._add(node, "constant", f"{v!r} -> {new!r}", mutate)
        self.generic_visit(node)

    def visit_Continue(self, node):
        # The shape every T-0074 evasion used: delete a guard's `continue` so the excluded case falls through.
        def mutate(tree, _l=node.lineno, _c=node.col_offset):
            for t in ast.walk(tree):
                for field, val in ast.iter_fields(t):
                    if isinstance(val, list):
                        for i, item in enumerate(val):
                            if isinstance(item, ast.Continue) and item.lineno == _l and item.col_offset == _c:
                                val[i] = ast.Pass()
                                return True
            return False
        self._add(node, "continue", "`continue` -> `pass`", mutate)
        self.generic_visit(node)


def mutants_for(path):
    """Every mutation this file knows how to make in `path`, deterministically ordered."""
    src = path.read_text(encoding="utf-8")
    c = Collector()
    c.visit(ast.parse(src))
    return src, sorted(c.found, key=lambda m: (m[0], m[1], m[2]))


# --------------------------------------------------------------------------- the floor under the denominator
# MAX_SURVIVORS in the runner bounds the numerator; on its own that is half a ratchet. Turning a rule off
# shrinks the mutant set, so fewer mutants survive, and the run prints a BETTER number and exits 0 without
# anyone touching MAX_SURVIVORS. Measured, not imagined: renaming visit_Dict/visit_Set out of the way took the
# enumeration 186 -> 154 and the survivors 69 -> 54 (PR #56 review). Same shape as MIN_FILES in
# ops/lib/check-exec-bits and MIN_FILES/MIN_CAPPED in ops/lib/check-line-cap, added there for the same reason.
#
# Per module, and scalars, deliberately: T-0079's `ratchet-lower:` hook parses a numeric binding of a
# MIN_*/MAX_* name and classifies a dict literal as `opaque`, which it then skips. A number here is guardable
# the day that hook merges; a dict would have looked like a ratchet and been none.
#
# Raising these is free. LOWERING one claims the module legitimately got smaller, and that has to be said out
# loud, because from the outside it is indistinguishable from an evasion.
MIN_MUTANTS_ORACLE = 66           # etl/oracle.py,        measured 2026-09-08
MIN_MUTANTS_ORACLE_SELECT = 120   # etl/oracle_select.py, measured 2026-09-08
MODULE_FLOORS = {"etl/oracle.py": MIN_MUTANTS_ORACLE, "etl/oracle_select.py": MIN_MUTANTS_ORACLE_SELECT}
