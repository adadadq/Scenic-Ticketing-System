from datetime import date

from fastapi import APIRouter, Depends, Query, Request, Response

from app.core.responses import success_response
from app.schemas.common import ApiSuccessDTO
from app.schemas.orders import (
    AdminDailyTrendDTO,
    AdminHourlyTrendDTO,
    AdminMonthlyTrendDTO,
    AdminPaymentReconciliationDTO,
    AdminProductBreakdownDTO,
    AdminReportSummaryDTO,
)
from app.services.orders import AdminReportService, get_admin_report_service

router = APIRouter(prefix="/api/admin/reports", tags=["admin-reports"])


@router.get(
    "/summary",
    response_model=ApiSuccessDTO[AdminReportSummaryDTO],
    response_model_exclude_none=True,
)
def get_admin_report_summary(
    request: Request,
    date_from: date | None = Query(default=None, alias="dateFrom"),
    date_to: date | None = Query(default=None, alias="dateTo"),
    admin_report_service: AdminReportService = Depends(get_admin_report_service),
) -> dict:
    summary = admin_report_service.get_summary(request=request, date_from=date_from, date_to=date_to)
    return success_response(request, summary.model_dump(by_alias=True, mode="json"))


@router.get(
    "/payment-reconciliation",
    response_model=ApiSuccessDTO[AdminPaymentReconciliationDTO],
    response_model_exclude_none=True,
)
def get_admin_payment_reconciliation(
    request: Request,
    date_from: date | None = Query(default=None, alias="dateFrom"),
    date_to: date | None = Query(default=None, alias="dateTo"),
    admin_report_service: AdminReportService = Depends(get_admin_report_service),
) -> dict:
    reconciliation = admin_report_service.get_payment_reconciliation(
        request=request,
        date_from=date_from,
        date_to=date_to,
    )
    return success_response(request, reconciliation.model_dump(by_alias=True, mode="json"))


@router.get(
    "/payment-reconciliation.csv",
    response_class=Response,
    responses={
        200: {
            "description": "Admin payment reconciliation CSV export",
            "headers": {
                "Content-Disposition": {
                    "description": "Attachment filename for the generated payment reconciliation CSV",
                    "schema": {"type": "string"},
                }
            },
            "content": {
                "text/csv": {
                    "schema": {
                        "type": "string",
                        "format": "binary",
                    }
                }
            },
        }
    },
)
def export_admin_payment_reconciliation_csv(
    request: Request,
    date_from: date | None = Query(default=None, alias="dateFrom"),
    date_to: date | None = Query(default=None, alias="dateTo"),
    admin_report_service: AdminReportService = Depends(get_admin_report_service),
) -> Response:
    csv_text = admin_report_service.export_payment_reconciliation_csv(
        request=request,
        date_from=date_from,
        date_to=date_to,
    )
    filename = admin_report_service.payment_reconciliation_export_filename(
        date_from=date_from,
        date_to=date_to,
    )
    return Response(
        content=csv_text.encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/payment-reconciliation.xlsx",
    response_class=Response,
    responses={
        200: {
            "description": "Admin payment reconciliation XLSX export",
            "headers": {
                "Content-Disposition": {
                    "description": "Attachment filename for the generated payment reconciliation workbook",
                    "schema": {"type": "string"},
                }
            },
            "content": {
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {
                    "schema": {
                        "type": "string",
                        "format": "binary",
                    }
                }
            },
        }
    },
)
def export_admin_payment_reconciliation_xlsx(
    request: Request,
    date_from: date | None = Query(default=None, alias="dateFrom"),
    date_to: date | None = Query(default=None, alias="dateTo"),
    admin_report_service: AdminReportService = Depends(get_admin_report_service),
) -> Response:
    xlsx_bytes = admin_report_service.export_payment_reconciliation_xlsx(
        request=request,
        date_from=date_from,
        date_to=date_to,
    )
    filename = admin_report_service.payment_reconciliation_export_xlsx_filename(
        date_from=date_from,
        date_to=date_to,
    )
    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/product-breakdown",
    response_model=ApiSuccessDTO[list[AdminProductBreakdownDTO]],
    response_model_exclude_none=True,
)
def list_admin_product_breakdown(
    request: Request,
    date_from: date | None = Query(default=None, alias="dateFrom"),
    date_to: date | None = Query(default=None, alias="dateTo"),
    admin_report_service: AdminReportService = Depends(get_admin_report_service),
) -> dict:
    rows = admin_report_service.list_product_breakdown(request=request, date_from=date_from, date_to=date_to)
    return success_response(request, [row.model_dump(by_alias=True, mode="json") for row in rows])


