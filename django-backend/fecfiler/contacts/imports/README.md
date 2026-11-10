# Contacts import prototype

Open Tools → Import in the local app. Download the example CSV, upload it, and
wait for validation. Only **Confirm import** creates contacts. Any invalid row
blocks the entire file. All valid rows are inserted in one transaction; a later
validation or database failure rolls back earlier rows. Existing contacts are
never matched or updated, and duplicate names/FEC IDs are intentionally allowed.
The regular contact API keeps its existing uniqueness validation.

## CSV

The downloadable `contacts-import-template.csv` includes all four types:
IND (individual), ORG (organization), COM (committee), and CAN (candidate).
Its 21 column names match the editable Contact fields. Columns can be reordered.
Optional columns can be omitted. Unknown/repeated/internal headers, incorrect
row lengths, and nonblank fields irrelevant to the row type are rejected.
Values are trimmed; blank cells become absent/null. All values remain strings,
preserving leading zeros in ZIP codes and House districts. UTF-8 with an optional
BOM is accepted. Limit: 1,000 rows and 10 MiB per upload.

All types need type, street_1, city, state, country. IND/CAN need first_name and
last_name; ORG/COM need name. COM needs committee_id; CAN needs candidate_id and
candidate_office (H/S/P). Senate requires candidate_state; House also requires
candidate_district. USA addresses require ZIP. Other rules come from the same
fecfile-validate contact schemas used by the app. Use ZZ for a foreign address
state, as the existing contact UI does. No automatic FEC lookup is performed.

## API and authorization

- POST /api/v1/contacts/imports/start/ — multipart `file`; returns an ImportJob.
- GET /api/v1/contacts/imports/{id}/ — status, totals, field errors, and preview.
- POST /api/v1/contacts/imports/{id}/confirm/ — confirm a valid preview once.
- POST /api/v1/contacts/imports/{id}/cancel/ — library cancellation action.

API access requires an authenticated administrator of the active committee and
FLAG__ENABLE_IMPORT. Committee/user IDs are assigned by the server and stored
in the job's resource arguments. Jobs are scoped to the active committee on
all actions. Workers recheck the creator's active administrator membership,
including committee enabled/not-deleted state. `force_import` and
`skip_parse_step` are rejected. The resource independently enforces transactions
and rollback on validation errors. Confirmation locks the job row to prevent
duplicate concurrent confirmations. CSV error row numbers include the header.
Preview responses show at most 100 rows; all rows are validated.

## Running locally

The API and worker images need requirements.txt dependencies, including
import-export-extensions 1.11.0 and import-export 4.4.5. Rebuild both images if
necessary. Run library migrations (`python -m django migrate
import_export_extensions --noinput`), then restart the API and Celery worker so
the library's tasks are registered. Redis/Celery must be running.

Uploads, job results, and error files are retained by the library. MEDIA_ROOT
is django-backend/.local/contact-imports, shared through the existing backend
bind mount between API and worker, and not publicly served. This filesystem
configuration is for the local prototype. A deployed API/worker pair needs a
shared private storage backend. Uploaded bytes are not included in logs by the
importer, and API responses exclude file URLs and tracebacks.

Preview old-job cleanup with `python -m django cleanup_contact_imports --days 7`.
Add `--delete` to delete eligible jobs and their files. Active jobs are excluded;
old unconfirmed previews are eligible. No automatic cleanup schedule is installed.

Run `python -m django test fecfiler.contacts.imports --noinput` for integration
tests. Those tests use a separate test database and temporary upload storage.
