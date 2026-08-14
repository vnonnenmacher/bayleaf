# Bayleaf API Endpoints

This is the implementation-level API contract for clients and agents. It reflects the URL configurations, views, serializers, permissions, and custom actions in this repository.

Base URL in local development: `http://localhost:8000`.

API paths below are relative to that base URL. Except where an endpoint is explicitly public, send a Simple JWT access token:

```http
Authorization: Bearer <access-token>
Content-Type: application/json
```

File uploads use `multipart/form-data`. JSON list responses from DRF viewsets and list views are normally paginated with a page size of 10:

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": []
}
```

Common errors are `400` for invalid input or an invalid transition, `401` for missing/invalid authentication, `403` for the wrong user type or organization, and `404` for a missing or out-of-scope object. DRF validation errors are usually keyed by field. UUIDs are strings; date-times are ISO 8601 strings.

## Authentication and current user

### `POST /api/users/login/`

Public. Obtain a normal JWT pair.

```json
{ "email": "person@example.com", "password": "secret" }
```

Response `200`:

```json
{ "refresh": "<refresh-token>", "access": "<access-token>" }
```

Invalid credentials return `401`.

### `POST /api/users/refresh/`

Public. Body: `{"refresh":"<refresh-token>"}`. Returns a new `access` token. Environments with refresh rotation enabled can also return a replacement `refresh` token.

### `POST /api/users/chat-token/`

Public. Exchanges email/password for a short-lived API token intended for agent/chat use.

```json
{ "email": "person@example.com", "password": "secret" }
```

Response `200`:

```json
{ "access_token": "<token>", "user_id": 12, "expires_in": 600 }
```

The token has audience `bayleaf-api`, scope `user.read`, and may contain `patient_id`. Invalid credentials return `401 {"detail":"invalid_credentials"}`. `expires_in` is configured per environment.

### `GET /api/users/me/type/`

Authenticated. Identifies the current account subtype.

```json
{
  "user_type": "professional",
  "ids": { "user_id": 12, "professional_did": "uuid" }
}
```

`user_type` is `professional`, `patient`, `relative`, or `null`. Patient IDs are returned as `patient_pid`.

## Shared profile shapes

Addresses are `{id, street, city, state, zip_code, country}`; contacts are `{id, phone_number, email}`; identifiers are `{type, value}`. Patient and professional profile writes accept nested `address1`, `address2`, `primary_contact`, `secondary_contact`, and `identifiers` objects.

A patient profile is:

```json
{
  "pid": "uuid",
  "first_name": "Ada",
  "last_name": "Lovelace",
  "birth_date": "1990-01-01",
  "email": "ada@example.com",
  "address1": null,
  "address2": null,
  "primary_contact": null,
  "secondary_contact": null,
  "identifiers": [],
  "avatar": null
}
```

`password` is accepted on create and is never returned.

A professional profile adds `did`, `role`, `role_id` (write-only), `bio`, `specializations`, and read-only `organizations`. A role is `{id,name,description}`, a specialization is `{id,name,description}`, and an organization is `{id,name,code,is_active}`.

## Patients

### `POST /api/patients/register/`

Public. Creates a patient. Required core fields are governed by the User model; send at least `first_name`, `last_name`, `email`, and `password`. Nested profile fields are optional. Returns the patient profile with `201`.

### `GET /api/patients/retrieve/`

Authenticated patient. Returns the current patient's profile.

### `GET|PUT|PATCH /api/patients/profile/`

Authenticated patient. Retrieves or updates the current patient's profile. PATCH is preferred for partial changes.

### `GET /api/patients/`

Authenticated. Paginated list of all patients. Optional `search` searches `first_name`, `last_name`, and `email`.

### `GET /api/patients/appointments/`

Authenticated patient. Optional appointment filters are `status`, `start_date`, and `end_date` (`YYYY-MM-DD`). Response is paginated, with a composite object inside `results`:

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": {
    "appointments": [{
      "id": 1,
      "scheduled_to": "2026-08-20T10:00:00Z",
      "duration_minutes": 30,
      "status": "CONFIRMED",
      "professional_did": "uuid",
      "patient": 12,
      "service": 2,
      "service_slot": 50
    }],
    "professionals": []
  }
}
```