@router.get(
    "/product-breakdown.csv",
    response_class=Response,
    responses={
        200: {
            "description": "Admin product breakdown CSV export",
            "headers": {
                "Content-Disposition": {
                    "description": "Attachment filename for the generated product breakdown CSV",
                    "schema": {"type": "string"},
                }
            },
            "content": {
                "text/csv": {
                    "schema": {
                        "type": "string",
                        "format": "binary",
                    }
                }
            },
        }
    },
)
def export_admin_product_breakdown_csv(
    request: Request,
    date_from: date | None = Query(default=None, alias="dateFrom"),
    date_to: date | None = Query(default=None, alias="dateTo"),
    admin_report_service: AdminReportService = Depends(get_admin_report_service),
) -> Response:
    csv_text = admin_report_service.export_product_breakdown_csv(
        request=request,
        date_from=date_from,
        date_to=date_to,
    )
    filename = admin_report_service.product_breakdown_export_filename(
        date_from=date_from,
        date_to=date_to,
    )
    return Response(
        content=csv_text.encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/product-breakdown.xlsx",
    response_class=Response,
    responses={
        200: {
            "description": "Admin product breakdown XLSX export",
            "headers": {
                "Content-Disposition": {
                    "description": "Attachment filename for the generated product breakdown workbook",
                    "schema": {"type": "string"},
                }
            },
            "content": {
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {
                    "schema": {
                        "type": "string",
                        "format": "binary",
                    }
                }
            },
        }
    },
)
def export_admin_product_breakdown_xlsx(
    request: Request,
    date_from: date | None = Query(default=None, alias="dateFrom"),
    date_to: date | None = Query(default=None, alias="dateTo"),
    admin_report_service: AdminReportService = Depends(get_admin_report_service),
) -> Response:
    xlsx_bytes = admin_report_service.export_product_breakdown_xlsx(
        request=request,
        date_from=date_from,
        date_to=date_to,
    )
    filename = admin_report_service.product_breakdown_export_xlsx_filename(
        date_from=date_from,
        date_to=date_to,
    )
    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/daily-trend",
    response_model=ApiSuccessDTO[list[AdminDailyTrendDTO]],
    response_model_exclude_none=True,
)
def list_admin_daily_trend(
    request: Request,
    date_from: date | None = Query(default=None, alias="dateFrom"),
    date_to: date | None = Query(default=None, alias="dateTo"),
    include_empty: bool = Query(default=False, alias="includeEmpty"),
    admin_report_service: AdminReportService = Depends(get_admin_report_service),
) -> dict:
    rows = admin_report_service.list_daily_trend(
        request=request,
        date_from=date_from,
        date_to=date_to,
        include_empty=include_empty,
    )
    return success_response(request, [row.model_dump(by_alias=True, mode="json") for row in rows])


