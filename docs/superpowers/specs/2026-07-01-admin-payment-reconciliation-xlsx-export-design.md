# Admin Payment Reconciliation XLSX Export Design

## Scope

Add a synchronous XLSX export endpoint:

`GET /api/admin/reports/payment-reconciliation.xlsx`

This slice exports the same one-row reconciliation summary returned by `GET /api/admin/reports/payment-reconciliation` and the same columns used by the CSV export.

## In Scope

- Require an admin session.
- Use the same optional `dateFrom` and `dateTo` query parameters and `ADMIN_REPORT_DATE_RANGE_INVALID` error as the JSON and CSV endpoints.
- Return `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` with `Content-Disposition`.
- XLSX columns:
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
- Write workbook cells as inline strings, generate no formula nodes, and reuse XML 1.0 control-character cleanup.
- Do not expose payment numbers, transaction numbers, full phone numbers, identity numbers, session/CSRF data, password hashes, SQL, internal ids, or audit details.

## Out Of Scope

- Async export jobs, export history, object storage, or download audit.
- Real payment-channel settlement files, fees, taxes, and notification callbacks.
- Multi-sheet financial reconciliation workbooks.

## Testing

- API test covers XLSX download, filename, date filters, admin-only access, no CSRF requirement, sensitive-field exclusion, and workbook headers.
- Service test covers no formula nodes and XML-safe cell output for the payment reconciliation workbook.
- OpenAPI test covers file response, `Content-Disposition`, and date parameters.
- Milestone, security, contract, acceptance, README, and decision-log docs record the slice.