A non-patient account receives `{"appointments":[],"professionals":[]}`.

### `GET /api/patients/appointments/next/`

Authenticated patient. Paginated future appointments excluding `CANCELED` and `COMPLETED`, earliest first.

## Relatives

Relatives are caregiver accounts that can manage relationships with patients. All relative endpoints except registration require a normal Bearer access token belonging to a `relative` user. A relationship is never deleted through this API; it is activated or deactivated with the toggle endpoint.

### Relative

```json
{
  "id": 20,
  "first_name": "Grace",
  "last_name": "Hopper",
  "email": "grace@example.com",
  "birth_date": "1980-01-01",
  "address1": {
    "id": 1,
    "street": "123 Main Street",
    "city": "Vancouver",
    "state": "BC",
    "zip_code": "V6B 1A1",
    "country": "Canada"
  },
  "address2": null,
  "primary_contact": {
    "id": 1,
    "phone_number": "+16045550100",
    "email": "grace@example.com"
  },
  "secondary_contact": null,
  "patient_links": []
}
```

`patient_links` is read-only. `password` is write-only and used only at registration. Nested address and contact objects may be created during registration or updated through the profile endpoint.

### Patient relationship

```json
{
  "id": 8,
  "patient": {
    "pid": "uuid",
    "first_name": "Alan",
    "last_name": "Turing",
    "email": "alan@example.com",
    "birth_date": "2010-01-01",
    "is_active": true
  },
  "active": true,
  "created_at": "ISO-8601 datetime"
}
```

The integer relationship `id` is used by the toggle endpoint. The patient's public `pid` is a UUID, but the existing-patient link endpoint currently accepts the patient's integer database ID as `patient_id`.

### `POST /api/patients/relatives/register/` — register a relative

Authentication: public.

Request:

```json
{
  "first_name": "Grace",
  "last_name": "Hopper",
  "email": "grace@example.com",
  "password": "secret123",
  "birth_date": "1980-01-01",
  "address1": {
    "street": "123 Main Street",
    "city": "Vancouver",
    "state": "BC",
    "zip_code": "V6B 1A1",
    "country": "Canada"
  },
  "primary_contact": {
    "phone_number": "+16045550100",
    "email": "grace@example.com"
  }
}
```

Required fields are `first_name`, `last_name`, `email`, and `password`. Password must contain at least six characters. `birth_date`, `address1`, `address2`, `primary_contact`, and `secondary_contact` are optional.

Response `201 Created`: the Relative shape above. The new account is active; `password` is omitted from the response. Duplicate email and field validation failures return `400`.

### `GET /api/patients/relatives/me/` — retrieve the logged-in relative

Authentication: relative JWT required.

Payload: none.

Response `200 OK`: the Relative shape, including every linked patient in `patient_links`, ordered with the newest relationship first. Example:

```json
{
  "id": 20,
  "first_name": "Grace",
  "last_name": "Hopper",
  "email": "grace@example.com",
  "birth_date": null,
  "address1": null,
  "address2": null,
  "primary_contact": null,
  "secondary_contact": null,
  "patient_links": [{
    "id": 8,
    "patient": {
      "pid": "uuid",
      "first_name": "Alan",
      "last_name": "Turing",
      "email": "noemail+...@placeholder.local",
      "birth_date": "2010-01-01",
      "is_active": false
    },
    "active": true,
    "created_at": "ISO-8601 datetime"
  }]
}
```

An authenticated user who is not a relative receives `403` with `{"detail":"Logged-in user is not a Relative."}`.

### `PUT /api/patients/relatives/me/` — replace the relative profile