@router.get(
    "/daily-trend.csv",
    response_class=Response,
    responses={
        200: {
            "description": "Admin daily trend CSV export",
            "headers": {
                "Content-Disposition": {
                    "description": "Attachment filename for the generated daily trend CSV",
                    "schema": {"type": "string"},
                }
            },
            "content": {
                "text/csv": {
                    "schema": {
                        "type": "string",
                        "format": "binary",
                    }
                }
            },
        }
    },
)
def export_admin_daily_trend_csv(
    request: Request,
    date_from: date | None = Query(default=None, alias="dateFrom"),
    date_to: date | None = Query(default=None, alias="dateTo"),
    include_empty: bool = Query(default=False, alias="includeEmpty"),
    admin_report_service: AdminReportService = Depends(get_admin_report_service),
) -> Response:
    csv_text = admin_report_service.export_daily_trend_csv(
        request=request,
        date_from=date_from,
        date_to=date_to,
        include_empty=include_empty,
    )
    filename = admin_report_service.trend_export_filename(
        trend="daily",
        date_from=date_from,
        date_to=date_to,
    )
    return Response(
        content=csv_text.encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/daily-trend.xlsx",
    response_class=Response,
    responses={
        200: {
            "description": "Admin daily trend XLSX export",
            "headers": {
                "Content-Disposition": {
                    "description": "Attachment filename for the generated daily trend workbook",
                    "schema": {"type": "string"},
                }
            },
            "content": {
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {
                    "schema": {
                        "type": "string",
                        "format": "binary",
                    }
                }
            },
        }
    },
)
def export_admin_daily_trend_xlsx(
    request: Request,
    date_from: date | None = Query(default=None, alias="dateFrom"),
    date_to: date | None = Query(default=None, alias="dateTo"),
    include_empty: bool = Query(default=False, alias="includeEmpty"),
    admin_report_service: AdminReportService = Depends(get_admin_report_service),
) -> Response:
    xlsx_bytes = admin_report_service.export_daily_trend_xlsx(
        request=request,
        date_from=date_from,
        date_to=date_to,
        include_empty=include_empty,
    )
    filename = admin_report_service.trend_export_xlsx_filename(
        trend="daily",
        date_from=date_from,
        date_to=date_to,
    )
    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/hourly-trend",
    response_model=ApiSuccessDTO[list[AdminHourlyTrendDTO]],
    response_model_exclude_none=True,
)
def list_admin_hourly_trend(
    request: Request,
    date_from: date | None = Query(default=None, alias="dateFrom"),
    date_to: date | None = Query(default=None, alias="dateTo"),
    include_empty: bool = Query(default=False, alias="includeEmpty"),
    admin_report_service: AdminReportService = Depends(get_admin_report_service),
) -> dict:
    rows = admin_report_service.list_hourly_trend(
        request=request,
        date_from=date_from,
        date_to=date_to,
        include_empty=include_empty,
    )
    return success_response(request, [row.model_dump(by_alias=True, mode="json") for row in rows])


@router.get(
    "/hourly-trend.csv",
    response_class=Response,
    responses={
        200: {
            "description": "Admin hourly trend CSV export",
            "headers": {
                "Content-Disposition": {
                    "description": "Attachment filename for the generated hourly trend CSV",
                    "schema": {"type": "string"},
                }
            },
            "content": {
                "text/csv": {
                    "schema": {
                        "type": "string",
                        "format": "binary",
                    }
                }
            },
        }
    },
)
def export_admin_hourly_trend_csv(
    request: Request,
    date_from: date | None = Query(default=None, alias="dateFrom"),
    date_to: date | None = Query(default=None, alias="dateTo"),
    include_empty: bool = Query(default=False, alias="includeEmpty"),
    admin_report_service: AdminReportService = Depends(get_admin_report_service),
) -> Response:
    csv_text = admin_report_service.export_hourly_trend_csv(
        request=request,
        date_from=date_from,
        date_to=date_to,
        include_empty=include_empty,
    )
    filename = admin_report_service.trend_export_filename(
        trend="hourly",
        date_from=date_from,
        date_to=date_to,
    )
    return Response(
        content=csv_text.encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/hourly-trend.xlsx",
    response_class=Response,
    responses={
        200: {
            "description": "Admin hourly trend XLSX export",
            "headers": {
                "Content-Disposition": {
                    "description": "Attachment filename for the generated hourly trend workbook",
                    "schema": {"type": "string"},
                }
            },
            "content": {
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {
                    "schema": {
                        "type": "string",
                        "format": "binary",
                    }
                }
            },
        }
    },
)
def export_admin_hourly_trend_xlsx(
    request: Request,
    date_from: date | None = Query(default=None, alias="dateFrom"),
    date_to: date | None = Query(default=None, alias="dateTo"),
    include_empty: bool = Query(default=False, alias="includeEmpty"),
    admin_report_service: AdminReportService = Depends(get_admin_report_service),
) -> Response:
    xlsx_bytes = admin_report_service.export_hourly_trend_xlsx(
        request=request,
        date_from=date_from,
        date_to=date_to,
        include_empty=include_empty,
    )
    filename = admin_report_service.trend_export_xlsx_filename(
        trend="hourly",
        date_from=date_from,
        date_to=date_to,
    )
    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/monthly-trend",
    response_model=ApiSuccessDTO[list[AdminMonthlyTrendDTO]],
    response_model_exclude_none=True,
)
def list_admin_monthly_trend(
    request: Request,
    date_from: date | None = Query(default=None, alias="dateFrom"),
    date_to: date | None = Query(default=None, alias="dateTo"),
    include_empty: bool = Query(default=False, alias="includeEmpty"),
    admin_report_service: AdminReportService = Depends(get_admin_report_service),
) -> dict:
    rows = admin_report_service.list_monthly_trend(
        request=request,
        date_from=date_from,
        date_to=date_to,
        include_empty=include_empty,
    )
    return success_response(request, [row.model_dump(by_alias=True, mode="json") for row in rows])


