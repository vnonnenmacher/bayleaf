# Plan: Lab Search Exam Requests Endpoint

## Goal
Add backend support for a frontend request/sample/exam listing flow with strong filtering and enriched payloads for lab requests.

## Scope
1. Add new fields to exam requests:
- `code` (request code provided at creation time)
- `is_validated` (boolean)
- `validated_by` (professional)

2. Add endpoint:
- `GET /api/lab/exam-requests/search-exam-requests/`

3. Response tree:
- request
- sample
- exams (list items, no exam field result payload)

4. Filtering behavior:
- Request-level filters:
  - `code` (exact or partial)
  - `is_validated` (true/false)
- Sample-level filters:
  - `sample_status` by current sample state id(s) and/or `sample_status_name` by state name(s)
- Exam-level filters:
  - `is_completed` (true/false), pruning exam lists to matching items only

## Proposed Endpoint Contract
`GET /api/lab/exam-requests/search-exam-requests/`

### Query params
- `code`: partial match on request code
- `is_validated`: `true|false|1|0|yes|no`
- `sample_status`: state id list (`1,2` or repeated key)
- `sample_status_name`: state name list (`Requested,Processing` or repeated key)
- `is_completed`: `true|false|1|0|yes|no`

### Response shape
```json
[
  {
    "request": {
      "id": 1,
      "code": "REQ-1023",
      "notes": "Fasting",
      "created_at": "...",
      "is_validated": false,
      "validated_by": null,
      "requested_by": {
        "id": "uuid",
        "full_name": "Pro User"
      },
      "patient": {
        "pid": "uuid",
        "first_name": "Pat",
        "last_name": "Ent",
        "birth_date": "2000-01-01"
      }
    },
    "samples": [
      {
        "id": "uuid",
        "sample_type": {
          "id": 1,
          "name": "Blood"
        },
        "current_state": {
          "id": 2,
          "name": "Processing"
        },
        "exams": [
          {
            "requested_exam_id": 10,
            "is_completed": true,
            "exam_version_id": 4,
            "exam": {
              "id": 3,
              "code": "GLU",
              "name": "Glucose",
              "sector": null
            }
          }
        ]
      }
    ]
  }
]
```

## Implementation Steps
1. Model + migration:
- Add `code`, `is_validated`, `validated_by` in `ExamRequest`.

2. Serializer updates:
- Include `code` as a required write field on exam request creation.
- Expose `is_validated` and `validated_by` as read-only fields.
- Include `is_completed` in requested exam serializer output.

3. Viewset action:
- Add `search_exam_requests` action in `ExamRequestViewSet`.
- Implement typed query param parsing and robust filter handling.
- Build response tree and prune exams when `is_completed` filter is present.

4. Tests:
- Add endpoint tests for:
  - auth/permission
  - `is_completed` filtering with tree pruning
  - sample status filtering
  - response payload fields

5. API docs:
- Update lab section in `ENDPOINTS.md`.

## Notes
- Current model does not define a direct relation between exam and `Sector`; response will include `sector: null` placeholder until a relationship is introduced.
- Endpoint intentionally omits exam field result values for list performance and payload size.
