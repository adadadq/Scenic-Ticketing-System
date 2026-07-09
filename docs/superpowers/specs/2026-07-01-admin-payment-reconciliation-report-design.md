# Admin Payment Reconciliation Report Design

## Scope

Add a read-only admin report endpoint:

`GET /api/admin/reports/payment-reconciliation`

This slice gives the backend and frontend a small financial reconciliation surface before real payment-channel integration. It compares existing order net paid amount with captured payment records minus refund audit logs for the same order-created date range.

## In Scope

- Require an admin session.
- Accept `dateFrom` and `dateTo` using the same order-created date filter as existing admin reports.
- Return:
  - `orderNetPaidAmount`
  - `capturedPaymentAmount`
  - `refundAuditAmount`
  - `expectedNetAmount`
  - `unreconciledAmount`
  - `capturedPaymentCount`
  - `refundAuditLogCount`
  - `reconciled`
- Count payment records whose status is `SUCCESS` or `REFUNDED`, because full refunds update the payment record to `REFUNDED` while the original captured amount still belongs in reconciliation.
- Keep the endpoint as a safe `GET`: no CSRF requirement, no mutation, no sensitive identifiers.

## Out Of Scope

- Real payment gateway settlement files.
- Channel transaction numbers in the admin DTO.
- Refund notification callbacks.
- Fee, commission, tax, and settlement date accounting.
- CSV/XLSX export or async export jobs.

## Testing

- API test covers admin access, date filters, DTO shape, and sensitive-field exclusion.
- API test covers missing admin session and invalid date range.
- Repository test covers parameterized SQL and `SUCCESS`/`REFUNDED` payment-record status inclusion.
- OpenAPI test covers the new path and query parameters.
- Milestone, security, contract, acceptance, README, and decision-log docs record the slice.