Authentication: relative JWT required.

Accepts the same profile fields as registration except that `password` is ignored and `patient_links` is read-only. Because PUT is a full update, clients should send all fields they intend to retain. Response `200 OK`: updated Relative shape.

### `PATCH /api/patients/relatives/me/` — update the relative profile

Authentication: relative JWT required. Preferred for partial updates.

Example request:

```json
{
  "first_name": "Grace M.",
  "primary_contact": {
    "phone_number": "+16045550101"
  }
}
```

Only supplied scalar fields are changed. A supplied nested address/contact updates the existing nested object or creates it when absent. Omitting a nested field leaves it unchanged. Response `200 OK`: updated Relative shape.

### `POST /api/patients/relatives/me/patients/managed/` — create a managed patient

Authentication: relative JWT required.

Request:

```json
{
  "first_name": "Alan",
  "last_name": "Turing",
  "birth_date": "2010-01-01",
  "active": true
}
```

`first_name` and `last_name` are required. `birth_date` is optional/null; `active` defaults to `true`. Do not send `email`: the backend generates a unique `@placeholder.local` address.

Response `201 Created`: the Patient relationship shape. The created patient has `is_active: false` and an unusable password, so this managed record cannot log in. The relationship belongs to the authenticated relative.

Sending `email` returns `400` with `"Do not send 'email'—it is generated by the backend."` A non-relative caller returns `400` with `"Logged-in user is not a Relative."` from serializer validation.

### `POST /api/patients/relatives/me/patients/link/` — link an existing patient

Authentication: relative JWT required.

Request:

```json
{
  "patient_id": 12,
  "active": true
}
```

`patient_id` is required and is currently the patient's integer database primary key—not the UUID `pid`. `active` defaults to `true`.

Response `201 Created`: the Patient relationship shape. A nonexistent `patient_id` or an already-linked patient returns `400`; duplicate relationships are not reactivated automatically.

### `PATCH /api/patients/relatives/me/relationships/{relationship_id}/toggle-active/` — deactivate or reactivate a relationship

Authentication: owning relative JWT required.

Request to deactivate:

```json
{ "active": false }
```

Request to reactivate:

```json
{ "active": true }
```

Response `200 OK`:

```json
{ "id": 8, "active": false }
```

The path uses the integer relationship ID returned in `patient_links`, not a patient ID. The queryset is scoped to the logged-in relative, so another relative's relationship and unknown IDs return `404`.

### `PUT /api/patients/relatives/me/relationships/{relationship_id}/toggle-active/`

Authentication and behavior match PATCH. PUT requires the `active` field. PATCH is recommended because this resource exposes only one writable property.

## Professionals

### `POST /api/professionals/register/`

Public. Creates a professional using the shared professional profile shape. `role_id` assigns an existing role.

### `GET /api/professionals/retrieve/`

Authenticated professional. Returns the current professional profile.

### `GET|PUT|PATCH /api/professionals/profile/`

Authenticated professional. Retrieves or updates the current profile.

### `GET /api/professionals/list/` and `GET /api/professionals/list/{id}/`

Authenticated. Read-only professional directory. Filters: `role=<id>`, repeated `service_ids=<id>`, repeated `specialization_ids=<id>`, and `search=<text>` across name/email. Results are ordered by last name then first name.

### Professional-owned appointments

- `GET /api/professionals/appointments/` — current professional's appointments, newest scheduled time first; supports `status`, `start_date`, `end_date`.
- `GET /api/professionals/appointments/next/` — future appointments excluding `CANCELED` and `COMPLETED`, earliest first.

### Standard professional resource CRUD

All require authentication. Each router exposes `GET collection`, `POST collection`, `GET item`, `PUT/PATCH item`, and `DELETE item` unless stated otherwise.

