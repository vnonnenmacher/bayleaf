# Exam Formula Format

This document defines the string-based format used in `ExamField.formula`.
The formula is an ordered list of rules; the first rule with a true condition
produces the result. If a rule has an empty condition, it is treated as true.

## Top-level shape

```json
[
  {
    "condition": "exam_field_result(135).exists",
    "result": "\"\""
  },
  {
    "condition": "",
    "result": "exam_field_result(135).numeric_value"
  }
]
```

- `condition`: string expression that returns true or false. Empty string means true.
- `result`: string expression that returns a value.

## References

### Analyte code results

```text
analyte_code_result(1).numeric_value
analyte_code_result(1).raw_value
analyte_code_result(1).units
```

### Exam field results

Default scope is the current `RequestedExam`:

```text
exam_field_result(135).numeric_value
exam_field_result(135).computed_value
exam_field_result(135).raw_value
exam_field_result(135).exists
```

Other `RequestedExam` in the same request:

```text
exam_field_result(135).numeric_value@requested_exam(42)
```

## Conditions

Conditions are boolean expressions composed of:

- Comparisons: `>`, `>=`, `<`, `<=`, `==`, `!=`
- Boolean operators: `and`, `or`, `not`
- Existence checks: `.exists` on references

Examples:

```text
exam_field_result(135).exists
exam_field_result(135).numeric_value > 10
analyte_code_result(1).numeric_value > 1 and analyte_code_result(2).exists
not exam_field_result(135).exists
```

## Result expressions

Result expressions support:

- Arithmetic: `+`, `-`, `*`, `/`, parentheses
- String literals: `"Positive"`, `"Nothing observed"`
- Numeric literals: `10`, `3.14`
- References (same as conditions)

Examples:

```text
analyte_code_result(1).numeric_value
(analyte_code_result(1).numeric_value * 10) + 2
"Nothing observed"
```

## Common formulas

### No condition, result: analyte_code_result(1).numeric_value

```json
[
  {
    "condition": "",
    "result": "analyte_code_result(1).numeric_value"
  }
]
```

### No condition, result: analyte_code_result(1).numeric_value - analyte_code_result(2).numeric_value

```json
[
  {
    "condition": "",
    "result": "analyte_code_result(1).numeric_value - analyte_code_result(2).numeric_value"
  }
]
```

### If analyte_code_result(1).numeric_value > 1 => "Positive", elif >= 1 => "Negative"

```json
[
  {
    "condition": "analyte_code_result(1).numeric_value > 1",
    "result": "\"Positive\""
  },
  {
    "condition": "analyte_code_result(1).numeric_value >= 1",
    "result": "\"Negative\""
  }
]
```

### No condition, result: "Nothing observed"

```json
[
  {
    "condition": "",
    "result": "\"Nothing observed\""
  }
]
```

### If analyte_code_result(1).exists => "", else analyte_code_result(1).numeric_value

```json
[
  {
    "condition": "analyte_code_result(1).exists",
    "result": "\"\""
  },
  {
    "condition": "",
    "result": "analyte_code_result(1).numeric_value"
  }
]
```
