"""
FP&A Dream — Formula Engine

FormulaParser  : safely parses formula strings using Python's ast module
DependencyGraph: builds a DAG of line item dependencies, topological sort
ActualsLoader  : sums transactions from Phase 1 data into time periods
Evaluator      : orchestrates the full calculation run for a model+scenario
"""

import ast
from dataclasses import dataclass, field
from decimal import Decimal, DivisionByZero, InvalidOperation
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.modeling import FinancialModel, Scenario, TimePeriod, LineItem, CellValue, LineItemType, ScenarioType
from app.models.financial import Transaction, Account


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class FormulaSyntaxError(Exception):
    pass


class CircularReferenceError(Exception):
    pass


# ---------------------------------------------------------------------------
# FormulaParser
# ---------------------------------------------------------------------------

BUILTIN_FUNCTIONS = {"SUM", "AVG", "IF", "PRIOR", "GROWTH"}
ALLOWED_NODES = (
    ast.Expression, ast.BinOp, ast.UnaryOp, ast.USub, ast.UAdd,
    ast.Add, ast.Sub, ast.Mul, ast.Div,
    ast.Constant, ast.Name, ast.Call,
    ast.Compare, ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
    ast.BoolOp, ast.And, ast.Or,
    ast.Load,
)


@dataclass
class ParsedFormula:
    raw: str
    dependencies: set[str] = field(default_factory=set)
    uses_prior: bool = False
    uses_growth: bool = False
    ast_node: Optional[ast.Expression] = None


class FormulaParser:
    def parse(self, formula: str) -> ParsedFormula:
        try:
            tree = ast.parse(formula.strip(), mode="eval")
        except SyntaxError as e:
            raise FormulaSyntaxError(f"Syntax error in formula: {e}") from e

        parsed = ParsedFormula(raw=formula)
        self._validate_and_extract(tree, parsed)
        parsed.ast_node = tree
        return parsed

    def _validate_and_extract(self, node, parsed: ParsedFormula):
        if not isinstance(node, tuple(ALLOWED_NODES)):
            raise FormulaSyntaxError(
                f"Unsupported expression type '{type(node).__name__}' in formula. "
                "Only arithmetic operators, comparisons, and built-in functions are allowed."
            )

        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise FormulaSyntaxError("Only built-in function calls are allowed.")
            func_name = node.func.id
            if func_name not in BUILTIN_FUNCTIONS:
                raise FormulaSyntaxError(
                    f"Unknown function '{func_name}'. "
                    f"Allowed: {', '.join(sorted(BUILTIN_FUNCTIONS))}"
                )
            if func_name in ("PRIOR", "GROWTH"):
                if len(node.args) != 1 or not isinstance(node.args[0], ast.Name):
                    raise FormulaSyntaxError(
                        f"{func_name}() requires exactly one line item name argument."
                    )
                ref = node.args[0].id
                # PRIOR/GROWTH refs are NOT same-period dependencies
                if func_name == "PRIOR":
                    parsed.uses_prior = True
                else:
                    parsed.uses_growth = True
                    parsed.uses_prior = True
                return  # don't recurse into args

        elif isinstance(node, ast.Name):
            if node.id not in BUILTIN_FUNCTIONS:
                parsed.dependencies.add(node.id)
            return

        for child in ast.iter_child_nodes(node):
            self._validate_and_extract(child, parsed)


# ---------------------------------------------------------------------------
# DependencyGraph  (Kahn's algorithm, no external deps)
# ---------------------------------------------------------------------------

class DependencyGraph:
    def __init__(self):
        self._edges: dict[int, set[int]] = {}   # id -> set of ids it depends on
        self._nodes: set[int] = set()
        self._id_by_name: dict[str, int] = {}

    def build(self, line_items: list[LineItem], parsed: dict[int, ParsedFormula]):
        for li in line_items:
            self._nodes.add(li.id)
            self._id_by_name[li.name] = li.id
            self._edges[li.id] = set()

        for li in line_items:
            if li.id not in parsed:
                continue
            for dep_name in parsed[li.id].dependencies:
                dep_id = self._id_by_name.get(dep_name)
                if dep_id and dep_id != li.id:
                    self._edges[li.id].add(dep_id)

    def topological_sort(self) -> list[int]:
        """Kahn's BFS topological sort. Raises CircularReferenceError on cycles."""
        in_degree = {n: 0 for n in self._nodes}
        for node, deps in self._edges.items():
            for dep in deps:
                in_degree[node] = in_degree.get(node, 0) + 1

        # Recalculate properly
        in_degree = {n: 0 for n in self._nodes}
        for node in self._nodes:
            for dep in self._edges.get(node, set()):
                in_degree[node] += 1

        queue = [n for n in self._nodes if in_degree[n] == 0]
        sorted_ids = []

        while queue:
            node = queue.pop(0)
            sorted_ids.append(node)
            # find all nodes that depend on this node
            for other in self._nodes:
                if node in self._edges.get(other, set()):
                    in_degree[other] -= 1
                    if in_degree[other] == 0:
                        queue.append(other)

        if len(sorted_ids) != len(self._nodes):
            raise CircularReferenceError(
                "Circular reference detected in formula dependencies. "
                "Check your formulas for cycles."
            )

        return sorted_ids


