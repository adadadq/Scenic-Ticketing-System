# Admin Product Breakdown CSV Export Design

## Scope

Add a synchronous CSV export endpoint:

`GET /api/admin/reports/product-breakdown.csv`

This slice exports the same product/ticket-type aggregation returned by `GET /api/admin/reports/product-breakdown`.

## In Scope

- Require an admin session.
- Use the same optional `dateFrom` and `dateTo` query parameters and `ADMIN_REPORT_DATE_RANGE_INVALID` error as the JSON endpoint.
- Return `text/csv; charset=utf-8` with `Content-Disposition`.
- CSV columns:
  - `productId`
  - `ticketTypeId`
  - `productName`
  - `ticketName`
  - `orderCount`
  - `ticketCount`
  - `soldTicketCount`
  - `checkedInTicketCount`
  - `refundedTicketCount`
  - `netPaidAmount`
- Do not expose buyer personal information, payment numbers, transaction numbers, session/CSRF data, password hashes, SQL, internal ids outside the public product/ticket identifiers, or audit details.
- Escape spreadsheet formula-like values in all CSV cells.

## Out Of Scope

- XLSX export.
- Async export jobs, export history, object storage, or download audit.
- Real financial settlement, fees, taxes, or payment-channel reconciliation.

## Testing

- API test covers CSV download, filename, date filters, admin-only access, no CSRF requirement, sensitive-field exclusion, and CSV headers.
- Service test covers spreadsheet cell escaping across all product breakdown export values.
- OpenAPI test covers file response, `Content-Disposition`, and date parameters.
- Milestone, security, contract, acceptance, README, and decision-log docs record the slice.