@router.get(
    "/monthly-trend.csv",
    response_class=Response,
    responses={
        200: {
            "description": "Admin monthly trend CSV export",
            "headers": {
                "Content-Disposition": {
                    "description": "Attachment filename for the generated monthly trend CSV",
                    "schema": {"type": "string"},
                }
            },
            "content": {
                "text/csv": {
                    "schema": {
                        "type": "string",
                        "format": "binary",
                    }
                }
            },
        }
    },
)
def export_admin_monthly_trend_csv(
    request: Request,
    date_from: date | None = Query(default=None, alias="dateFrom"),
    date_to: date | None = Query(default=None, alias="dateTo"),
    include_empty: bool = Query(default=False, alias="includeEmpty"),
    admin_report_service: AdminReportService = Depends(get_admin_report_service),
) -> Response:
    csv_text = admin_report_service.export_monthly_trend_csv(
        request=request,
        date_from=date_from,
        date_to=date_to,
        include_empty=include_empty,
    )
    filename = admin_report_service.trend_export_filename(
        trend="monthly",
        date_from=date_from,
        date_to=date_to,
    )
    return Response(
        content=csv_text.encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/monthly-trend.xlsx",
    response_class=Response,
    responses={
        200: {
            "description": "Admin monthly trend XLSX export",
            "headers": {
                "Content-Disposition": {
                    "description": "Attachment filename for the generated monthly trend workbook",
                    "schema": {"type": "string"},
                }
            },
            "content": {
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {
                    "schema": {
                        "type": "string",
                        "format": "binary",
                    }
                }
            },
        }
    },
)
def export_admin_monthly_trend_xlsx(
    request: Request,
    date_from: date | None = Query(default=None, alias="dateFrom"),
    date_to: date | None = Query(default=None, alias="dateTo"),
    include_empty: bool = Query(default=False, alias="includeEmpty"),
    admin_report_service: AdminReportService = Depends(get_admin_report_service),
) -> Response:
    xlsx_bytes = admin_report_service.export_monthly_trend_xlsx(
        request=request,
        date_from=date_from,
        date_to=date_to,
        include_empty=include_empty,
    )
    filename = admin_report_service.trend_export_xlsx_filename(
        trend="monthly",
        date_from=date_from,
        date_to=date_to,
    )
    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/orders.csv",
    response_class=Response,
    responses={
        200: {
            "description": "Admin order CSV export",
            "content": {
                "text/csv": {
                    "schema": {
                        "type": "string",
                        "format": "binary",
                    }
                }
            },
        }
    },
)
def export_admin_orders_csv(
    request: Request,
    date_from: date | None = Query(default=None, alias="dateFrom"),
    date_to: date | None = Query(default=None, alias="dateTo"),
    admin_report_service: AdminReportService = Depends(get_admin_report_service),
) -> Response:
    csv_text = admin_report_service.export_orders_csv(request=request, date_from=date_from, date_to=date_to)
    filename = admin_report_service.order_export_filename(date_from=date_from, date_to=date_to)
    return Response(
        content=csv_text.encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/orders.xlsx",
    response_class=Response,
    responses={
        200: {
            "description": "Admin order XLSX export",
            "headers": {
                "Content-Disposition": {
                    "description": "Attachment filename for the generated order workbook",
                    "schema": {"type": "string"},
                }
            },
            "content": {
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {
                    "schema": {
                        "type": "string",
                        "format": "binary",
                    }
                }
            },
        }
    },
)
def export_admin_orders_xlsx(
    request: Request,
    date_from: date | None = Query(default=None, alias="dateFrom"),
    date_to: date | None = Query(default=None, alias="dateTo"),
    admin_report_service: AdminReportService = Depends(get_admin_report_service),
) -> Response:
    xlsx_bytes = admin_report_service.export_orders_xlsx(request=request, date_from=date_from, date_to=date_to)
    filename = admin_report_service.order_export_xlsx_filename(date_from=date_from, date_to=date_to)
    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