# ---------------------------------------------------------------------------
# ActualsLoader
# ---------------------------------------------------------------------------

class ActualsLoader:
    def load(
        self,
        db: Session,
        account_id: int,
        time_periods: list[TimePeriod],
    ) -> dict[int, Decimal]:
        """Sum transactions for each time period. Returns {period_id: total}."""
        result: dict[int, Decimal] = {}
        for period in time_periods:
            total = (
                db.query(Transaction)
                .filter(
                    Transaction.account_id == account_id,
                    Transaction.date >= period.start_date,
                    Transaction.date <= period.end_date,
                )
                .all()
            )
            result[period.id] = Decimal(str(sum(t.amount or 0 for t in total)))
        return result


# ---------------------------------------------------------------------------
# Expression Evaluator (AST walker)
# ---------------------------------------------------------------------------

class _ExpressionEvaluator(ast.NodeVisitor):
    def __init__(
        self,
        value_map: dict[tuple[str, int], Decimal],
        current_period: TimePeriod,
        period_by_order: dict[int, TimePeriod],
    ):
        self._map = value_map
        self._period = current_period
        self._period_by_order = period_by_order

    def evaluate(self, node: ast.Expression) -> Decimal:
        return self.visit(node.body)

    def visit_Constant(self, node):
        return Decimal(str(node.value))

    def visit_Name(self, node):
        key = (node.id, self._period.id)
        return self._map.get(key, Decimal(0))

    def visit_UnaryOp(self, node):
        operand = self.visit(node.operand)
        if isinstance(node.op, ast.USub):
            return -operand
        return operand

    def visit_BinOp(self, node):
        left = self.visit(node.left)
        right = self.visit(node.right)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mul):
            return left * right
        if isinstance(node.op, ast.Div):
            return _safe_divide(left, right)
        raise FormulaSyntaxError(f"Unsupported operator: {type(node.op).__name__}")

    def visit_Compare(self, node):
        left = self.visit(node.left)
        results = []
        for op, comparator in zip(node.ops, node.comparators):
            right = self.visit(comparator)
            if isinstance(op, ast.Eq):
                results.append(left == right)
            elif isinstance(op, ast.NotEq):
                results.append(left != right)
            elif isinstance(op, ast.Lt):
                results.append(left < right)
            elif isinstance(op, ast.LtE):
                results.append(left <= right)
            elif isinstance(op, ast.Gt):
                results.append(left > right)
            elif isinstance(op, ast.GtE):
                results.append(left >= right)
        return Decimal(1) if all(results) else Decimal(0)

    def visit_BoolOp(self, node):
        if isinstance(node.op, ast.And):
            return Decimal(1) if all(self.visit(v) != 0 for v in node.values) else Decimal(0)
        return Decimal(1) if any(self.visit(v) != 0 for v in node.values) else Decimal(0)

    def visit_Call(self, node):
        func_name = node.func.id

        if func_name == "SUM":
            return sum((self.visit(a) for a in node.args), Decimal(0))

        if func_name == "AVG":
            vals = [self.visit(a) for a in node.args]
            return _safe_divide(sum(vals, Decimal(0)), Decimal(len(vals)))

        if func_name == "IF":
            cond, true_val, false_val = node.args
            return self.visit(true_val) if self.visit(cond) != 0 else self.visit(false_val)

        if func_name == "PRIOR":
            name = node.args[0].id
            prior_order = self._period.sort_order - 1
            prior_period = self._period_by_order.get(prior_order)
            if prior_period is None:
                return Decimal(0)
            return self._map.get((name, prior_period.id), Decimal(0))

        if func_name == "GROWTH":
            name = node.args[0].id
            prior_order = self._period.sort_order - 1
            prior_period = self._period_by_order.get(prior_order)
            if prior_period is None:
                return Decimal(0)
            current = self._map.get((name, self._period.id), Decimal(0))
            prior = self._map.get((name, prior_period.id), Decimal(0))
            return _safe_divide((current - prior) * 100, prior)

        raise FormulaSyntaxError(f"Unknown function: {func_name}")

    def generic_visit(self, node):
        raise FormulaSyntaxError(f"Unsupported AST node: {type(node).__name__}")


def _safe_divide(a: Decimal, b: Decimal) -> Decimal:
    try:
        return a / b if b != 0 else Decimal(0)
    except (DivisionByZero, InvalidOperation):
        return Decimal(0)


# ---------------------------------------------------------------------------
# Evaluator  (main engine)
# ---------------------------------------------------------------------------

