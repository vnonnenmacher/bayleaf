import ast
import re

from lab.models import (
    AnalyteCode,
    AnalyteResult,
    ExamField,
    ExamFieldResult,
    ExamRequest,
    RequestedExam,
    Sample,
)

_MISSING = object()
_REFERENCE_RE = re.compile(
    r"(analyte_code_result|exam_field_result)\((\d+)\)\.(\w+)(?:@requested_exam\((\d+)\))?"
)


class ExamProcessor:
    """
    Orchestrates exam processing for requests and samples.
    """

    def compute_exam_request(self, exam_request: ExamRequest) -> None:
        """
        Compute all requested exams inside an exam request.
        """
        requested_exams = self._order_exams_(list(exam_request.requested_exams.all()))
        for requested_exam in requested_exams:
            self._compute_requested_exam(requested_exam)

    def compute_sample(self, sample: Sample) -> None:
        """
        Compute all requested exams within a sample.
        """
        requested_exams = self._order_exams_(list(sample.requested_exams.all()))
        for requested_exam in requested_exams:
            self._compute_requested_exam(requested_exam)

    def _order_exams_(self, requested_exam_list: list[RequestedExam]) -> list[RequestedExam]:
        """
        Returns an ordered list of requested exams for processing.
        """
        return sorted(requested_exam_list, key=lambda requested_exam: requested_exam.id)

    def _order_exam_fields(self, exam_fields_list: list[ExamField]) -> list[ExamField]:
        """
        Returns an ordered list of exam fields for processing.
        """
        ordered = self._topo_sort_exam_fields(exam_fields_list)
        if ordered is None:
            return sorted(exam_fields_list, key=lambda exam_field: (exam_field.priority, exam_field.id))
        return ordered

    def _compute_requested_exam(self, requested_exam: RequestedExam) -> None:
        """
        Compute a single requested exam, creating field results when possible.
        """
        exam_fields = self._order_exam_fields(list(requested_exam.exam_version.fields.all()))
        for exam_field in exam_fields:
            computed_value = self._evaluate_field_formula(exam_field, requested_exam)
            if computed_value is _MISSING:
                continue
            if computed_value is None:
                computed_str = None
            elif isinstance(computed_value, str):
                computed_str = computed_value
            else:
                computed_str = str(computed_value)
            ExamFieldResult.objects.update_or_create(
                requested_exam=requested_exam,
                exam_field=exam_field,
                defaults={"computed_value": computed_str},
            )

    def _topo_sort_exam_fields(self, exam_fields_list: list[ExamField]) -> list[ExamField] | None:
        field_map = {field.id: field for field in exam_fields_list}
        dependencies: dict[int, set[int]] = {field.id: set() for field in exam_fields_list}

        for field in exam_fields_list:
            for dep_id in self._extract_exam_field_dependencies(field.formula):
                if dep_id in field_map:
                    dependencies[field.id].add(dep_id)

        ordered: list[ExamField] = []
        ready = [field_id for field_id, deps in dependencies.items() if not deps]

        while ready:
            field_id = ready.pop()
            ordered.append(field_map[field_id])
            for other_id, deps in dependencies.items():
                if field_id in deps:
                    deps.remove(field_id)
                    if not deps:
                        ready.append(other_id)

        if len(ordered) != len(exam_fields_list):
            return None
        return ordered

    def _extract_exam_field_dependencies(self, formula) -> set[int]:
        if not formula or not isinstance(formula, list):
            return set()
        deps: set[int] = set()
        for rule in formula:
            for key in ("condition", "result"):
                expr = rule.get(key)
                if not isinstance(expr, str):
                    continue
                for match in _REFERENCE_RE.finditer(expr):
                    ref_type, ref_id, _field, requested_exam_id = match.groups()
                    if ref_type == "exam_field_result" and requested_exam_id is None:
                        deps.add(int(ref_id))
        return deps

    def _evaluate_field_formula(self, exam_field: ExamField, requested_exam: RequestedExam):
        formula = exam_field.formula
        if not formula or not isinstance(formula, list):
            return _MISSING

        for rule in formula:
            if not isinstance(rule, dict):
                continue
            condition_expr = rule.get("condition") or ""
            result_expr = rule.get("result")
            if not isinstance(result_expr, str):
                continue
            if condition_expr:
                condition_value = self._evaluate_expression(condition_expr, requested_exam)
                if condition_value is _MISSING:
                    return _MISSING
                if not isinstance(condition_value, bool):
                    return _MISSING
                if not condition_value:
                    continue
            result_value = self._evaluate_expression(result_expr, requested_exam)
            if result_value is _MISSING:
                return _MISSING
            return result_value

        return _MISSING

    def _evaluate_expression(self, expression: str, requested_exam: RequestedExam):
        python_expression = _REFERENCE_RE.sub(self._reference_replacer, expression)
        try:
            parsed = ast.parse(python_expression, mode="eval")
        except SyntaxError:
            return _MISSING
        return self._eval_ast(parsed.body, requested_exam)

    def _reference_replacer(self, match: re.Match) -> str:
        ref_type, ref_id, field, requested_exam_id = match.groups()
        requested_exam_value = requested_exam_id or "None"
        return f"_ref('{ref_type}', {int(ref_id)}, '{field}', {requested_exam_value})"

    def _eval_ast(self, node: ast.AST, requested_exam: RequestedExam):
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Name):
            if node.id == "True":
                return True
            if node.id == "False":
                return False
            if node.id == "None":
                return None
            return _MISSING
        if isinstance(node, ast.UnaryOp):
            operand = self._eval_ast(node.operand, requested_exam)
            if operand is _MISSING or operand is None:
                return _MISSING
            if isinstance(node.op, ast.Not):
                return not bool(operand)
            if isinstance(node.op, ast.UAdd):
                return +operand
            if isinstance(node.op, ast.USub):
                return -operand
            return _MISSING
        if isinstance(node, ast.BoolOp):
            if isinstance(node.op, ast.And):
                for value_node in node.values:
                    value = self._eval_ast(value_node, requested_exam)
                    if value is _MISSING or value is None:
                        return _MISSING
                    if not bool(value):
                        return False
                return True
            if isinstance(node.op, ast.Or):
                saw_missing = False
                for value_node in node.values:
                    value = self._eval_ast(value_node, requested_exam)
                    if value is _MISSING or value is None:
                        saw_missing = True
                        continue
                    if bool(value):
                        return True
                return _MISSING if saw_missing else False
            return _MISSING
        if isinstance(node, ast.Compare):
            left = self._eval_ast(node.left, requested_exam)
            if left is _MISSING or left is None:
                return _MISSING
            for op, comparator in zip(node.ops, node.comparators):
                right = self._eval_ast(comparator, requested_exam)
                if right is _MISSING or right is None:
                    return _MISSING
                if isinstance(op, ast.Gt):
                    ok = left > right
                elif isinstance(op, ast.GtE):
                    ok = left >= right
                elif isinstance(op, ast.Lt):
                    ok = left < right
                elif isinstance(op, ast.LtE):
                    ok = left <= right
                elif isinstance(op, ast.Eq):
                    ok = left == right
                elif isinstance(op, ast.NotEq):
                    ok = left != right
                else:
                    return _MISSING
                if not ok:
                    return False
                left = right
            return True
        if isinstance(node, ast.BinOp):
            left = self._eval_ast(node.left, requested_exam)
            right = self._eval_ast(node.right, requested_exam)
            if left is _MISSING or right is _MISSING or left is None or right is None:
                return _MISSING
            try:
                if isinstance(node.op, ast.Add):
                    return left + right
                if isinstance(node.op, ast.Sub):
                    return left - right
                if isinstance(node.op, ast.Mult):
                    return left * right
                if isinstance(node.op, ast.Div):
                    return left / right
            except (TypeError, ZeroDivisionError):
                return _MISSING
            return _MISSING
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id != "_ref":
                return _MISSING
            if len(node.args) != 4:
                return _MISSING
            ref_type = self._eval_ast(node.args[0], requested_exam)
            ref_id = self._eval_ast(node.args[1], requested_exam)
            field = self._eval_ast(node.args[2], requested_exam)
            requested_exam_id = self._eval_ast(node.args[3], requested_exam)
            if (
                ref_type is _MISSING
                or ref_id is _MISSING
                or field is _MISSING
                or requested_exam_id is _MISSING
            ):
                return _MISSING
            return self._resolve_reference(
                requested_exam=requested_exam,
                ref_type=str(ref_type),
                ref_id=int(ref_id),
                field=str(field),
                requested_exam_id=requested_exam_id,
            )
        return _MISSING

    def _resolve_reference(
        self,
        *,
        requested_exam: RequestedExam,
        ref_type: str,
        ref_id: int,
        field: str,
        requested_exam_id,
    ):
        if ref_type == "exam_field_result":
            return self._resolve_exam_field_result(
                requested_exam=requested_exam,
                exam_field_id=ref_id,
                field=field,
                requested_exam_id=requested_exam_id,
            )
        if ref_type == "analyte_code_result":
            return self._resolve_analyte_code_result(
                requested_exam=requested_exam,
                analyte_code_id=ref_id,
                field=field,
            )
        return _MISSING

    def _resolve_exam_field_result(
        self,
        *,
        requested_exam: RequestedExam,
        exam_field_id: int,
        field: str,
        requested_exam_id,
    ):
        target_exam = requested_exam
        if requested_exam_id is not None:
            target_exam = RequestedExam.objects.filter(
                id=requested_exam_id,
                exam_request=requested_exam.exam_request,
            ).first()
            if target_exam is None:
                return _MISSING

        result = ExamFieldResult.objects.filter(
            requested_exam=target_exam,
            exam_field_id=exam_field_id,
        ).first()

        if field == "exists":
            return result is not None
        if result is None:
            return _MISSING
        if field == "numeric_value":
            return self._coerce_numeric(result.computed_value or result.raw_value)
        if field == "computed_value":
            return result.computed_value
        if field == "raw_value":
            return result.raw_value
        return _MISSING

    def _resolve_analyte_code_result(
        self,
        *,
        requested_exam: RequestedExam,
        analyte_code_id: int,
        field: str,
    ):
        analyte_code = AnalyteCode.objects.filter(id=analyte_code_id).first()
        if analyte_code is None:
            return _MISSING
        if not requested_exam.sample_id:
            return _MISSING
        analyte_result = AnalyteResult.objects.filter(
            sample_id=requested_exam.sample_id,
            analyte=analyte_code.analyte,
            equipment=analyte_code.equipment,
        ).order_by("id").first()

        if field == "exists":
            return analyte_result is not None
        if analyte_result is None:
            return _MISSING
        if field == "numeric_value":
            return analyte_result.numeric_value
        if field == "raw_value":
            return analyte_result.raw_value
        if field == "units":
            return analyte_result.units.code if analyte_result.units else None
        return _MISSING

    def _coerce_numeric(self, value):
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
