import ast
import re

_REFERENCE_RE = re.compile(
    r"(analyte_code_result|exam_field_result)\((\d+)\)\.(\w+)(?:@requested_exam\((\d+)\))?"
)

_ANALYTE_FIELDS = {"numeric_value", "raw_value", "units", "exists"}
_EXAM_FIELD_FIELDS = {"numeric_value", "computed_value", "raw_value", "exists"}


class ExamFormulaValidator:
    """
    Validates formula structure and expression syntax without executing it.
    """

    def validate(self, formula) -> list[str]:
        errors: list[str] = []
        if not isinstance(formula, list):
            return ["Formula must be a list of rule objects."]

        for idx, rule in enumerate(formula):
            if not isinstance(rule, dict):
                errors.append(f"Rule {idx}: must be an object.")
                continue

            condition = rule.get("condition", "")
            result = rule.get("result")
            if condition is None:
                condition = ""

            if not isinstance(condition, str):
                errors.append(f"Rule {idx}: condition must be a string.")
            if not isinstance(result, str):
                errors.append(f"Rule {idx}: result must be a string.")

            if isinstance(condition, str) and condition:
                errors.extend(self._validate_expression(condition, idx, "condition"))
            if isinstance(result, str):
                errors.extend(self._validate_expression(result, idx, "result"))

        return errors

    def is_valid(self, formula) -> bool:
        return not self.validate(formula)

    def _validate_expression(self, expression: str, rule_index: int, label: str) -> list[str]:
        errors: list[str] = []
        errors.extend(self._validate_references(expression, rule_index, label))

        python_expression = _REFERENCE_RE.sub(self._reference_replacer, expression)
        try:
            parsed = ast.parse(python_expression, mode="eval")
        except SyntaxError:
            return [f"Rule {rule_index}: {label} has invalid syntax."]

        errors.extend(self._validate_ast(parsed.body, rule_index, label))
        return errors

    def _validate_references(self, expression: str, rule_index: int, label: str) -> list[str]:
        errors: list[str] = []
        for match in _REFERENCE_RE.finditer(expression):
            ref_type, _ref_id, field, _requested_exam_id = match.groups()
            if ref_type == "analyte_code_result" and field not in _ANALYTE_FIELDS:
                errors.append(
                    f"Rule {rule_index}: {label} uses invalid analyte_code_result field '{field}'."
                )
            if ref_type == "exam_field_result" and field not in _EXAM_FIELD_FIELDS:
                errors.append(
                    f"Rule {rule_index}: {label} uses invalid exam_field_result field '{field}'."
                )
        return errors

    def _reference_replacer(self, match: re.Match) -> str:
        ref_type, ref_id, field, requested_exam_id = match.groups()
        requested_exam_value = requested_exam_id or "None"
        return f"_ref('{ref_type}', {int(ref_id)}, '{field}', {requested_exam_value})"

    def _validate_ast(self, node: ast.AST, rule_index: int, label: str) -> list[str]:
        if isinstance(node, ast.Constant):
            return []
        if isinstance(node, ast.Name):
            if node.id in {"True", "False", "None"}:
                return []
            return [f"Rule {rule_index}: {label} uses unsupported name '{node.id}'."]
        if isinstance(node, ast.UnaryOp):
            if isinstance(node.op, (ast.Not, ast.UAdd, ast.USub)):
                return self._validate_ast(node.operand, rule_index, label)
            return [f"Rule {rule_index}: {label} uses unsupported unary operator."]
        if isinstance(node, ast.BoolOp):
            if not isinstance(node.op, (ast.And, ast.Or)):
                return [f"Rule {rule_index}: {label} uses unsupported boolean operator."]
            errors: list[str] = []
            for value in node.values:
                errors.extend(self._validate_ast(value, rule_index, label))
            return errors
        if isinstance(node, ast.Compare):
            errors = self._validate_ast(node.left, rule_index, label)
            for op, comparator in zip(node.ops, node.comparators):
                if not isinstance(op, (ast.Gt, ast.GtE, ast.Lt, ast.LtE, ast.Eq, ast.NotEq)):
                    errors.append(f"Rule {rule_index}: {label} uses unsupported comparison.")
                errors.extend(self._validate_ast(comparator, rule_index, label))
            return errors
        if isinstance(node, ast.BinOp):
            if not isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
                return [f"Rule {rule_index}: {label} uses unsupported arithmetic operator."]
            errors = self._validate_ast(node.left, rule_index, label)
            errors.extend(self._validate_ast(node.right, rule_index, label))
            return errors
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id != "_ref":
                return [f"Rule {rule_index}: {label} uses unsupported function call."]
            if len(node.args) != 4:
                return [f"Rule {rule_index}: {label} has malformed reference."]
            errors: list[str] = []
            for arg in node.args:
                errors.extend(self._validate_ast(arg, rule_index, label))
            return errors
        return [f"Rule {rule_index}: {label} contains unsupported syntax."]
