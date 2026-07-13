import { createServer as createHttpServer } from 'node:http'

function formatLocalDate(date) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function addDays(date, days) {
  const nextDate = new Date(date)
  nextDate.setDate(nextDate.getDate() + days)
  return nextDate
}

const today = new Date()
const todayDate = formatLocalDate(today)
const tomorrowDate = formatLocalDate(addDays(today, 1))
const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
function dateChipLabel(date) {
  return `${date.getMonth() + 1}月${date.getDate()}日\n${weekdays[date.getDay()]}`
}
const todayLabel = dateChipLabel(today)
const tomorrowLabel = dateChipLabel(addDays(today, 1))

export const e2eVisitDates = {
  emptyDate: tomorrowDate,
  emptyLabel: tomorrowLabel,
  primaryDate: todayDate,
  primaryLabel: todayLabel,
}

const product = {
  productId: 1,
  ticketTypeId: 10,
  scenicSpotName: 'Yulong River Scenic Area',
  productName: 'Yulong River Adult Ticket With Very Long Pier And Scenic Route Name',
  ticketName: 'Adult Ticket Long Display Name',
  ticketCategory: 'ADULT',
  originalPrice: '108.00',
  salePrice: '88.00',
  description: 'Day admission',
  refundRule: 'Refundable before use',
  realNameRequired: true,
  tripType: 'DAY',
  raftCapacity: 4,
  startPierName: 'Jinlong Bridge Pier',
  endPierName: 'Jiuxian Pier',
  windowPhone: '0773-0000000',
}

const slot = {
  timeSlotId: 100,
  productId: 1,
  ticketTypeId: 10,
  visitDate: e2eVisitDates.primaryDate,
  slotStartTime: '09:00:00',
  slotEndTime: '11:00:00',
  quotaRemaining: 5,
}

function ok(data) {
  return { success: true, data, request_id: 'e2e-request' }
}

function fail(code, message) {
  return { success: false, code, message, request_id: 'e2e-request' }
}

function readJson(request) {
  return new Promise((resolve) => {
    const chunks = []
    request.on('data', (chunk) => chunks.push(chunk))
    request.on('end', () => {
      const raw = Buffer.concat(chunks).toString('utf8')

      try {
        resolve(raw ? JSON.parse(raw) : {})
      } catch {
        resolve({ raw })
      }
    })
  })
}

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

export function createE2eOrderFactory({ phone, visitorName }) {
  return function createOrder(orderNo = 'ORD-E2E-001', status = 'CREATED') {
    const paid = status === 'PAID'
    const cancelled = status === 'CANCELLED'
    const refunded = status === 'REFUNDED'

    return {
      orderNo,
      buyerName: visitorName,
      buyerPhone: phone,
      orderStatus: status,
      paymentStatus: paid ? 'PAID' : refunded ? 'REFUNDED' : 'UNPAID',
      totalAmount: '176.00',
      payableAmount: '176.00',
      orderTime: '2026-06-28T15:00:00+08:00',
      canSelfRefund: paid,
      refundDeadline: `${tomorrowDate}T18:00:00+08:00`,
      items: [1, 2].map((index) => ({
        itemNo: `ITEM-E2E-00${index}`,
        productId: 1,
        ticketTypeId: 10,
        productName: product.productName,
        ticketName: product.ticketName,
        timeSlotId: 100,
        visitDate: e2eVisitDates.primaryDate,
        slotStartTime: '09:00:00',
        slotEndTime: '11:00:00',
        originalPrice: '108.00',
        finalPrice: '88.00',
        itemStatus: paid ? 'UNUSED' : refunded ? 'REFUNDED' : cancelled ? 'CANCELLED' : 'PENDING_PAYMENT',
        passengerName: index === 1 ? visitorName : '李四',
        passengerIdType: 'ID_CARD',
        passengerIdNumberMasked: `110********00${index}`,
        passengerPhoneMasked: `${phone.slice(0, 3)}****${phone.slice(-4)}`,
        ...(paid || refunded ? { ticketCode: `TICKET-E2E-00${index}-LONG-CODE-20260701-ABCDEFGHIJK` } : {}),
      })),
    }
  }
}

