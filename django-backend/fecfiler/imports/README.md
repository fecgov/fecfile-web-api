# CSV report preview

`POST /api/v1/imports/` accepts a multipart field named `file` and returns JSON.
It requires a logged-in administrator of the active committee. Files are not
retained and no reports, forms, contacts, or transactions are saved.

The first two CSV records must be an eight-column `HDR,FEC,8.5,...` record and a
123-column F3XN, F3XA, or F3XT record. The field ordering comes from the existing
`web_services/dot_fec/schema_fields/HDR.json` and `F3X.json` export mappings.
This matches the supplied F3X monthly report export. Other versions and forms
are rejected; this is not a general .fec parser.

The response contains `header`, `report`, `saved: false`, and
`transactions_processed: false`. All source values remain strings, including
empty fields, dates in YYYYMMDD form, and monetary values. This is extraction,
not report schema validation or a payload approved for persistence. Later rows
are deliberately not parsed or validated. The filer committee ID is source data,
not an authorization or ownership instruction.

Uploads must be nonempty UTF-8 CSV (a BOM is accepted), at most 10 MiB. Malformed
header/report records return HTTP 400 with `file` errors. Django's normal upload
handling may spool larger uploads to temporary storage during the request; no
application file or job record is created. Deployment-level request limits and
Django upload handling still apply.