class Evaluator:
    def __init__(self, db: Session, model_id: int, scenario_id: int):
        self.db = db
        self.model_id = model_id
        self.scenario_id = scenario_id

    def run(self) -> list[CellValue]:
        db = self.db
        scenario = db.query(Scenario).filter_by(id=self.scenario_id).first()
        line_items: list[LineItem] = (
            db.query(LineItem)
            .filter_by(model_id=self.model_id)
            .order_by(LineItem.sort_order)
            .all()
        )
        time_periods: list[TimePeriod] = (
            db.query(TimePeriod)
            .filter_by(model_id=self.model_id)
            .order_by(TimePeriod.sort_order)
            .all()
        )

        period_by_order = {p.sort_order: p for p in time_periods}
        id_by_name = {li.name: li.id for li in line_items}
        parser = FormulaParser()
        actuals_loader = ActualsLoader()

        # Parse all formulas
        parsed_formulas: dict[int, ParsedFormula] = {}
        parse_errors: dict[int, str] = {}
        for li in line_items:
            if li.item_type == LineItemType.formula and li.formula:
                try:
                    parsed_formulas[li.id] = parser.parse(li.formula)
                except FormulaSyntaxError as e:
                    parse_errors[li.id] = str(e)

        # Build dependency graph and sort
        graph = DependencyGraph()
        graph.build(line_items, parsed_formulas)
        try:
            sorted_ids = graph.topological_sort()
        except CircularReferenceError as e:
            # Fall back to sort_order; cells will show errors
            sorted_ids = [li.id for li in line_items]
            for li in line_items:
                parse_errors[li.id] = str(e)

        li_by_id = {li.id: li for li in line_items}
        sorted_items = [li_by_id[i] for i in sorted_ids if i in li_by_id]

        # Load existing manual cell values (inputs / overrides)
        existing_values: dict[tuple[int, int], CellValue] = {
            (cv.line_item_id, cv.time_period_id): cv
            for cv in db.query(CellValue).filter_by(scenario_id=self.scenario_id).all()
            if cv.line_item_id in {li.id for li in line_items}
        }

        # value_map: (line_item_name, period_id) -> Decimal
        value_map: dict[tuple[str, int], Decimal] = {}

        # Pre-populate from existing manual inputs
        for li in line_items:
            if li.item_type == LineItemType.input:
                if li.account_id and scenario and scenario.scenario_type == ScenarioType.actual:
                    actuals = actuals_loader.load(db, li.account_id, time_periods)
                    for period in time_periods:
                        value_map[(li.name, period.id)] = actuals.get(period.id, Decimal(0))
                else:
                    for period in time_periods:
                        cv = existing_values.get((li.id, period.id))
                        if cv and cv.value is not None:
                            value_map[(li.name, period.id)] = Decimal(str(cv.value))

        # Evaluate formula items in dependency order
        new_cell_values: list[dict] = []
        for li in sorted_items:
            if li.item_type == LineItemType.header:
                continue

            if li.item_type == LineItemType.input:
                # Already populated above; persist to DB
                for period in time_periods:
                    val = value_map.get((li.name, period.id))
                    new_cell_values.append({
                        "line_item_id": li.id,
                        "scenario_id": self.scenario_id,
                        "time_period_id": period.id,
                        "value": val,
                        "error_message": None,
                        "is_override": False,
                    })
                continue

            if li.item_type == LineItemType.formula:
                if li.id in parse_errors:
                    for period in time_periods:
                        new_cell_values.append({
                            "line_item_id": li.id,
                            "scenario_id": self.scenario_id,
                            "time_period_id": period.id,
                            "value": None,
                            "error_message": parse_errors[li.id],
                            "is_override": False,
                        })
                    continue

                pf = parsed_formulas.get(li.id)
                if not pf:
                    continue

                for period in time_periods:
                    # Respect manual overrides
                    cv = existing_values.get((li.id, period.id))
                    if cv and cv.is_override:
                        value_map[(li.name, period.id)] = Decimal(str(cv.value)) if cv.value is not None else Decimal(0)
                        new_cell_values.append({
                            "line_item_id": li.id,
                            "scenario_id": self.scenario_id,
                            "time_period_id": period.id,
                            "value": cv.value,
                            "error_message": None,
                            "is_override": True,
                        })
                        continue

                    try:
                        evaluator = _ExpressionEvaluator(value_map, period, period_by_order)
                        result = evaluator.evaluate(pf.ast_node)
                        value_map[(li.name, period.id)] = result
                        new_cell_values.append({
                            "line_item_id": li.id,
                            "scenario_id": self.scenario_id,
                            "time_period_id": period.id,
                            "value": float(result),
                            "error_message": None,
                            "is_override": False,
                        })
                    except Exception as e:
                        new_cell_values.append({
                            "line_item_id": li.id,
                            "scenario_id": self.scenario_id,
                            "time_period_id": period.id,
                            "value": None,
                            "error_message": str(e),
                            "is_override": False,
                        })

        # Bulk upsert
        from sqlalchemy.dialects.postgresql import insert as pg_insert
        if new_cell_values:
            stmt = pg_insert(CellValue).values(new_cell_values)
            stmt = stmt.on_conflict_do_update(
                constraint="uq_cell",
                set_={
                    "value": stmt.excluded.value,
                    "error_message": stmt.excluded.error_message,
                    "is_override": stmt.excluded.is_override,
                    "updated_at": stmt.excluded.updated_at,
                },
            )
            db.execute(stmt)
            db.commit()

        return db.query(CellValue).filter_by(scenario_id=self.scenario_id).all()