export function createMockApi({ password, phone, username, visitorName }) {
  const createOrder = createE2eOrderFactory({ phone, visitorName })
  const state = {
    allowedOrigin: '',
    adminAuthMeCount: 0,
    catalogProductsFail: false,
    catalogTimeSlotsFail: false,
    createOrderBody: null,
    createOrderBodies: [],
    csrfFetchCount: 0,
    csrfHeaders: [],
    currentCsrfToken: '',
    csrfRebindRequired: false,
    databaseHealthFail: false,
    cancelOrderNo: '',
    cancelOrderNos: [],
    cancelNotAllowedOrderNos: new Set(),
    detailFailureOrderNos: new Set(),
    idempotencyKey: '',
    idempotencyKeys: [],
    loginBodies: [],
    rateLimitedLoginUsernames: new Set(),
    notPayableOrderNos: new Set(),
    orders: [],
    orderErrors: [],
    passengerTemplateId: 2,
    passengerTemplates: [
      {
        templateId: 1,
        passengerName: visitorName,
        idType: 'ID_CARD',
        idNumber: '110101199001010011',
        phone,
      },
    ],
    payAttemptsByOrder: new Map(),
    paymentAttempts: [],
    refundBodies: [],
    quotaNotEnoughOrderNos: new Set(),
    registerBodies: [],
    registerConflictPhones: new Set(),
    sessionLookupFail: false,
    visitor: null,
  }

  const server = createHttpServer(async (request, response) => {
    const url = new URL(request.url || '/', `http://${request.headers.host}`)

    response.setHeader('Access-Control-Allow-Origin', state.allowedOrigin)
    response.setHeader('Access-Control-Allow-Credentials', 'true')
    response.setHeader('Access-Control-Allow-Headers', 'accept, content-type, idempotency-key, x-csrf-token')
    response.setHeader('Access-Control-Allow-Methods', 'GET,POST,PATCH,DELETE,OPTIONS')

    if (request.method === 'OPTIONS') {
      response.writeHead(204)
      response.end()
      return
    }

    function json(status, body, headers = {}) {
      const payload = JSON.stringify(body)
      response.writeHead(status, {
        'Content-Length': Buffer.byteLength(payload),
        'Content-Type': 'application/json; charset=utf-8',
        'X-Request-Id': 'e2e-request',
        ...headers,
      })
      response.end(payload)
    }

    function requireCsrf() {
      const header = request.headers['x-csrf-token'] || ''
      state.csrfHeaders.push(header)

      if (state.csrfRebindRequired || !state.currentCsrfToken || header !== state.currentCsrfToken) {
        json(403, fail('CSRF_INVALID', 'CSRF token invalid'))
        return false
      }

      return true
    }

    if (request.method === 'GET' && url.pathname === '/api/health') {
      json(200, ok({ environment: 'e2e', service: 'scenic-ticket-api', status: 'ok' }))
      return
    }

    if (request.method === 'GET' && url.pathname === '/api/health/db') {
      if (state.databaseHealthFail) {
        json(503, fail('DATABASE_UNAVAILABLE', 'Database unavailable'))
        return
      }

      json(200, ok({ database: 'ok', environment: 'e2e', service: 'scenic-ticket-api', status: 'ok' }))
      return
    }

    if (request.method === 'GET' && url.pathname === '/api/auth/csrf') {
      state.csrfFetchCount += 1
      state.currentCsrfToken = `e2e-csrf-${state.csrfFetchCount}`
      state.csrfRebindRequired = false
      json(200, ok({ headerName: 'x-csrf-token' }), {
        'Set-Cookie': `scenic_csrf=${state.currentCsrfToken}; Path=/; SameSite=Lax`,
      })
      return
    }

    if (request.method === 'GET' && url.pathname === '/api/auth/me') {
      if (state.sessionLookupFail) {
        json(503, fail('SESSION_LOOKUP_FAILED', 'Session lookup failed'))
        return
      }

      if (!state.visitor) {
        json(401, fail('AUTH_REQUIRED', 'Login required'))
        return
      }

      json(200, ok(state.visitor))
      return
    }

    if (request.method === 'GET' && url.pathname === '/api/admin/auth/me') {
      state.adminAuthMeCount += 1
      json(401, fail('ADMIN_AUTH_REQUIRED', 'Admin login required'))
      return
    }

    if (request.method === 'POST' && url.pathname === '/api/auth/visitor/login') {
      if (!requireCsrf()) {
        return
      }

      const body = await readJson(request)
      state.loginBodies.push(body)
      if (state.rateLimitedLoginUsernames.has(body.username)) {
        json(429, fail('RATE_LIMITED', '请求过于频繁，请稍后再试'))
        return
      }

      if (body.username !== username || body.password !== password) {
        json(401, fail('VISITOR_LOGIN_FAILED', '账号或密码错误'))
        return
      }

      state.visitor = { visitorId: 7, visitorName: username, phone, visitorScope: 'REGISTERED', isRegistered: true }
      state.csrfRebindRequired = true
      json(200, ok(state.visitor))
      return
    }

    if (request.method === 'POST' && url.pathname === '/api/auth/visitor/register') {
      if (!requireCsrf()) {
        return
      }

      const body = await readJson(request)
      state.registerBodies.push(body)
      if (state.registerConflictPhones.has(body.phone)) {
        json(409, fail('VISITOR_REGISTER_CONFLICT', '账号或手机号已被使用'))
        return
      }

      state.visitor = {
        visitorId: 7,
        visitorName: body.username || visitorName,
        phone: body.phone || phone,
        visitorScope: 'REGISTERED',
        isRegistered: true,
      }
      state.csrfRebindRequired = true
      json(200, ok(state.visitor))
      return
    }

    if (request.method === 'POST' && url.pathname === '/api/auth/logout') {
      if (!requireCsrf()) {
        return
      }

      state.visitor = null
      state.csrfRebindRequired = true
      json(200, ok({ loggedOut: true }), {
        'Set-Cookie': [
          'scenic_session=; Path=/; Max-Age=0; SameSite=Lax',
          'scenic_csrf=; Path=/; Max-Age=0; SameSite=Lax',
        ],
      })
      return
    }

    if (request.method === 'GET' && url.pathname === '/api/catalog/products') {
      if (state.catalogProductsFail) {
        json(500, fail('CATALOG_UNAVAILABLE', 'Catalog unavailable'))
        return
      }

      json(200, ok([product]))
      return
    }

    if (request.method === 'GET' && url.pathname === '/api/catalog/time-slots') {
      if (state.catalogTimeSlotsFail) {
        json(500, fail('TIME_SLOTS_UNAVAILABLE', 'Time slots unavailable'))
        return
      }

      if (url.searchParams.get('visitDate') === e2eVisitDates.emptyDate) {
        json(200, ok([]))
        return
      }

      json(200, ok([{ ...slot, visitDate: url.searchParams.get('visitDate') || slot.visitDate }]))
      return
    }

    if (request.method === 'GET' && url.pathname === '/api/me/passenger-templates') {
      if (!state.visitor) {
        json(401, fail('AUTH_REQUIRED', 'Login required'))
        return
      }

      json(200, ok(state.passengerTemplates))
      return
    }

    if (request.method === 'POST' && url.pathname === '/api/me/passenger-templates') {
      if (!requireCsrf()) {
        return
      }

      const body = await readJson(request)
      const template = { ...body, templateId: state.passengerTemplateId++ }
      state.passengerTemplates.push(template)
      json(200, ok(template))
      return
    }

    const passengerTemplateMatch = url.pathname.match(/^\/api\/me\/passenger-templates\/(\d+)$/)
    if (passengerTemplateMatch && request.method === 'PATCH') {
      if (!requireCsrf()) {
        return
      }

      const templateId = Number(passengerTemplateMatch[1])
      const index = state.passengerTemplates.findIndex((template) => template.templateId === templateId)
      if (index === -1) {
        json(404, fail('PASSENGER_TEMPLATE_NOT_FOUND', 'Passenger template not found'))
        return
      }

      state.passengerTemplates[index] = { ...(await readJson(request)), templateId }
      json(200, ok(state.passengerTemplates[index]))
      return
    }

    if (passengerTemplateMatch && request.method === 'DELETE') {
      if (!requireCsrf()) {
        return
      }

      const templateId = Number(passengerTemplateMatch[1])
      state.passengerTemplates = state.passengerTemplates.filter((template) => template.templateId !== templateId)
      json(200, ok({ deleted: true }))
      return
    }

    if (request.method === 'POST' && url.pathname === '/api/orders') {
      if (!requireCsrf()) {
        return
      }

      state.createOrderBody = await readJson(request)
      state.createOrderBodies.push(state.createOrderBody)
      const order = createOrder(`ORD-E2E-${String(state.orders.length + 1).padStart(3, '0')}`, 'CREATED')
      state.orders.push(order)
      json(200, ok(order))
      return
    }

    if (request.method === 'GET' && url.pathname === '/api/me/orders') {
      if (!state.visitor) {
        json(401, fail('AUTH_REQUIRED', 'Login required'))
        return
      }

      const status = url.searchParams.get('status')
      const orders = status ? state.orders.filter((order) => order.orderStatus === status) : state.orders
      json(200, ok([...orders].reverse()))
      return
    }

    const orderDetailMatch = url.pathname.match(/^\/api\/me\/orders\/(ORD-E2E-\d{3})$/)
    if (request.method === 'GET' && orderDetailMatch) {
      if (!state.visitor) {
        json(401, fail('AUTH_REQUIRED', 'Login required'))
        return
      }

      const order = state.orders.find((candidate) => candidate.orderNo === orderDetailMatch[1])
      await delay(500)
      const orderDetailFailureCode = 'ORDER_NOT_FOUND'
      if (!order || state.detailFailureOrderNos.has(order.orderNo)) {
        state.orderErrors.push({ code: orderDetailFailureCode, endpoint: 'detail', orderNo: orderDetailMatch[1] })
      }
      json(
        order && !state.detailFailureOrderNos.has(order.orderNo) ? 200 : 404,
        order && !state.detailFailureOrderNos.has(order.orderNo) ? ok(order) : fail(orderDetailFailureCode, 'Order not found'),
      )
      return
    }

    const payMatch = url.pathname.match(/^\/api\/orders\/(ORD-E2E-\d{3})\/pay$/)
    if (request.method === 'POST' && payMatch) {
      if (!requireCsrf()) {
        return
      }

      state.idempotencyKey = request.headers['idempotency-key'] || ''
      state.idempotencyKeys.push(state.idempotencyKey)
      state.paymentAttempts.push({ idempotencyKey: state.idempotencyKey, orderNo: payMatch[1] })
      const index = state.orders.findIndex((candidate) => candidate.orderNo === payMatch[1])
      if (index === -1) {
        const payFailureCode = 'ORDER_NOT_FOUND'
        state.orderErrors.push({ code: payFailureCode, endpoint: 'pay', orderNo: payMatch[1] })
        json(404, fail(payFailureCode, 'Order not found'))
        return
      }

      const payAttempts = (state.payAttemptsByOrder.get(payMatch[1]) ?? 0) + 1
      state.payAttemptsByOrder.set(payMatch[1], payAttempts)

      if (state.notPayableOrderNos.has(payMatch[1])) {
        const payFailureCode = 'ORDER_NOT_PAYABLE'
        state.orderErrors.push({ code: payFailureCode, endpoint: 'pay', orderNo: payMatch[1] })
        json(409, fail(payFailureCode, '订单状态不可支付'))
        return
      }

      if (state.quotaNotEnoughOrderNos.has(payMatch[1])) {
        const payFailureCode = 'TIME_SLOT_QUOTA_NOT_ENOUGH'
        state.orderErrors.push({ code: payFailureCode, endpoint: 'pay', orderNo: payMatch[1] })
        json(409, fail(payFailureCode, '当前时段余票不足'))
        return
      }

      if (payMatch[1] === 'ORD-E2E-001' && payAttempts === 1) {
        json(500, fail('INTERNAL_SERVER_ERROR', '服务暂时不可用，请稍后重试'))
        return
      }

      state.orders[index] = createOrder(payMatch[1], 'PAID')
      json(200, ok(state.orders[index]))
      return
    }

    const cancelMatch = url.pathname.match(/^\/api\/orders\/(ORD-E2E-\d{3})\/cancel$/)
    if (request.method === 'POST' && cancelMatch) {
      if (!requireCsrf()) {
        return
      }

      const index = state.orders.findIndex((candidate) => candidate.orderNo === cancelMatch[1])
      if (index === -1) {
        const cancelFailureCode = 'ORDER_NOT_FOUND'
        state.orderErrors.push({ code: cancelFailureCode, endpoint: 'cancel', orderNo: cancelMatch[1] })
        json(404, fail(cancelFailureCode, 'Order not found'))
        return
      }

      if (
        state.cancelNotAllowedOrderNos.has(cancelMatch[1]) ||
        state.orders[index].orderStatus !== 'CREATED' ||
        state.orders[index].paymentStatus !== 'UNPAID'
      ) {
        const cancelFailureCode = 'ORDER_NOT_CANCELABLE'
        state.orderErrors.push({ code: cancelFailureCode, endpoint: 'cancel', orderNo: cancelMatch[1] })
        json(409, fail(cancelFailureCode, '当前订单状态不可取消'))
        return
      }

      state.cancelOrderNo = cancelMatch[1]
      state.cancelOrderNos.push(cancelMatch[1])
      state.orders[index] = createOrder(cancelMatch[1], 'CANCELLED')
      json(200, ok(state.orders[index]))
      return
    }

    const refundMatch = url.pathname.match(/^\/api\/orders\/(ORD-E2E-\d{3})\/refund$/)
    if (request.method === 'POST' && refundMatch) {
      if (!requireCsrf()) {
        return
      }
      const index = state.orders.findIndex((candidate) => candidate.orderNo === refundMatch[1])
      if (index === -1) {
        json(404, fail('ORDER_NOT_FOUND', 'Order not found'))
        return
      }
      if (!state.orders[index].canSelfRefund) {
        json(409, fail('ORDER_NOT_REFUNDABLE', '当前订单不可退款'))
        return
      }
      state.refundBodies.push(await readJson(request))
      state.orders[index] = createOrder(refundMatch[1], 'REFUNDED')
      json(200, ok(state.orders[index]))
      return
    }

    json(404, fail('NOT_FOUND', `${request.method} ${url.pathname}`))
  })

  return { createOrder, server, state }
}