| Resource | Paths | Shape / notes |
| --- | --- | --- |
| Shifts | `/api/professionals/shifts/`, `.../{id}/` | `{id,professional,weekday,service,slot_duration,from_time,to_time}`. Scoped to the current professional. Creating a shift generates service slots for the next four matching weekdays. |
| Roles | `/api/professionals/roles/`, `.../{id}/` | `{id,name,description}`. Global collection. |
| Specializations | `/api/professionals/specializations/`, `.../{id}/` | `{id,name,description}`. Global collection. |

## Services and health

### `GET /api/core/healthcheck/`

Public. Returns `200 {"status":"ok"}`.

### Service CRUD

Authenticated standard CRUD at `/api/core/services/` and `/api/core/services/{id}/`. Shape: `{id,name,code,description}`.

## Appointment discovery and booking

### `GET /api/appointments/available-slots/`

Public. Required repeated query parameter `services=<service-id>`. Optional `start_date` and `end_date` use `YYYY-MM-DD`; defaults are now through 30 days later. `page_size` is accepted up to 100.

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [{
    "id": 50,
    "shift_id": 5,
    "start_time": "ISO-8601 datetime",
    "end_time": "ISO-8601 datetime",
    "professional_id": 12,
    "service": {"id":2,"name":"Consultation"}
  }],
  "professionals": [{
    "id": 12,
    "first_name": "Ana",
    "last_name": "Silva",
    "email": "ana@example.com",
    "avatar": null
  }]
}
```

Booked, canceled-ineligible, and past slots are excluded. Invalid dates or missing services return `400`.

### `GET /api/appointments/available-specializations/`

Public. Supply both `start_date` and `end_date`, or neither. Returns specializations having availability; each contains at most four upcoming `slots`, each with `slot_id`, `shift_id`, times, `service_id`, and a nested `doctor`.

### `GET /api/appointments/available-professionals/`

Public. Date rules match the specializations endpoint. Returns professionals with basic profile fields and at most four upcoming slots.

### `POST /api/appointments/book/`

Authenticated patient. Body: `{"service_slot_id":50}`. The backend derives professional, service, time, and duration from the slot. Returns `201 {"id":<appointment-id>}`. Past/already-booked slots and non-patient callers return `400`.

### Appointment status actions

Authenticated. Empty request body.

| Endpoint | Allowed caller | New status |
| --- | --- | --- |
| `POST /api/appointments/{id}/confirm/` | assigned professional | `CONFIRMED` |
| `POST /api/appointments/{id}/initiate/` | assigned professional | `INITIATED` |
| `POST /api/appointments/{id}/complete/` | assigned professional | `COMPLETED` |
| `POST /api/appointments/{id}/cancel/` | assigned professional or patient | `CANCELED` |

The response is the appointment list shape. Invalid lifecycle transitions return `400`; a caller outside the appointment returns `403`; an unknown ID returns `404`.

## Documents

All document endpoints require a professional who belongs to an organization. Objects are strictly scoped to the first organization assigned to that professional.

Document shape:

```json
{
  "id": "uuid",
  "org": 1,
  "doc_key": "patient/uuid/report",
  "name": "Blood report",
  "reference": "minio://bucket/object-key",
  "mime_type": "application/pdf",
  "description": "",
  "tags": ["lab", "blood"],
  "size_bytes": 1234,
  "content_hash": "sha256",
  "created_by": 12,
  "created_at": "ISO-8601 datetime",
  "updated_at": "ISO-8601 datetime"
}
```

### `GET|POST /api/documents/`

GET filters: exact `doc_key`, prefix `search_doc_key`, case-insensitive `search_name`, exact `mime_type`, and repeated `tags` (all supplied tags must be present).

POST accepts either multipart `file` or an external `reference`. With a reference, `mime_type` is required. `name` is inferred from the filename/reference when omitted. Uploaded files populate `reference`, size, hash, and MIME type. The backend assigns `org` and `created_by`.

### `GET|PUT|PATCH|DELETE /api/documents/{uuid}/`

Reads, changes, or deletes an organization-scoped document. A replacement `file` can be supplied on update.

### `GET /api/documents/{uuid}/download-url/`

Returns `{"url":"...","expires_in":<seconds-or-null>}`. MinIO references become presigned URLs; external references are returned unchanged.

## Medications

Medication shape: `{id,name,description}`. Medication item shape:

```json
{
  "id": 4,
  "medication": {"id":2,"name":"Example","description":""},
  "dosage_amount": "1.00",
  "dosage_unit": {"id":1,"code":"TAB","name":"tablet"},
  "frequency_hours": 8,
  "instructions": "With food",
  "total_unit_amount": 21
}
```

### Medication catalog CRUD

Authenticated standard CRUD at `/api/medications/` and `/api/medications/{id}/`.

### `GET /api/medications/drug-search/?key=<text>`

Authenticated. Returns up to 20 medications whose name contains the key. Missing key returns `400`.

### `POST /api/medications/prescribe/`

Authenticated professional. Body:

```json
{
  "patient_uuid": "uuid",
  "medication": 2,
  "dosage_unit": "TAB",
  "dosage_amount": "1.00",
  "frequency_hours": 8,
  "total_unit_amount": 21
}
```

Returns `201 {"message":"Medication prescribed successfully","prescription_id":"uuid"}`. The dosage unit is looked up case-insensitively by code.

### Patient-owned medication items

- `GET /api/medications/my-medications/` — paginated current-patient items.
- `POST /api/medications/my-medications/add/` — creates a standalone item. Send the prescription fields above except `patient_uuid`, plus optional `instructions`, `first_dose_at`, and `window_minutes` (default 90). Scheduled medication events are generated.
- `GET|PUT|PATCH /api/medications/my-medications/{id}/` — current-patient item only. Schedule events are regenerated when frequency, total amount, or `first_dose_at` changes.
- `DELETE /api/medications/my-medications/{id}/` — removes the item and related pending events. Optional `delete_completed` controls completed event removal.

## Laboratory

Permissions: samples, sample types, and sample states require authentication. All other lab catalog and result resources require a professional. Standard CRUD means the usual collection/item methods. Samples are read-only except for the custom actions below. Exam requests intentionally do not support DELETE.

### Resource map

| Resource path | Shape |
| --- | --- |
| `/api/lab/samples/` | `{id,patient_uuid(write-only),sample_type,current_state,patient}` |
| `/api/lab/sample-types/` | `{id,name,description,created_at}` |
| `/api/lab/sample-states/` | `{id,name,description,created_at,is_initial_state,is_final_state,allowed_transitions, incoming_transitions, allowed_transitions_detail,incoming_transitions_detail}` |
| `/api/lab/measurement-units/` | `{id,name,code,description}` |
| `/api/lab/exams/` | `{id,name,code,description,material,is_active}` |
| `/api/lab/exam-versions/` | `{id,exam,version,is_active,notes,created_at,updated_at}`. Activating one deactivates other versions of the same exam. |
| `/api/lab/exam-fields/` | `{id,exam_version,name,code,priority,field_type,measurement_unit,formula,classification_rules,is_required,tag_ids(write-only),tags,created_at,updated_at}` |
| `/api/lab/tags/` | `{id,name,description,formula,created_at,updated_at}` |
| `/api/lab/exam-requests/` | See below. GET/POST/PUT/PATCH only. |
| `/api/lab/exam-field-results/` | `{id,requested_exam,exam_field,raw_value,computed_value,classification,classification_context,applied_tags,created_at,updated_at}` |
| `/api/lab/equipment-groups/` | `{id,name,description}` |
| `/api/lab/sectors/` | `{id,name,description}` |
| `/api/lab/equipments/` | `{id,code,name,group,manufacturer}` |
| `/api/lab/analytes/` | `{id,name,group,default_code}` |
| `/api/lab/analyte-codes/` | `{id,analyte,equipment,code,is_default,configuration}` |
| `/api/lab/analyte-results/` | `{id,analyte,equipment,sample,requested_exam,raw_value,numeric_value,units,metadata,created_at,updated_at}` |

Append `{id}/` for item operations on every standard CRUD resource.

### `POST /api/lab/samples/request_sample/`

Authenticated. Body: `{"patient_uuid":"uuid","sample_type":<id>}`. Creates a sample and its initial state transition. Returns `201` with `message`, `sample_id`, and simulated `transaction_hash`.

### `POST /api/lab/samples/{id}/update_sample_state/`

Authenticated. Body: `{"new_state_id":<id>}`. The transition must be configured in `AllowedStateTransition`. Returns the new state and transaction hash.

### Exam requests

Create at `POST /api/lab/exam-requests/`:

```json
{
  "code": "REQ-1023",
  "patient_uuid": "uuid",
  "notes": "Fasting sample",
  "exam_version_ids": [1, 2]
}
```

The response has `{id,code,notes,requested_exams,samples,is_validated,validated_by,canceled_at,canceled_by,cancel_reason,created_at,updated_at}`; each requested exam is `{id,exam_version,sample,is_completed,created_at,updated_at}`.

Cancel with `POST /api/lab/exam-requests/{id}/cancel/` and optional `{"cancel_reason":"..."}`. Invalid/repeated cancellation returns `400`.

Search with `GET /api/lab/exam-requests/search-exam-requests/`.

Filters:
- `code=<text>`: partial match on request code.
- `is_validated=true|false`.
- `sample_status=<id>` (supports repeated key and comma-separated values).
- `sample_status_name=<name>` (supports repeated key and comma-separated values).
- `is_completed=true|false`: returns only matching exams inside each sample.

Response is paginated and each row has:
- `request`: request metadata, validation info, requester, and patient (`pid`, first/last name, birth date).
- `samples`: each sample with sample type, current state, and `exams` list.
- `exams`: requested exam items with completion state and exam metadata. Exam result values are intentionally omitted.

### Search and injection actions

- `GET /api/lab/sectors/term-search/?term=<text>` and `GET /api/lab/equipments/term-search/?term=<text>` perform case-insensitive name search. Missing term returns `400`.
- `POST /api/lab/analyte-results/inject/` accepts `equipment_code`, `analyte_code`, `raw_result`, `sample_id`, and optional `numeric_value`, `units_code`, `metadata`. It resolves catalog mappings, injects/processes the result, and returns the analyte-result shape with `201`; semantic failures return `400 {"error":"..."}`.

## Care plans

Professional and agent API tokens have full access. Patients can read only their own plans, goals, actions, and reviews; modifying those resources returns `403`. Patients may read and update their own scheduled activity events. Professional reads are currently not organization-scoped.

All resources below are standard CRUD at both collection and `{id}/` paths:

| Resource | Base path | Main fields |
| --- | --- | --- |
| Care plan templates | `/api/careplans/templates/careplans/` | `id,name,summary,version,is_published,applicability_json,created_by,created_at,updated_at,goal_templates,activity_templates` |
| Goal templates | `/api/careplans/templates/goals/` | `id,template,title,description,target_metric_code,target_value,timeframe_days` |
| Action templates | `/api/careplans/templates/actions/` | `id,template,title,category,instructions_richtext,required_role,schedule_json,completion_criteria_json,code,order_index` |
| Care plans | `/api/careplans/careplans/` | `id,patient,template,status,start_date,end_date,owner,reason_codes,notes,created_at,updated_at` |
| Goals | `/api/careplans/goals/` | `id,careplan,template,title,target_metric_code,target_value_json,due_date,status,created_at,updated_at` |
| Actions | `/api/careplans/actions/` | `id,careplan,template,category,title,status,cancel_reason,completed_at,custom_instructions_richtext,schedule_json,assigned_to,extras,medication_detail,appointment_detail,created_at,updated_at` |
| Reviews | `/api/careplans/reviews/` | `id,careplan,reviewed_by,review_date,summary,outcome,changes_json` |
| Activity events | `/api/careplans/events/` | `id,action,scheduled_to,duration_minutes,event_type,description,status,created_at,created_by,rescheduled_to` |

Care plan create/update accepts nested `goals` and `actions`. A medication action requires `medication_detail`; an appointment action requires `appointment_detail`. Nested create merges template scheduling defaults with medication defaults and explicit `schedule_json`, then generates activity events. Retrieve returns the expanded plan tree (`goals`, `actions`, and `reviews`).

Updating an activity event's `status` enforces the event lifecycle and records status history. Writable event fields are `action`, `scheduled_to`, `duration_minutes`, `description`, and `status`.

### `GET /api/careplans/careplans/my/`

Authenticated patient or patient-scoped agent token. Returns an unpaginated array of the current patient's expanded care plans.

## Timeline

### `GET /api/timeline/timeline/`

Authenticated patient. Paginated timeline of appointments whose status is `CONFIRMED`, `INITIATED`, or `COMPLETED`, sorted oldest first.

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [{
    "type": "appointment",
    "title": "Appointment with Dr. Example Name",
    "when": "ISO-8601 datetime",
    "is_future": true,
    "reference_id": "1"
  }]
}
```

