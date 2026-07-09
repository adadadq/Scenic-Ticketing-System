# Admin Payment Reconciliation CSV Export Design

## Scope

Add a synchronous CSV export endpoint:

`GET /api/admin/reports/payment-reconciliation.csv`

This slice exports the same one-row reconciliation summary returned by `GET /api/admin/reports/payment-reconciliation`.

## In Scope

- Require an admin session.
- Use the same optional `dateFrom` and `dateTo` query parameters and `ADMIN_REPORT_DATE_RANGE_INVALID` error as the JSON endpoint.
- Return `text/csv; charset=utf-8` with `Content-Disposition`.
- CSV columns:
  - `dateFrom`
  - `dateTo`
  - `orderNetPaidAmount`
  - `capturedPaymentAmount`
  - `refundAuditAmount`
  - `expectedNetAmount`
  - `unreconciledAmount`
  - `capturedPaymentCount`
  - `refundAuditLogCount`
  - `reconciled`
- Do not expose payment numbers, transaction numbers, full phone numbers, identity numbers, session/CSRF data, password hashes, SQL, internal ids, or audit details.

## Out Of Scope

- XLSX export.
- Async export jobs, export history, object storage, or download audit.
- Real payment-channel settlement files, fees, taxes, and notification callbacks.

## Testing

- API test covers CSV download, filename, date filters, admin-only access, no CSRF requirement, sensitive-field exclusion, and CSV headers.
- Service test covers spreadsheet cell escaping across all export values.
- OpenAPI test covers file response, `Content-Disposition`, and date parameters.
- Milestone, security, contract, acceptance, README, and decision-log docs record the slice.
