import { useRef, useState } from 'react'
import type { AdminReportParams, AdminTrendReportParams } from '../../shared/api/types'
import {
  downloadAdminOrdersCsv,
  downloadAdminOrdersXlsx,
  downloadAdminPaymentReconciliationCsv,
  downloadAdminPaymentReconciliationXlsx,
  downloadAdminProductBreakdownCsv,
  downloadAdminProductBreakdownXlsx,
  downloadAdminTrendCsv,
  downloadAdminTrendXlsx,
  type AdminTrendCsvKind,
} from './exportCsv'

type UseAdminReportExportsOptions = {
  reportParams: AdminReportParams
  trendReportParams: AdminTrendReportParams
}

export function useAdminReportExports({ reportParams, trendReportParams }: UseAdminReportExportsOptions) {
  const [ordersCsvError, setOrdersCsvError] = useState<unknown>(null)
  const [ordersXlsxError, setOrdersXlsxError] = useState<unknown>(null)
  const [paymentReconciliationCsvError, setPaymentReconciliationCsvError] = useState<unknown>(null)
  const [paymentReconciliationXlsxError, setPaymentReconciliationXlsxError] = useState<unknown>(null)
  const [productBreakdownCsvError, setProductBreakdownCsvError] = useState<unknown>(null)
  const [productBreakdownXlsxError, setProductBreakdownXlsxError] = useState<unknown>(null)
  const [trendCsvError, setTrendCsvError] = useState<unknown>(null)
  const [trendXlsxError, setTrendXlsxError] = useState<unknown>(null)
  const [isOrdersCsvExporting, setIsOrdersCsvExporting] = useState(false)
  const [isOrdersXlsxExporting, setIsOrdersXlsxExporting] = useState(false)
  const [isPaymentReconciliationCsvExporting, setIsPaymentReconciliationCsvExporting] = useState(false)
  const [isPaymentReconciliationXlsxExporting, setIsPaymentReconciliationXlsxExporting] = useState(false)
  const [isProductBreakdownCsvExporting, setIsProductBreakdownCsvExporting] = useState(false)
  const [isProductBreakdownXlsxExporting, setIsProductBreakdownXlsxExporting] = useState(false)
  const [isTrendCsvExporting, setIsTrendCsvExporting] = useState<AdminTrendCsvKind | null>(null)
  const [isTrendXlsxExporting, setIsTrendXlsxExporting] = useState<AdminTrendCsvKind | null>(null)
  const isTrendExportingRef = useRef(false)

  async function exportOrdersCsv() {
    setOrdersCsvError(null)
    setIsOrdersCsvExporting(true)

    try {
      await downloadAdminOrdersCsv(reportParams)
    } catch (error) {
      setOrdersCsvError(error)
    } finally {
      setIsOrdersCsvExporting(false)
    }
  }

  async function exportOrdersXlsx() {
    setOrdersXlsxError(null)
    setIsOrdersXlsxExporting(true)

    try {
      await downloadAdminOrdersXlsx(reportParams)
    } catch (error) {
      setOrdersXlsxError(error)
    } finally {
      setIsOrdersXlsxExporting(false)
    }
  }

  async function exportPaymentReconciliationCsv() {
    setPaymentReconciliationCsvError(null)
    setIsPaymentReconciliationCsvExporting(true)

    try {
      await downloadAdminPaymentReconciliationCsv(reportParams)
    } catch (error) {
      setPaymentReconciliationCsvError(error)
    } finally {
      setIsPaymentReconciliationCsvExporting(false)
    }
  }

  async function exportPaymentReconciliationXlsx() {
    setPaymentReconciliationXlsxError(null)
    setIsPaymentReconciliationXlsxExporting(true)

    try {
      await downloadAdminPaymentReconciliationXlsx(reportParams)
    } catch (error) {
      setPaymentReconciliationXlsxError(error)
    } finally {
      setIsPaymentReconciliationXlsxExporting(false)
    }
  }

  async function exportProductBreakdownCsv() {
    setProductBreakdownCsvError(null)
    setIsProductBreakdownCsvExporting(true)

    try {
      await downloadAdminProductBreakdownCsv(reportParams)
    } catch (error) {
      setProductBreakdownCsvError(error)
    } finally {
      setIsProductBreakdownCsvExporting(false)
    }
  }

  async function exportProductBreakdownXlsx() {
    setProductBreakdownXlsxError(null)
    setIsProductBreakdownXlsxExporting(true)

    try {
      await downloadAdminProductBreakdownXlsx(reportParams)
    } catch (error) {
      setProductBreakdownXlsxError(error)
    } finally {
      setIsProductBreakdownXlsxExporting(false)
    }
  }

  async function exportTrendCsv(kind: AdminTrendCsvKind) {
    if (isTrendExportingRef.current) {
      return
    }

    isTrendExportingRef.current = true
    setTrendCsvError(null)
    setIsTrendCsvExporting(kind)

    try {
      await downloadAdminTrendCsv(kind, trendReportParams)
    } catch (error) {
      setTrendCsvError(error)
    } finally {
      isTrendExportingRef.current = false
      setIsTrendCsvExporting(null)
    }
  }

  async function exportTrendXlsx(kind: AdminTrendCsvKind) {
    if (isTrendExportingRef.current) {
      return
    }

    isTrendExportingRef.current = true
    setTrendXlsxError(null)
    setIsTrendXlsxExporting(kind)

    try {
      await downloadAdminTrendXlsx(kind, trendReportParams)
    } catch (error) {
      setTrendXlsxError(error)
    } finally {
      isTrendExportingRef.current = false
      setIsTrendXlsxExporting(null)
    }
  }

  return {
    actions: {
      exportOrdersCsv,
      exportOrdersXlsx,
      exportPaymentReconciliationCsv,
      exportPaymentReconciliationXlsx,
      exportProductBreakdownCsv,
      exportProductBreakdownXlsx,
      exportTrendCsv,
      exportTrendXlsx,
    },
    errors: {
      ordersCsv: ordersCsvError,
      ordersXlsx: ordersXlsxError,
      paymentReconciliationCsv: paymentReconciliationCsvError,
      paymentReconciliationXlsx: paymentReconciliationXlsxError,
      productBreakdownCsv: productBreakdownCsvError,
      productBreakdownXlsx: productBreakdownXlsxError,
      trendCsv: trendCsvError,
      trendXlsx: trendXlsxError,
    },
    loading: {
      isAnyTrendExporting: isTrendCsvExporting !== null || isTrendXlsxExporting !== null,
      ordersCsv: isOrdersCsvExporting,
      ordersXlsx: isOrdersXlsxExporting,
      paymentReconciliationCsv: isPaymentReconciliationCsvExporting,
      paymentReconciliationXlsx: isPaymentReconciliationXlsxExporting,
      productBreakdownCsv: isProductBreakdownCsvExporting,
      productBreakdownXlsx: isProductBreakdownXlsxExporting,
      trendCsv: isTrendCsvExporting,
      trendXlsx: isTrendXlsxExporting,
    },
  }
}