Professional callers receive an empty paginated response.

## Interactive schemas and non-API routes

- `GET /swagger/` — Swagger UI (public).
- `GET /swagger.json` or `/swagger.yaml` — generated schema (public).
- `GET /redoc/` — ReDoc UI (public).
- `/admin/` — Django administration site; staff/session authentication, not API JWT.

## Complete endpoint inventory

This inventory is a coverage checklist against every path explicitly mounted in the repository's URL configurations and every route generated by its DRF routers. `CRUD` means `GET` and `POST` on the collection plus `GET`, `PUT`, `PATCH`, and `DELETE` on `/{id}/`. Exceptions are stated explicitly.

| Area | Endpoint and methods |
| --- | --- |
| Users | `POST /api/users/login/` |
| Users | `POST /api/users/refresh/` |
| Users | `POST /api/users/chat-token/` |
| Users | `GET /api/users/me/type/` |
| Patients | `POST /api/patients/register/` |
| Patients | `GET /api/patients/retrieve/` |
| Patients | `GET`, `PUT`, `PATCH /api/patients/profile/` |
| Patients | `GET /api/patients/` |
| Patients | `GET /api/patients/appointments/` |
| Patients | `GET /api/patients/appointments/next/` |
| Relatives | `POST /api/patients/relatives/register/` |
| Relatives | `GET`, `PUT`, `PATCH /api/patients/relatives/me/` |
| Relatives | `POST /api/patients/relatives/me/patients/managed/` |
| Relatives | `POST /api/patients/relatives/me/patients/link/` |
| Relatives | `PUT`, `PATCH /api/patients/relatives/me/relationships/{id}/toggle-active/` |
| Professionals | `POST /api/professionals/register/` |
| Professionals | `GET /api/professionals/retrieve/` |
| Professionals | `GET`, `PUT`, `PATCH /api/professionals/profile/` |
| Professionals | `GET /api/professionals/appointments/` |
| Professionals | `GET /api/professionals/appointments/next/` |
| Professionals | Read-only `GET /api/professionals/list/` and `GET /api/professionals/list/{id}/` |
| Professionals | CRUD `/api/professionals/shifts/` |
| Professionals | CRUD `/api/professionals/roles/` |
| Professionals | CRUD `/api/professionals/specializations/` |
| Core | `GET /api/core/healthcheck/` |
| Core | CRUD `/api/core/services/` |
| Appointments | `GET /api/appointments/available-slots/` |
| Appointments | `GET /api/appointments/available-specializations/` |
| Appointments | `GET /api/appointments/available-professionals/` |
| Appointments | `POST /api/appointments/book/` |
| Appointments | `POST /api/appointments/{id}/confirm/` |
| Appointments | `POST /api/appointments/{id}/initiate/` |
| Appointments | `POST /api/appointments/{id}/complete/` |
| Appointments | `POST /api/appointments/{id}/cancel/` |
| Documents | `GET`, `POST /api/documents/` |
| Documents | `GET`, `PUT`, `PATCH`, `DELETE /api/documents/{uuid}/` |
| Documents | `GET /api/documents/{uuid}/download-url/` |
| Medications | CRUD `/api/medications/` |
| Medications | `GET /api/medications/drug-search/` |
| Medications | `POST /api/medications/prescribe/` |
| Medications | `GET /api/medications/my-medications/` |
| Medications | `POST /api/medications/my-medications/add/` |
| Medications | `GET`, `PUT`, `PATCH`, `DELETE /api/medications/my-medications/{id}/` |
| Lab | Read-only `GET /api/lab/samples/` and `GET /api/lab/samples/{id}/` |
| Lab | `POST /api/lab/samples/request_sample/` |
| Lab | `POST /api/lab/samples/{id}/update_sample_state/` |
| Lab | CRUD `/api/lab/sample-types/` |
| Lab | CRUD `/api/lab/sample-states/` |
| Lab | CRUD `/api/lab/measurement-units/` |
| Lab | CRUD `/api/lab/exams/` |
| Lab | CRUD `/api/lab/exam-versions/` |
| Lab | CRUD `/api/lab/exam-fields/` |
| Lab | CRUD `/api/lab/tags/` |
| Lab | `GET`, `POST /api/lab/exam-requests/`; `GET`, `PUT`, `PATCH /api/lab/exam-requests/{id}/` |
| Lab | `POST /api/lab/exam-requests/{id}/cancel/` |
| Lab | `GET /api/lab/exam-requests/search-exam-requests/` |
| Lab | CRUD `/api/lab/exam-field-results/` |
| Lab | CRUD `/api/lab/equipment-groups/` |
| Lab | CRUD `/api/lab/sectors/` |
| Lab | `GET /api/lab/sectors/term-search/` |
| Lab | CRUD `/api/lab/equipments/` |
| Lab | `GET /api/lab/equipments/term-search/` |
| Lab | CRUD `/api/lab/analytes/` |
| Lab | CRUD `/api/lab/analyte-codes/` |
| Lab | CRUD `/api/lab/analyte-results/` |
| Lab | `POST /api/lab/analyte-results/inject/` |
| Care plans | CRUD `/api/careplans/templates/careplans/` |
| Care plans | CRUD `/api/careplans/templates/goals/` |
| Care plans | CRUD `/api/careplans/templates/actions/` |
| Care plans | CRUD `/api/careplans/careplans/` |
| Care plans | `GET /api/careplans/careplans/my/` |
| Care plans | CRUD `/api/careplans/goals/` |
| Care plans | CRUD `/api/careplans/actions/` |
| Care plans | CRUD `/api/careplans/reviews/` |
| Care plans | CRUD `/api/careplans/events/` |
| Timeline | `GET /api/timeline/timeline/` |
| Schema/admin | `GET /swagger/`, `GET /swagger.json`, `GET /swagger.yaml`, `GET /redoc/`, `/admin/` |

## Known contract caveats

- Router actions use underscores exactly as generated: `request_sample` and `update_sample_state`.
- The README's older `/api/docs/` Swagger URL is not mounted; use `/swagger/`.
- The patient appointments endpoint has a nonstandard pagination payload: `results` is an object containing two arrays, not an array itself.
- `DELETE /api/medications/my-medications/{id}/?delete_completed=false` is interpreted as truthy by the current implementation because any non-empty query string is truthy. Omit the parameter to mean false.
- The timeline currently contains appointments only.
- Registration and nested update serializers do not provide a general password-change endpoint.
