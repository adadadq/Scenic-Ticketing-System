import {
  clickByText,
  clickDateChip,
  clickableText,
  clickSegmentedOption,
  clickSelector,
  clickTableRowContaining,
  enabledSelector,
  evaluate,
  fillPlaceholder,
  fillPlaceholderIn,
  fillSelector,
  hasPlaceholder,
  headerIncludesText,
  includesText,
  navigateApp,
  openAuthSessionDiagnostic,
  selectAntOption,
  visibleElementScript,
  visibleTextSelector,
  waitFor,
} from './e2e-browser-utils.mjs'
import { withE2eHarness } from './e2e-harness.mjs'
import { assertVisitorE2eState } from './e2e-visitor-assertions.mjs'
import { finishE2eSmoke } from './e2e-smoke-result.mjs'
import { createE2eOrderFactory, e2eVisitDates } from './e2e-mock-api.mjs'
import { assert } from './e2e-runtime-utils.mjs'
import { createE2eIdentity } from './e2e-test-data.mjs'

const chromePath = process.env.CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
const viewport = { width: 390, height: 844 }
const realApiBaseUrl = process.env.E2E_API_BASE_URL?.trim()
const {
  password: e2ePassword,
  phone: e2ePhone,
  phoneWithSeparators: e2ePhoneWithSeparators,
  username: e2eUsername,
} = createE2eIdentity({ realApiBaseUrl })
const createOrder = createE2eOrderFactory({ phone: e2ePhone, visitorName: e2eUsername })

async function openAdminSidePage(client, label) {
  const clicked = await evaluate(
    client,
    `(() => {
      ${visibleElementScript}
      const target = [...document.querySelectorAll('.admin-side-menu [role="menuitem"]')]
        .find((element) => isVisible(element) && element.textContent.includes(${JSON.stringify(label)}))
      if (!target) return false
      target.click()
      return true
    })()`,
  )
  assert(clicked, `admin side navigation should open ${label}`)
}

async function run() {
  await withE2eHarness({
    chromePath,
    password: e2ePassword,
    phone: e2ePhone,
    realApiBaseUrl,
    username: e2eUsername,
    viewport,
    visitorName: e2eUsername,
  }, async ({ apiBaseUrl, appUrl, client, mock }) => {
    await waitFor(client, 'document.readyState === "complete"', 'page load')
    let sessionFailureState = null
    if (mock) {
      mock.state.sessionLookupFail = true
      await navigateApp(client, appUrl)
      await waitFor(client, 'document.readyState === "complete"', 'page load with session lookup failure')
      await waitFor(client, headerIncludesText('登录状态检查失败'), 'auth session failure entry')
      await openAuthSessionDiagnostic(client, 'logged-out auth session')
      await waitFor(client, includesText('登录状态检查失败'), 'auth session diagnostic title')
      await waitFor(client, includesText('错误码：SESSION_LOOKUP_FAILED'), 'auth session diagnostic code')
      await waitFor(client, includesText('请求编号：e2e-request'), 'auth session diagnostic request id')
      sessionFailureState = await evaluate(
        client,
        `(() => ({
          hasDiagnosticCode: document.body.textContent.includes('错误码：SESSION_LOOKUP_FAILED'),
          hasDiagnosticRequestId: document.body.textContent.includes('请求编号：e2e-request'),
          hasRetryAction: Boolean(document.querySelector('.auth-status button:not([disabled])')),
          hasSessionError: document.querySelector('.auth-status')?.textContent.includes('登录状态检查失败') ?? false,
        }))()`,
      )
      mock.state.sessionLookupFail = false
      await clickSelector(client, '.auth-status button:not(.auth-session-error-trigger)')
      await waitFor(client, headerIncludesText('未登录'), 'session recovery after retry')
    }

    await waitFor(client, headerIncludesText('未登录'), 'logged-out session badge')
    await waitFor(client, includesText('账号登录'), 'login entry')
    await waitFor(client, `Boolean(document.querySelector('.ticket-card-title'))`, 'mobile ticket card title')
    let adminDetailState = null
    let adminBatchCheckInState = null
    let adminBatchUndoCheckInState = null
    let adminFilterState = null
    let adminFullRefundState = null
    let adminPartialRefundState = null
    let adminPageSeparationState = null
    let adminReportState = null
    let adminReportTrendExportState = null
    let adminReportZeroFillState = null
    let adminTicketsState = null
    let adminCheckInAuditExportState = null
    let adminCheckInFailureAuditExportState = null
    let adminCheckInFailureLogSearchState = null
    let adminRefundAuditExportState = null
    let adminRefundAuditState = null
    let adminRefundLogSearchState = null
    let adminExportJobCreateState = null
    let adminIntermediateState = null
    let adminReturnToVisitorState = null
    let adminShellState = null
    let adminTabletState = null
    let bookingStepState = null
    if (mock) {
      await waitFor(
        client,
        `document.querySelector('.booking-steps')?.getAttribute('data-current-step-label') === '填写信息'`,
        'booking step before real-name',
      )
      bookingStepState = {
        initialStep: await evaluate(client, `document.querySelector('.booking-steps')?.getAttribute('data-current-step-label') || ''`),
      }
    }
    const mobileDateStripState = await evaluate(
      client,
      `(() => {
        const strip = document.querySelector('.date-strip')
        const chips = strip ? [...strip.querySelectorAll('.date-chip')] : []
        const firstTop = chips[0]?.getBoundingClientRect().top ?? 0
        return {
          chipCount: chips.length,
          clientWidth: document.documentElement.clientWidth,
          flexWrap: strip ? getComputedStyle(strip).flexWrap : '',
          sameRow: chips.every((chip) => Math.abs(chip.getBoundingClientRect().top - firstTop) < 1),
          scrollWidth: document.documentElement.scrollWidth,
          stripCanScrollHorizontally: strip ? strip.scrollWidth >= strip.clientWidth : false,
        }
      })()`,
    )
    const mobileTicketCardState = await evaluate(
      client,
      `(() => {
        const card = document.querySelector('.ticket-card')
        const title = document.querySelector('.ticket-card-title')
        const titleRect = title?.getBoundingClientRect()
        const lineHeight = title ? Number.parseFloat(getComputedStyle(title).lineHeight) : 0
        return {
          cardClientWidth: card?.clientWidth ?? 0,
          cardScrollWidth: card?.scrollWidth ?? 0,
          text: title?.textContent ?? '',
          titleAttribute: title?.getAttribute('title') ?? '',
          hasFullTitle: Boolean(title?.textContent && title.getAttribute('title') === title.textContent),
          titleLineCount: lineHeight && titleRect ? Math.round(titleRect.height / lineHeight) : 0,
        }
      })()`,
    )
    const visitorShellState = await evaluate(
      client,
      `(() => {
        const visitorMenuItems = [...document.querySelectorAll('.visitor-sider .ant-menu-item')]
        return {
          hasVisitorShell: Boolean(document.querySelector('.visitor-shell')),
          hasVisitorServiceLabel: document.querySelector('.visitor-sider')?.textContent.includes('游客购票') &&
            document.querySelector('.visitor-sider')?.textContent.includes('游客服务'),
          hidesStatusStrip: !document.querySelector('.visitor-header .status-strip'),
          hidesAdminMenuEntry: !visitorMenuItems.some((item) =>
            item.textContent.includes('后台管理') || item.textContent.includes('后台工作台')
          ),
        }
      })()`,
    )
    const mobileBookingVisualState = await evaluate(
      client,
      `(() => {
        const bar = document.querySelector('.mobile-action-bar')
        const action = document.querySelector('.mobile-action-bar button')
        const heading = document.querySelector('.booking-heading')
        const summary = document.querySelector('.booking-summary-card')
        const actionRect = action?.getBoundingClientRect()
        return {
          actionWidth: actionRect?.width ?? 0,
          hasBookingHeading: Boolean(heading),
          hidesDesktopSummary: summary ? getComputedStyle(summary).display === 'none' : false,
          pageFits: document.documentElement.scrollWidth === document.documentElement.clientWidth,
          stickyBarVisible: bar ? getComputedStyle(bar).display === 'grid' : false,
        }
      })()`,
    )
    let loggedOutOrdersState = null
    let emptyOrdersState = null
    if (mock) {
      await clickByText(client, '我的订单')
      await waitFor(client, `document.querySelector('.page-heading h1')?.textContent.includes('我的订单')`, 'logged-out orders page')
      await waitFor(client, includesText('请先登录后查看订单'), 'logged-out orders auth error')
      loggedOutOrdersState = await evaluate(
        client,
        `(() => ({
          canOpenLogin: [...document.querySelectorAll('button')].some((button) =>
            button.textContent.includes('去登录') && !button.disabled
          ),
          canReturnBooking: [...document.querySelectorAll('button')].some((button) =>
            button.textContent.includes('返回购票') && !button.disabled
          ),
          hasAuthError: document.body.textContent.includes('请先登录后查看订单'),
          hasEmptyText: document.body.textContent.includes('暂无订单'),
        }))()`,
      )
      await clickByText(client, '返回购票')
      await waitFor(client, `document.querySelector('.page-heading h1')?.textContent.includes('购买门票')`, 'booking page from logged-out orders')
    }

    let desktopAuthActionState = null
    let desktopBookingVisualState = null
    if (mock) {
      await client.send('Emulation.setDeviceMetricsOverride', {
        deviceScaleFactor: 1,
        height: 900,
        mobile: false,
        width: 1280,
      })
      await waitFor(
        client,
        `(() => {
          ${visibleElementScript}
          const button = document.querySelector('.pay-button')
          return Boolean(button && isVisible(button) && button.textContent.includes('先登录') && !button.disabled)
        })()`,
        'desktop booking login action',
      )
      desktopBookingVisualState = await evaluate(
        client,
        `(() => {
          const contentRoots = [document.body, document.querySelector('#root'), document.querySelector('.app-shell')]
            .filter(Boolean)
          const heading = document.querySelector('.booking-heading')
          const grid = document.querySelector('.booking-workbench-grid')
          const summary = document.querySelector('.booking-summary-card')
          const readiness = document.querySelector('.booking-readiness')
          const readinessItems = [...document.querySelectorAll('.booking-readiness-item')]
          return {
            hasBookingHeading: Boolean(heading),
            hasReadinessList: Boolean(readiness),
            hasWorkbenchGrid: Boolean(grid),
            hasSummaryCard: Boolean(summary) && getComputedStyle(summary).display !== 'none',
            pageFits: Math.max(...contentRoots.map((element) => element.scrollWidth)) === document.documentElement.clientWidth,
            readinessItemCount: readinessItems.length,
            readinessText: readiness?.textContent ?? '',
            summaryPosition: summary ? getComputedStyle(summary).position : '',
          }
        })()`,
      )
      desktopAuthActionState = {
        loginLabel: await evaluate(client, `document.querySelector('.pay-button')?.textContent || ''`),
      }
      await clickSelector(client, '.pay-button')
    } else {
      await waitFor(
        client,
        `(() => {
          const button = document.querySelector('.mobile-action-bar button')
          return Boolean(button?.textContent.includes('登录') && !button.disabled)
        })()`,
        'booking login action',
      )
      await clickSelector(client, '.mobile-action-bar button')
    }
    await waitFor(client, hasPlaceholder('demo_visitor'), 'login username input', 10000)
    await fillPlaceholder(client, 'demo_visitor', 'ab')
    await fillPlaceholder(client, '请输入密码', e2ePassword)
    await clickSelector(client, '.auth-modal-primary-panel div:not([hidden]) button[type="submit"]')
    await waitFor(client, includesText('账号为 3-32 位字母、数字或下划线'), 'invalid login username validation')
    if (mock) {
      assert(mock.state.loginBodies.length === 0, 'invalid login username should not submit request in mock mode')
    }

    await fillPlaceholder(client, 'demo_visitor', e2eUsername)
    await fillPlaceholder(client, '请输入密码', e2ePassword)
    if (mock) {
      mock.state.rateLimitedLoginUsernames.add(e2eUsername)
    }
    await clickSelector(client, '.auth-modal-primary-panel div:not([hidden]) button[type="submit"]')
    if (mock) {
      await waitFor(client, includesText('请求过于频繁，请稍后再试'), 'rate-limited login error')
      await waitFor(client, includesText('请求编号：e2e-request'), 'rate-limited login request id')
      await waitFor(
        client,
        `(() => {
          const authText = document.querySelector('.auth-status')?.textContent || ''
          return authText.includes('未登录') && !authText.includes('已登录')
        })()`,
        'rate-limited login keeps visitor logged out',
      )
      assert(mock.state.visitor === null, 'rate-limited login should not create a visitor session in mock mode')
      mock.state.rateLimitedLoginUsernames.delete(e2eUsername)
    }

    await clickSegmentedOption(client, '注册账号')
    await waitFor(client, hasPlaceholder('例如 yulong_001'), 'register username input')
    await fillPlaceholder(client, '例如 yulong_001', e2eUsername)
    await fillPlaceholder(client, '至少 6 位', e2ePassword)
    await fillPlaceholder(client, '13911112222', '139 1111a2222')
    await clickSelector(client, '.auth-modal-primary-panel div:not([hidden]) button[type="submit"]')
    await waitFor(client, includesText('请输入 11 位中国大陆手机号'), 'invalid register phone validation')
    if (mock) {
      assert(mock.state.registerBodies.length === 0, 'invalid register phone should not submit request in mock mode')
    }

    await fillPlaceholder(client, '13911112222', e2ePhoneWithSeparators)
    if (mock) {
      mock.state.registerConflictPhones.add(e2ePhone)
    }
    await clickSelector(client, '.auth-modal-primary-panel div:not([hidden]) button[type="submit"]')
    if (mock) {
      await waitFor(client, includesText('账号或手机号已被使用'), 'register conflict error')
      await waitFor(client, includesText('请求编号：e2e-request'), 'register conflict request id')
      await waitFor(client, headerIncludesText('未登录'), 'register conflict keeps visitor logged out')
      assert(mock.state.visitor === null, 'register conflict should not create visitor session in mock mode')
      mock.state.registerConflictPhones.delete(e2ePhone)
      await clickSelector(client, '.auth-modal-primary-panel div:not([hidden]) button[type="submit"]')
    }
    await waitFor(
      client,
      `document.querySelector('.auth-status')?.textContent.includes(${JSON.stringify(e2eUsername)})`,
      'registered visitor',
    )
    await waitFor(client, headerIncludesText('已登录'), 'registered visitor session badge')
    if (mock) {
      mock.state.sessionLookupFail = true
      await navigateApp(client, appUrl)
      await waitFor(client, 'document.readyState === "complete"', 'registered visitor page load with session lookup failure')
      await waitFor(client, headerIncludesText('登录状态检查失败'), 'registered visitor auth session failure entry')
      await openAuthSessionDiagnostic(client, 'registered visitor auth session')
      await waitFor(client, includesText('错误码：SESSION_LOOKUP_FAILED'), 'registered visitor auth session diagnostic code')
      await waitFor(client, includesText('请求编号：e2e-request'), 'registered visitor auth session diagnostic request id')
      mock.state.sessionLookupFail = false
      await clickSelector(client, '.auth-status button:not(.auth-session-error-trigger)')
      await waitFor(client, headerIncludesText('已登录'), 'registered visitor session recovery after retry')
    }
    await client.send('Emulation.setDeviceMetricsOverride', {
      deviceScaleFactor: 1,
      height: viewport.height,
      mobile: true,
      width: viewport.width,
    })
    if (mock) {
      await clickByText(client, '我的订单')
      await waitFor(client, `document.querySelector('.page-heading h1')?.textContent.includes('我的订单')`, 'empty orders page')
      await waitFor(client, clickableText('去购票'), 'empty orders booking action')
      emptyOrdersState = await evaluate(
        client,
        `(() => ({
          canOpenBooking: [...document.querySelectorAll('button')].some((button) =>
            button.textContent.includes('去购票') && !button.disabled
          ),
          hasEmptyText: document.body.textContent.includes('暂无订单'),
          mobileOrdersVisible: getComputedStyle(document.querySelector('.orders-mobile-list')).display !== 'none',
        }))()`,
      )
      await clickByText(client, '去购票')
      await waitFor(client, `document.querySelector('.page-heading h1')?.textContent.includes('购买门票')`, 'booking page from empty orders')
    }
    if (mock) {
      await waitFor(
        client,
        `document.querySelector('.booking-steps')?.getAttribute('data-current-step-label') === '支付订单'`,
        'booking step after real-name',
      )
      bookingStepState.afterRegisterStep = await evaluate(
        client,
        `document.querySelector('.booking-steps')?.getAttribute('data-current-step-label') || ''`,
      )
    }

    let catalogFallbackState = null
    let timeSlotFallbackState = null
    if (mock) {
      mock.state.catalogProductsFail = true
      await navigateApp(client, appUrl)
      await waitFor(client, 'document.readyState === "complete"', 'booking page with catalog failure')
      await waitFor(client, includesText('暂时无法提交订单'), 'catalog fallback alert')
      await waitFor(client, includesText('遇龙河成人票'), 'demo product fallback')
      catalogFallbackState = await evaluate(
        client,
        `(() => ({
          createButtonDisabled: Boolean(document.querySelector('.mobile-action-bar button')?.disabled),
          currentStepLabel: document.querySelector('.booking-steps')?.getAttribute('data-current-step-label') || '',
          hasCatalogAlert: document.body.textContent.includes('暂时无法提交订单'),
          hasDemoHint: document.body.textContent.includes('当前可先查看票种，提交订单请稍后再试。'),
          hasDemoSlot: document.body.textContent.includes('08:30-10:30'),
          hasDemoTicket: document.body.textContent.includes('遇龙河成人票'),
        }))()`,
      )
      mock.state.catalogProductsFail = false
      await navigateApp(client, appUrl)
      await waitFor(client, 'document.readyState === "complete"', 'booking page after catalog recovery')

      mock.state.catalogTimeSlotsFail = true
      await navigateApp(client, appUrl)
      await waitFor(client, 'document.readyState === "complete"', 'booking page with time slot failure')
      await clickDateChip(client, e2eVisitDates.emptyLabel)
      await waitFor(client, includesText('当前可先查看时段，提交订单请稍后再试。'), 'time slot fallback alert')
      await waitFor(client, includesText('08:30-10:30'), 'demo time slot fallback')
      timeSlotFallbackState = await evaluate(
        client,
        `(() => ({
          createButtonDisabled: Boolean(document.querySelector('.mobile-action-bar button')?.disabled),
          currentStepLabel: document.querySelector('.booking-steps')?.getAttribute('data-current-step-label') || '',
          hasDemoHint: document.body.textContent.includes('当前可先查看时段，提交订单请稍后再试。'),
          hasDemoSlot: document.body.textContent.includes('08:30-10:30'),
          hasEnglishTicketName: document.body.textContent.includes('Adult Ticket'),
          hasRealProduct: document.body.textContent.includes('成人票'),
          hasTimeSlotAlert: document.body.textContent.includes('暂时无法提交订单'),
        }))()`,
      )
      mock.state.catalogTimeSlotsFail = false
      await navigateApp(client, appUrl)
      await waitFor(client, 'document.readyState === "complete"', 'booking page after time slot recovery')
    }

    await waitFor(client, enabledSelector('.mobile-action-bar button'), 'selectable product and time slot')
    let emptyTimeSlotsState = null
    if (mock) {
      await clickDateChip(client, e2eVisitDates.emptyLabel)
      await waitFor(client, includesText('当前日期暂无可预约时段，请换一天查看'), 'empty time slot state')
      emptyTimeSlotsState = await evaluate(
        client,
        `(() => ({
          createButtonDisabled: Boolean(document.querySelector('.mobile-action-bar button')?.disabled),
          hasEmptyTimeSlots: document.body.textContent.includes('当前日期暂无可预约时段，请换一天查看'),
          scrollWidth: document.documentElement.scrollWidth,
          clientWidth: document.documentElement.clientWidth,
        }))()`,
      )
      await clickDateChip(client, e2eVisitDates.primaryLabel)
      await waitFor(client, enabledSelector('.mobile-action-bar button'), 'selectable product and time slot after empty date')
    }
    await clickSelector(client, '.mobile-action-bar button')
    await waitFor(client, `document.querySelector('.page-heading h1')?.textContent.includes('我的订单')`, 'orders page', 10000)
    await waitFor(client, enabledSelector('.order-mobile-card'), 'mobile order card')
    let orderCardToneState = null
    if (mock) {
      orderCardToneState = await evaluate(
        client,
        `(() => {
          const pendingCard = document.querySelector('.order-mobile-card[data-order-status="CREATED"]')
          return {
            pendingAction: pendingCard?.textContent.includes('查看并处理') ?? false,
            pendingClass: pendingCard?.classList.contains('is-pending') ?? false,
            pendingStatus: pendingCard?.getAttribute('data-order-status') ?? '',
          }
        })()`,
      )
    }
    await clickSelector(client, '.order-mobile-card')
    await waitFor(
      client,
      `(() => {
        const body = document.querySelector('.mobile-order-detail-drawer .ant-drawer-body')
        const rect = body?.getBoundingClientRect()
        return Boolean(rect && rect.top < window.innerHeight && rect.bottom <= window.innerHeight + 1)
      })()`,
      'mobile detail drawer settled',
    )
    await waitFor(client, enabledSelector('.mobile-order-detail-drawer .ant-btn-primary'), 'mobile drawer pay button')
    const mobileDetailActionState = await evaluate(
      client,
      `(() => {
        const actions = document.querySelector('.mobile-order-detail-drawer .order-detail-actions')
        const buttons = actions ? [...actions.querySelectorAll('button')] : []
        const rect = actions?.getBoundingClientRect()
        return {
          bottomGap: rect ? Math.round(window.innerHeight - rect.bottom) : null,
          buttonCount: buttons.length,
          firstButtonWidth: buttons[0]?.getBoundingClientRect().width ?? 0,
          position: actions ? getComputedStyle(actions).position : '',
          secondButtonWidth: buttons[1]?.getBoundingClientRect().width ?? 0,
        }
      })()`,
    )
    await waitFor(
      client,
      `document.querySelector('.mobile-order-detail-drawer')?.textContent.includes('余票以支付结果为准')`,
      'payment deadline note',
    )

    await clickSelector(client, '.mobile-order-detail-drawer .ant-btn-primary')
    if (mock) {
      await waitFor(client, includesText('服务暂时不可用，请稍后重试'), 'retryable payment failure')
      await waitFor(client, includesText('请求编号：e2e-request'), 'retryable payment request id')
      await waitFor(client, enabledSelector('.mobile-order-detail-drawer .ant-btn-primary'), 'retry payment button')
      await clickSelector(client, '.mobile-order-detail-drawer .ant-btn-primary')
    }
    await waitFor(client, includesText('支付成功，票码已生成'), 'payment success')
    await waitFor(
      client,
      visibleTextSelector('.mobile-order-detail-drawer .payment-success-result', '支付成功，票码已生成'),
      'mobile payment success result',
    )

    const paidPageState = await evaluate(
      client,
      `(() => {
        ${visibleElementScript}
        const detailDrawer = document.querySelector('.mobile-order-detail-drawer')
        const actionBar = detailDrawer?.querySelector('.order-detail-actions')
        const successResult = detailDrawer?.querySelector('.payment-success-result')
        const stateCard = detailDrawer?.querySelector('.order-detail-state-card')
        const ticketRegion = detailDrawer?.querySelector('.ticket-code-list')
        return {
          clientWidth: document.documentElement.clientWidth,
          hidesStateActions: !actionBar || !isVisible(actionBar),
          hasMockOrder: document.body.textContent.includes('ORD-E2E-001'),
          hasMockTicket1: document.body.textContent.includes('TICKET-E2E-001-LONG-CODE-20260701-ABCDEFGHIJK'),
          hasMockTicket2: document.body.textContent.includes('TICKET-E2E-002-LONG-CODE-20260701-ABCDEFGHIJK'),
          hasLocalizedTicketName: Boolean(detailDrawer?.textContent.includes('遇龙河成人票')),
          hasNoEnglishTicketName: !document.body.textContent.includes('Adult Ticket'),
          hasPaymentSuccess: Boolean(detailDrawer?.textContent.includes('支付成功，票码已生成')),
          hasPaymentSuccessResult: Boolean(successResult && isVisible(successResult)),
          hasStateCard: Boolean(stateCard && isVisible(stateCard)),
          hasTicketReadyCopy: Boolean(stateCard?.textContent.includes('票码可用') && stateCard.textContent.includes('不再显示取消入口')),
          hasTicketRegion: Boolean(ticketRegion && isVisible(ticketRegion)),
          scrollWidth: document.documentElement.scrollWidth,
        }
      })()`,
    )
    if (mock && orderCardToneState) {
      Object.assign(orderCardToneState, await evaluate(
        client,
        `(() => {
          const paidCard = document.querySelector('.order-mobile-card[data-order-status="PAID"]')
          return {
            paidAction: paidCard?.textContent.includes('查看凭证') ?? false,
            paidClass: paidCard?.classList.contains('is-paid') ?? false,
            paidStatus: paidCard?.getAttribute('data-order-status') ?? '',
          }
        })()`,
      ))
    }

    await client.send('Emulation.setDeviceMetricsOverride', {
      deviceScaleFactor: 1,
      height: 900,
      mobile: false,
      width: 1280,
    })
    await waitFor(
      client,
      `(() => {
        const detailCard = document.querySelector('.order-detail-card')
        return Boolean(detailCard && getComputedStyle(detailCard).display !== 'none')
      })()`,
      'desktop order detail card',
    )
    await waitFor(client, `Boolean(document.querySelector('.order-detail-card .ticket-code-list'))`, 'desktop ticket codes')
    await waitFor(
      client,
      visibleTextSelector('.order-detail-card .payment-success-result', '支付成功，票码已生成'),
      'desktop payment success result',
    )

    const desktopDetailState = await evaluate(
      client,
      `(() => {
        ${visibleElementScript}
        const detailCard = document.querySelector('.order-detail-card')
        const heading = document.querySelector('.orders-heading')
        const grid = document.querySelector('.orders-workbench-grid')
        const successResult = detailCard?.querySelector('.payment-success-result')
        const stateCard = detailCard?.querySelector('.order-detail-state-card')
        const ticketRegion = detailCard?.querySelector('.ticket-code-list')
        return {
          clientWidth: document.documentElement.clientWidth,
          detailPosition: detailCard ? getComputedStyle(detailCard).position : '',
          detailCardVisible: Boolean(detailCard && isVisible(detailCard)),
          hasOrdersHeading: Boolean(heading),
          hasWorkbenchGrid: Boolean(grid),
          hasPaymentSuccessResult: Boolean(successResult && isVisible(successResult)),
          hasStateCard: Boolean(stateCard && isVisible(stateCard)),
          hasTicketRegion: Boolean(ticketRegion && isVisible(ticketRegion)),
          hasLocalizedTicketName: Boolean(detailCard?.textContent.includes('遇龙河成人票')),
          hasNoEnglishTicketName: !document.body.textContent.includes('Adult Ticket'),
          scrollWidth: document.documentElement.scrollWidth,
        }
      })()`,
    )

    await client.send('Emulation.setDeviceMetricsOverride', {
      deviceScaleFactor: 1,
      height: viewport.height,
      mobile: true,
      width: viewport.width,
    })

    let notPayablePaymentState = null
    if (mock) {
      await navigateApp(client, appUrl)
      await waitFor(client, 'document.readyState === "complete"', 'booking page reload')
      await waitFor(client, enabledSelector('.mobile-action-bar button'), 'second order action')
      await clickSelector(client, '.mobile-action-bar button')
      await waitFor(client, includesText('ORD-E2E-002'), 'second created order')
      await waitFor(client, enabledSelector('.order-mobile-card'), 'second mobile order card')
      await clickSelector(client, '.order-mobile-card')
      await waitFor(
        client,
        `document.querySelector('.mobile-order-detail-drawer')?.textContent.includes('ORD-E2E-002')`,
        'second order drawer',
      )
      mock.state.notPayableOrderNos.add('ORD-E2E-002')
      await waitFor(client, enabledSelector('.mobile-order-detail-drawer .ant-btn-primary'), 'second order pay button')
      await clickSelector(client, '.mobile-order-detail-drawer .ant-btn-primary')
      await waitFor(client, includesText('订单状态不可支付'), 'not payable payment failure')
      notPayablePaymentState = await evaluate(
        client,
        `(() => {
          ${visibleElementScript}
          const drawer = document.querySelector('.mobile-order-detail-drawer')
          const primaryButton = drawer?.querySelector('.ant-btn-primary')
          const refreshButton = [...(drawer?.querySelectorAll('button') ?? [])].find((button) =>
            isVisible(button) && button.textContent.includes('刷新订单')
          )
          return {
            hasNotPayableMessage: Boolean(drawer?.textContent.includes('订单状态不可支付')),
            hasPayFailure: Boolean(drawer?.textContent.includes('支付失败')),
            hasRefreshAction: Boolean(refreshButton && !refreshButton.disabled),
            hasRetryPayLabel: Boolean(drawer?.textContent.includes('继续支付')),
            payButtonDisabled: Boolean(primaryButton?.disabled),
          }
        })()`,
      )
      mock.state.notPayableOrderNos.delete('ORD-E2E-002')
      await clickByText(client, '取消订单')
      await waitFor(client, clickableText('确认取消'), 'cancel confirmation')
      await clickByText(client, '确认取消')
      await waitFor(
        client,
        `document.querySelector('.mobile-order-detail-drawer')?.textContent.includes('已取消')`,
        'cancelled order status',
      )
    }

    const pageState = await evaluate(
      client,
      `(() => {
        ${visibleElementScript}
        const firstCard = document.querySelector('.order-mobile-card')
        const drawer = document.querySelector('.mobile-order-detail-drawer')
        const actionBar = drawer?.querySelector('.order-detail-actions')
        return {
          clientWidth: document.documentElement.clientWidth,
          hasOrder: document.body.textContent.includes('ORD-E2E-001'),
          hasCancelledSecondOrder: document.querySelector('.mobile-order-detail-drawer')?.textContent.includes('ORD-E2E-002') &&
            document.querySelector('.mobile-order-detail-drawer')?.textContent.includes('已取消'),
          hasCancelledTicketCopy: Boolean(drawer?.textContent.includes('已取消订单不会生成入园票码')),
          hasCancelledStateCard: Boolean(drawer?.querySelector('.order-detail-state-card')?.textContent.includes('只读订单')),
          hasOrdersHeading: Boolean(document.querySelector('.orders-heading')),
          hasOrdersListCard: Boolean(document.querySelector('.orders-list-card')),
          hasWorkflowStrip: Boolean(document.querySelector('.orders-workflow-strip')),
          hasWorkflowCopy: document.querySelector('.orders-workflow-strip')?.textContent.includes('先从列表选择订单') &&
            document.querySelector('.orders-workflow-strip')?.textContent.includes('查看票码'),
          hasSecondOrder: document.body.textContent.includes('ORD-E2E-002'),
          hidesCancelledStateActions: !actionBar || !isVisible(actionBar),
          heading: document.querySelector('.page-heading h1')?.textContent || '',
          mobileCardFits: firstCard ? firstCard.scrollWidth === firstCard.clientWidth : false,
          mobileDetailDrawerVisible: getComputedStyle(document.querySelector('.mobile-order-detail-drawer')).display !== 'none',
          mobileOrdersVisible: getComputedStyle(document.querySelector('.orders-mobile-list')).display !== 'none',
          orderTableHidden: getComputedStyle(document.querySelector('.orders-table')).display === 'none',
          scrollWidth: document.documentElement.scrollWidth,
        }
      })()`,
    )
    if (mock && orderCardToneState) {
      Object.assign(orderCardToneState, await evaluate(
        client,
        `(() => {
          const cancelledCard = document.querySelector('.order-mobile-card[data-order-status="CANCELLED"]')
          return {
            cancelledAction: cancelledCard?.textContent.includes('查看详情') ?? false,
            cancelledClass: cancelledCard?.classList.contains('is-cancelled') ?? false,
            cancelledStatus: cancelledCard?.getAttribute('data-order-status') ?? '',
          }
        })()`,
      ))
    }

    let quotaPaymentState = null
    if (mock) {
      await navigateApp(client, appUrl)
      await waitFor(client, 'document.readyState === "complete"', 'booking page before quota order')
      await waitFor(client, enabledSelector('.mobile-action-bar button'), 'third order action')
      await clickSelector(client, '.mobile-action-bar button')
      await waitFor(client, includesText('ORD-E2E-003'), 'third created order')
      await waitFor(client, clickableText('ORD-E2E-003'), 'third mobile order card')
      await clickByText(client, 'ORD-E2E-003')
      await waitFor(
        client,
        `document.querySelector('.mobile-order-detail-drawer')?.textContent.includes('ORD-E2E-003')`,
        'third order drawer',
      )
      mock.state.quotaNotEnoughOrderNos.add('ORD-E2E-003')
      await waitFor(client, enabledSelector('.mobile-order-detail-drawer .ant-btn-primary'), 'third order pay button')
      await clickSelector(client, '.mobile-order-detail-drawer .ant-btn-primary')
      await waitFor(client, includesText('当前时段余票不足'), 'quota not enough payment failure')
      quotaPaymentState = await evaluate(
        client,
        `(() => {
          ${visibleElementScript}
          const drawer = document.querySelector('.mobile-order-detail-drawer')
          const primaryButton = drawer?.querySelector('.ant-btn-primary')
          const refreshButton = [...(drawer?.querySelectorAll('button') ?? [])].find((button) =>
            isVisible(button) && button.textContent.includes('刷新订单')
          )
          return {
            hasPayFailure: Boolean(drawer?.textContent.includes('支付失败')),
            hasQuotaMessage: Boolean(drawer?.textContent.includes('当前时段余票不足')),
            hasRefreshAction: Boolean(refreshButton && !refreshButton.disabled),
            hasRetryPayLabel: Boolean(drawer?.textContent.includes('继续支付')),
            payButtonDisabled: Boolean(primaryButton?.disabled),
          }
        })()`,
      )
      mock.state.quotaNotEnoughOrderNos.delete('ORD-E2E-003')
      await clickByText(client, '取消订单')
      await waitFor(client, clickableText('确认取消'), 'quota order cancel confirmation')
      await clickByText(client, '确认取消')
      await waitFor(
        client,
        `document.querySelector('.mobile-order-detail-drawer')?.textContent.includes('已取消')`,
        'quota order cancelled status',
      )
    }

    let cancelNotAllowedState = null
    if (mock) {
      await navigateApp(client, appUrl)
      await waitFor(client, 'document.readyState === "complete"', 'booking page before cancel failure order')
      await waitFor(client, enabledSelector('.mobile-action-bar button'), 'fourth order action')
      await clickSelector(client, '.mobile-action-bar button')
      await waitFor(client, includesText('ORD-E2E-004'), 'fourth created order')
      await waitFor(client, clickableText('ORD-E2E-004'), 'fourth mobile order card')
      await clickByText(client, 'ORD-E2E-004')
      await waitFor(
        client,
        `document.querySelector('.mobile-order-detail-drawer')?.textContent.includes('ORD-E2E-004')`,
        'fourth order drawer',
      )
      mock.state.cancelNotAllowedOrderNos.add('ORD-E2E-004')
      await clickByText(client, '取消订单')
      await waitFor(client, clickableText('确认取消'), 'cancel failure confirmation')
      await clickByText(client, '确认取消')
      await waitFor(client, includesText('当前订单状态不可取消'), 'cancel not allowed failure')
      cancelNotAllowedState = await evaluate(
        client,
        `(() => {
          ${visibleElementScript}
          const drawer = document.querySelector('.mobile-order-detail-drawer')
          const buttons = [...(drawer?.querySelectorAll('button') ?? [])]
          const visibleEnabledButtonTexts = buttons
            .filter((button) => isVisible(button) && !button.disabled)
            .map((button) => button.textContent.trim())
          return {
            hasCancelAction: visibleEnabledButtonTexts.some((text) => text.includes('取消订单')),
            hasCancelFailure: Boolean(drawer?.textContent.includes('取消失败')),
            hasNotCancelableMessage: Boolean(drawer?.textContent.includes('当前订单状态不可取消')),
            hasPayAction: visibleEnabledButtonTexts.some((text) => text.includes('继续支付')),
            hasRequestId: Boolean(drawer?.textContent.includes('请求编号：e2e-request')),
            hasCancelledStatus: Boolean(drawer?.textContent.includes('已取消')),
            stillPending: Boolean(drawer?.textContent.includes('待支付')),
          }
        })()`,
      )
      mock.state.cancelNotAllowedOrderNos.delete('ORD-E2E-004')
      await clickByText(client, '取消订单')
      await waitFor(client, clickableText('确认取消'), 'cancel failure order retry confirmation')
      await clickByText(client, '确认取消')
      await waitFor(
        client,
        `document.querySelector('.mobile-order-detail-drawer')?.textContent.includes('已取消')`,
        'cancel failure order cancelled status',
      )
    }

    let orderStatusFilterState = null
    let orderDetailErrorState = null
    let paidFilterShowsDetailLoading = false
    let paidFilterShowsResult = false
    if (mock) {
      await navigateApp(client, appUrl)
      await waitFor(client, 'document.readyState === "complete"', 'booking page after status filter reload')
      await clickByText(client, '我的订单')
      await waitFor(client, `document.querySelector('.page-heading h1')?.textContent.includes('我的订单')`, 'orders page for status filters')
      await waitFor(client, includesText('ORD-E2E-001'), 'all status includes paid order')
      await waitFor(client, includesText('ORD-E2E-002'), 'all status includes cancelled order')

      await fillSelector(client, '.orders-search input', 'ORD-NOT-FOUND')
      await waitFor(
        client,
        `document.querySelector('.orders-mobile-list')?.textContent.includes('未找到匹配订单')`,
        'empty search result',
      )
      await clickByText(client, '清空筛选')
      await waitFor(
        client,
        `(() => {
          const list = document.querySelector('.orders-mobile-list')
          return Boolean(list?.textContent.includes('ORD-E2E-001') && list.textContent.includes('ORD-E2E-002'))
        })()`,
        'orders restored after clearing search',
      )
      await fillSelector(client, '.orders-date-filter input', '2026-07-02')
      await waitFor(
        client,
        `document.querySelector('.orders-mobile-list')?.textContent.includes('未找到匹配订单')`,
        'empty date filter result',
      )
      await clickByText(client, '清空筛选')
      await waitFor(
        client,
        `(() => {
          const list = document.querySelector('.orders-mobile-list')
          return Boolean(list?.textContent.includes('ORD-E2E-001') && list.textContent.includes('ORD-E2E-002'))
        })()`,
        'orders restored after clearing date filter',
      )

      await clickSegmentedOption(client, '待支付')
      await waitFor(client, includesText('当前状态暂无订单'), 'empty status filter result')
      await waitFor(client, clickableText('查看全部'), 'show all action after empty status filter')
      await clickByText(client, '查看全部')
      await waitFor(
        client,
        `(() => {
          const list = document.querySelector('.orders-mobile-list')
          return Boolean(list?.textContent.includes('ORD-E2E-001') && list.textContent.includes('ORD-E2E-002'))
        })()`,
        'all orders restored after empty status filter',
      )

      await clickSegmentedOption(client, '已支付')
      await waitFor(
        client,
        `(() => {
          const list = document.querySelector('.orders-mobile-list')
          return Boolean(list?.textContent.includes('ORD-E2E-001') && !list.textContent.includes('ORD-E2E-002'))
        })()`,
        'paid status filter',
      )
      await clickSelector(client, '.order-mobile-card')
      await waitFor(
        client,
        visibleTextSelector('.mobile-order-detail-drawer .order-detail-loading', '订单详情加载中'),
        'historical paid order detail loading',
      )
      paidFilterShowsDetailLoading = await evaluate(
        client,
        visibleTextSelector('.mobile-order-detail-drawer .order-detail-loading', '订单详情加载中'),
      )
      await waitFor(
        client,
        visibleTextSelector('.mobile-order-detail-drawer .payment-success-result', '支付成功，票码已生成'),
        'historical paid order result',
      )
      paidFilterShowsResult = await evaluate(
        client,
        visibleTextSelector('.mobile-order-detail-drawer .payment-success-result', '支付成功，票码已生成'),
      )
      await clickSelector(client, '.mobile-order-detail-drawer .ant-drawer-close')
      await waitFor(
        client,
        `(() => {
          ${visibleElementScript}
          const drawer = document.querySelector('.mobile-order-detail-drawer')
          return !drawer || !isVisible(drawer)
        })()`,
        'historical paid order drawer closed',
      )
      await clickSegmentedOption(client, '已取消')
      await waitFor(
        client,
        `(() => {
          const list = document.querySelector('.orders-mobile-list')
          return Boolean(
            list?.textContent.includes('ORD-E2E-002') &&
            list.textContent.includes('ORD-E2E-003') &&
            list.textContent.includes('ORD-E2E-004') &&
            !list.textContent.includes('ORD-E2E-001')
          )
        })()`,
        'cancelled status filter',
      )
      orderStatusFilterState = await evaluate(
        client,
        `(() => ({
          cancelledFilterShowsCancelledOnly: document.querySelector('.orders-mobile-list')?.textContent.includes('ORD-E2E-002') &&
            document.querySelector('.orders-mobile-list')?.textContent.includes('ORD-E2E-003') &&
            document.querySelector('.orders-mobile-list')?.textContent.includes('ORD-E2E-004') &&
            !document.querySelector('.orders-mobile-list')?.textContent.includes('ORD-E2E-001'),
          emptyStatusFilterCleared: !document.body.textContent.includes('当前状态暂无订单'),
          heading: document.querySelector('.page-heading h1')?.textContent || '',
          searchCleared: document.querySelector('.orders-search input')?.value === '',
          workflowActiveStatus: document.querySelector('.orders-workflow-strip')?.getAttribute('data-active-status') ?? '',
          workflowHasCancelledCopy: document.querySelector('.orders-workflow-strip')?.textContent.includes('已取消订单不会生成票码'),
          scrollWidth: document.documentElement.scrollWidth,
          clientWidth: document.documentElement.clientWidth,
        }))()`,
      )
      orderStatusFilterState.paidFilterShowsDetailLoading = paidFilterShowsDetailLoading
      orderStatusFilterState.paidFilterShowsResult = paidFilterShowsResult

      mock.state.orders.push(createOrder('ORD-E2E-404', 'CREATED'))
      mock.state.detailFailureOrderNos.add('ORD-E2E-404')
      await navigateApp(client, appUrl)
      await waitFor(client, 'document.readyState === "complete"', 'booking page after detail error reload')
      await clickByText(client, '我的订单')
      await waitFor(client, `document.querySelector('.page-heading h1')?.textContent.includes('我的订单')`, 'orders page for detail error')
      await clickSegmentedOption(client, '待支付')
      await waitFor(
        client,
        `(() => {
          const list = document.querySelector('.orders-mobile-list')
          return Boolean(list?.textContent.includes('ORD-E2E-404') && !list.textContent.includes('ORD-E2E-001'))
        })()`,
        'detail error order in pending filter',
      )
      await clickSelector(client, '.order-mobile-card')
      await waitFor(
        client,
        visibleTextSelector('.mobile-order-detail-drawer .ant-alert-error', '详情加载失败'),
        'detail error state',
      )
      await waitFor(client, includesText('请求编号：e2e-request'), 'detail error request id')
      orderDetailErrorState = await evaluate(
        client,
        `(() => {
          ${visibleElementScript}
          const drawer = document.querySelector('.mobile-order-detail-drawer')
          const error = drawer?.querySelector('.ant-alert-error')
          const actions = drawer?.querySelector('.order-detail-actions')
          return {
            hasCancelAction: Boolean(drawer?.textContent.includes('取消订单')),
            hasDetailError: Boolean(error && isVisible(error) && error.textContent.includes('详情加载失败')),
            hasOrderNotFoundMessage: Boolean(error?.textContent.includes('Order not found')),
            hasPayAction: Boolean(drawer?.textContent.includes('继续支付')),
            hasPendingTicketAlert: Boolean(drawer?.textContent.includes('订单待支付')),
            hasRequestId: Boolean(error?.textContent.includes('请求编号：e2e-request')),
            hasRetryAction: Boolean(drawer?.textContent.includes('重试加载')),
            hasStateActions: Boolean(actions && isVisible(actions)),
          }
        })()`,
      )
      await clickSelector(client, '.mobile-order-detail-drawer .ant-drawer-close')
      await waitFor(
        client,
        `(() => {
          ${visibleElementScript}
          const drawer = document.querySelector('.mobile-order-detail-drawer')
          return !drawer || !isVisible(drawer)
        })()`,
        'detail error drawer closed',
      )
    }

    if (mock) {
      await clickByText(client, '退出')
      await waitFor(client, headerIncludesText('未登录'), 'logged-out session badge after logout')
      await waitFor(client, `document.querySelector('.auth-status')?.textContent.includes('未登录')`, 'logged-out auth status')
    }

    assertVisitorE2eState({
      bookingStepState,
      cancelNotAllowedState,
      catalogFallbackState,
      desktopAuthActionState,
      desktopBookingVisualState,
      desktopDetailState,
      e2ePhone,
      e2ePassword,
      e2eUsername,
      emptyOrdersState,
      emptyTimeSlotsState,
      loggedOutOrdersState,
      mobileBookingVisualState,
      mobileDateStripState,
      mobileDetailActionState,
      mobileTicketCardState,
      mock,
      notPayablePaymentState,
      orderCardToneState,
      orderDetailErrorState,
      orderStatusFilterState,
      pageState,
      paidPageState,
      quotaPaymentState,
      sessionFailureState,
      timeSlotFallbackState,
      visitorShellState,
    })
    await client.send('Emulation.setDeviceMetricsOverride', {
      deviceScaleFactor: 1,
      height: 900,
      mobile: false,
      width: 1280,
    })
    await navigateApp(client, `${appUrl}#/admin`)
    await waitFor(client, 'document.readyState === "complete"', 'desktop page load before admin shell smoke')
    await waitFor(client, includesText('运营后台登录'), 'admin login gate')
    await waitFor(client, includesText('返回游客端'), 'admin visitor return')
    const adminLoggedOutState = await evaluate(
      client,
      `(() => ({
        hasLoginGate: Boolean(document.querySelector('.admin-login-gate')),
        hasLoginCard: Boolean(document.querySelector('.admin-login-gate-card')),
        hidesAdminHeader: !Boolean(document.querySelector('.admin-app-header')),
        hidesAdminShell: !Boolean(document.querySelector('.admin-shell')),
        hidesAdminSider: !Boolean(document.querySelector('.admin-sider')),
        hidesAdminMobileTabbar: !Boolean(document.querySelector('.admin-mobile-tabbar')),
        hidesAccessCard: !Boolean(document.querySelector('.admin-access-card')),
        hidesWorkbenchGrid: !Boolean(document.querySelector('.admin-workbench-grid')),
        hidesAuditSearchPanel: !document.body.textContent.includes('退款审计检索'),
        hidesCheckInFailureAuditSearchPanel: !document.body.textContent.includes('核验失败审计'),
        hidesAuditSearchRows: !document.body.textContent.includes('暴雨停航') &&
          !document.body.textContent.includes('mock-refund-request-260628-004') &&
          !document.body.textContent.includes('儿童票临时取消'),
        hidesCheckInFailureAuditSearchRows: !document.body.textContent.includes('mock-check-in-failure-260701-001') &&
          !document.body.textContent.includes('TK-MISSING-260701'),
        hidesMaskedPhone: !document.body.textContent.includes('139****2222'),
        hidesOrderRows: !document.body.textContent.includes('YT2606280001'),
        hidesReportRows: !document.body.textContent.includes('遇龙河竹筏漂流'),
        hidesReportTotals: !document.body.textContent.includes('¥ 30220.00'),
      }))()`,
    )
    await fillPlaceholder(client, '请输入管理员账号', 'admin')
    await fillPlaceholder(client, '请输入密码', 'demo-secret')
    await clickSelector(client, '.admin-login-gate-card button[type="submit"]')
    await waitFor(client, includesText('演示管理员'), 'mock admin session')
    adminShellState = await evaluate(
      client,
      `(() => {
        const contentRoots = [document.body, document.querySelector('#root'), document.querySelector('.app-shell')]
          .filter(Boolean)
        const clientWidth = document.documentElement.clientWidth
          const scrollWidth = Math.max(...contentRoots.map((element) => element.scrollWidth))
          return {
            clientWidth,
          hasAdminOnlyNav: ['工作台', '票种', '报表', '订单', '审计'].every((label) =>
            document.querySelector('.admin-sider')?.textContent.includes(label)
          ) && !Boolean(document.querySelector('.admin-sider')?.textContent.includes('游客购票')),
          hasAdminShell: Boolean(document.querySelector('.admin-shell')),
          hasAdminSession: document.body.textContent.includes('管理员会话'),
          hasBackToVisitorAction: [...document.querySelectorAll('button')].some((button) =>
            button.textContent.includes('返回游客端') && !button.disabled
          ),
          hasAdminHeading: Boolean(document.querySelector('.admin-heading')),
          hasAuditBoundary: document.body.textContent.includes('审计留痕'),
          hasAuditWorkspace: Boolean(document.querySelector('.admin-audit-workspace-card')),
          hasCsrfBoundary: document.body.textContent.includes('防伪请求头'),
          hasHttpOnlyBoundary: document.body.textContent.includes('服务端会话'),
          hasMockAuthMode: document.body.textContent.includes('演示认证'),
          hasMockOrdersMode: document.body.textContent.includes('演示订单'),
          hasMockReportsMode: document.body.textContent.includes('演示报表'),
          hasMockAuditMode: document.body.textContent.includes('演示审计'),
          hasMockCheckInAuditMode: document.body.textContent.includes('演示核验审计'),
          hasMockCheckInFailureAuditMode: document.body.textContent.includes('演示失败审计'),
          hasOverviewEntryCards: document.querySelectorAll('.admin-page-entry-card').length === 4 &&
            document.body.textContent.includes('进入票种管理') &&
            document.body.textContent.includes('进入运营报表') &&
            document.body.textContent.includes('进入订单运营') &&
            document.body.textContent.includes('进入审计导出'),
          hasAuthenticatedWorkbench: Boolean(document.querySelector('.admin-workbench-grid.is-authenticated')),
          hasAuthenticatedAccessSummary: Boolean(document.querySelector('.admin-access-summary')),
          hasOperationCards: document.querySelectorAll('.admin-operation-card').length >= 3,
          hasOperationsWorkflowStrip: Boolean(document.querySelector('.admin-operations-workflow-strip')),
          hasOperationsWorkflowCopy:
            document.body.textContent.includes('先读数据，再管理票种，最后执行状态变更并回到审计证据') &&
            document.body.textContent.includes('1. 看报表') &&
            document.body.textContent.includes('2. 管票种') &&
            document.body.textContent.includes('3. 查订单') &&
            document.body.textContent.includes('4. 做变更') &&
            document.body.textContent.includes('5. 留证据'),
          operationsWorkflowItemCount: document.querySelectorAll('.admin-operations-workflow-item').length,
          hasOperationsBoundaryStrip: Boolean(document.querySelector('.admin-operations-boundary-strip')),
          hasOperationsBoundaryCopy:
            document.body.textContent.includes('后台操作按只读视图、状态变更、审计导出分区推进') &&
            document.body.textContent.includes('不展示完整手机号或证件号') &&
            document.body.textContent.includes('真实后端接入时必须审计留痕') &&
            document.body.textContent.includes('由后端计算状态、金额和库存') &&
            document.body.textContent.includes('错误态保留错误码和请求编号'),
          hasTicketsWorkspace: Boolean(document.querySelector('.admin-tickets-workspace-card')),
          hasOrdersWorkspace: Boolean(document.querySelector('.admin-orders-workspace-card')),
          hasOrderReadModel: document.body.textContent.includes('订单运营列表') &&
            document.body.textContent.includes('YT2606280001'),
          hasBatchCheckInPanel: document.body.textContent.includes('批量票码核验') &&
            document.body.textContent.includes('状态变更只提交待核验票码'),
          hasBatchCheckInAction: [...document.querySelectorAll('.admin-batch-check-in-action')].some((button) =>
            button.textContent.includes('批量核验') && button.disabled
          ),
          hasBatchUndoCheckInPanel: document.body.textContent.includes('批量撤销核验') &&
            document.body.textContent.includes('状态变更只提交待撤销票码'),
          hasBatchUndoCheckInAction: [...document.querySelectorAll('.admin-batch-undo-check-in-action')].some((button) =>
            button.textContent.includes('批量撤销') && button.disabled
          ),
          hasReportWorkspace: Boolean(document.querySelector('.admin-report-workspace-card')),
          hasReportReadModel: document.body.textContent.includes('运营报表') &&
            document.body.textContent.includes('统计周期') &&
            document.body.textContent.includes('趋势仅显示有订单活动时间桶') &&
            document.body.textContent.includes('产品维度') &&
            document.body.textContent.includes('小时趋势') &&
            document.body.textContent.includes('每日趋势') &&
            document.body.textContent.includes('月度趋势'),
          hasWorkbenchGrid: Boolean(document.querySelector('.admin-workbench-grid')),
          hasCsvExportAction: [...document.querySelectorAll('.admin-report-export-action')].some((button) =>
            button.textContent.includes('导出订单 CSV') && !button.disabled
          ),
          hasXlsxExportAction: [...document.querySelectorAll('.admin-report-xlsx-export-action')].some((button) =>
            button.textContent.includes('导出订单 XLSX') && !button.disabled
          ),
          hasCheckInLogCsvExportAction: [...document.querySelectorAll('.admin-check-in-log-csv-export-action')].some((button) =>
            button.textContent.includes('导出核验 CSV') && !button.disabled
          ),
          hasCheckInLogXlsxExportAction: [...document.querySelectorAll('.admin-check-in-log-xlsx-export-action')].some((button) =>
            button.textContent.includes('导出核验 XLSX') && !button.disabled
          ),
          hasCheckInFailureLogCsvExportAction: [...document.querySelectorAll('.admin-check-in-failure-log-csv-export-action')].some((button) =>
            button.textContent.includes('导出失败 CSV') && !button.disabled
          ),
          hasCheckInFailureLogXlsxExportAction: [...document.querySelectorAll('.admin-check-in-failure-log-xlsx-export-action')].some((button) =>
            button.textContent.includes('导出失败 XLSX') && !button.disabled
          ),
          hasRefundLogCsvExportAction: [...document.querySelectorAll('.admin-refund-log-csv-export-action')].some((button) =>
            button.textContent.includes('导出退款 CSV') && !button.disabled
          ),
          hasRefundLogXlsxExportAction: [...document.querySelectorAll('.admin-refund-log-xlsx-export-action')].some((button) =>
            button.textContent.includes('导出退款 XLSX') && !button.disabled
          ),
          hasCheckInAuditExportPanel: document.body.textContent.includes('核验审计导出') &&
            document.body.textContent.includes('只读导出：按票码、订单号、操作人和日期导出核验审计 CSV/XLSX'),
          hasCheckInFailureAuditPanel: document.body.textContent.includes('核验失败审计') &&
            document.body.textContent.includes('只读检索：按失败码、票码、操作人和日期定位核验业务失败尝试'),
          hasExportJobsPanel: Boolean(document.querySelector('.admin-export-jobs-panel')),
          hasExportJobsBoundary: document.body.textContent.includes('异步导出任务') &&
            document.body.textContent.includes('创建任务必须走管理员会话和防伪校验') &&
            document.body.textContent.includes('不提交管理员内部编号、任务状态、文件名、存储位置或下载链接') &&
            document.body.textContent.includes('前端不读取后端存储位置'),
          hasMockExportJobsMode: document.body.textContent.includes('演示导出任务'),
          hasExportJobRows: document.body.textContent.includes('mock-export-job-order-csv-260701') &&
            document.body.textContent.includes('mock-export-job-check-in-xlsx-260701') &&
            document.body.textContent.includes('mock-export-job-failure-csv-260701'),
          hasExportJobCreateAction: [...document.querySelectorAll('.admin-export-job-create-action')].some((button) =>
            button.textContent.includes('创建任务') && !button.disabled
          ),
          hasExportJobDownloadBoundary: [...document.querySelectorAll('.admin-export-job-download-action')].some((button) =>
            button.textContent.includes('下载') && !button.disabled
          ) && [...document.querySelectorAll('.admin-export-job-download-action')].some((button) =>
            button.textContent.includes('下载') && button.disabled
          ),
          hasNoExportJobInternalFields: !document.body.textContent.includes('13911112222') &&
            !document.body.textContent.includes('11010519491231002X') &&
            !document.body.textContent.includes('sessionToken') &&
            !document.body.textContent.includes('csrfToken') &&
            !document.body.textContent.includes('passwordHash') &&
            !document.body.textContent.includes('SELECT '),
          hasMaskedPhone: document.body.textContent.includes('139****2222'),
          hasNoFullMockPhone: !document.body.textContent.includes('13911112222'),
          hasDisabledFutureActions: [...document.querySelectorAll('.admin-card-stack button:disabled')].some((button) =>
            button.textContent.includes('后续接入')
          ),
          hasNoLegacyRefundEntry: ![...document.querySelectorAll('button')].some((button) =>
            button.textContent.includes('进入退款处理')
          ),
          hasNoExecutableCheckInAction: ![...document.querySelectorAll('button')].some((button) =>
            button.textContent.includes('核验通过')
          ),
          orderFutureActionsDisabled: (() => {
            const actions = [...document.querySelectorAll('.admin-order-future-action')]
            return actions.length > 0 && actions.every((button) => button.disabled)
          })(),
          heading: document.querySelector('.page-heading h1')?.textContent.trim() || '',
          scrollWidth,
        }
      })()`,
    )
    adminPageSeparationState = {
      overview: await evaluate(
        client,
        `(() => ({
          hash: location.hash,
          heading: document.querySelector('.page-heading h1')?.textContent.trim() || '',
          hasOverviewEntryCards: document.querySelectorAll('.admin-page-entry-card').length === 4,
          hasTicketsWorkspace: Boolean(document.querySelector('.admin-tickets-workspace-card')),
          hasReportWorkspace: Boolean(document.querySelector('.admin-report-workspace-card')),
          hasOrdersWorkspace: Boolean(document.querySelector('.admin-orders-workspace-card')),
          hasAuditWorkspace: Boolean(document.querySelector('.admin-audit-workspace-card')),
        }))()`,
      ),
    }
    await openAdminSidePage(client, '票种')
    await waitFor(client, `document.querySelector('.page-heading h1')?.textContent.includes('票种管理')`, 'admin tickets page')
    await waitFor(client, includesText('价格变更需管理员会话与审计记录'), 'admin tickets audit boundary')
    adminShellState = {
      ...adminShellState,
      ...(await evaluate(
        client,
        `(() => ({
          hasTicketsWorkspace: Boolean(document.querySelector('.admin-tickets-workspace-card')),
          hasTicketsPanel: Boolean(document.querySelector('.admin-tickets-panel')),
          hasTicketRows: document.body.textContent.includes('遇龙河成人票') &&
            document.body.textContent.includes('遇龙河儿童票') &&
            document.body.textContent.includes('遇龙河团队票'),
          hasTicketActions: Boolean(document.querySelector('.admin-ticket-create-action')) &&
            Boolean(document.querySelector('.admin-ticket-edit-action')) &&
            Boolean(document.querySelector('.admin-ticket-price-action')) &&
            Boolean(document.querySelector('.admin-ticket-status-action')) &&
            Boolean(document.querySelector('.admin-ticket-delete-action')),
          hasTicketAuditBoundary: document.body.textContent.includes('真实后端接入时保存、改价、上下架和删除都必须写入审计'),
        }))()`,
      )),
    }
    adminPageSeparationState.tickets = await evaluate(
      client,
      `(() => ({
        hash: location.hash,
        heading: document.querySelector('.page-heading h1')?.textContent.trim() || '',
        hasAccessCard: Boolean(document.querySelector('.admin-access-card')),
        hasTicketsWorkspace: Boolean(document.querySelector('.admin-tickets-workspace-card')),
        hasReportWorkspace: Boolean(document.querySelector('.admin-report-workspace-card')),
        hasOrdersWorkspace: Boolean(document.querySelector('.admin-orders-workspace-card')),
        hasAuditWorkspace: Boolean(document.querySelector('.admin-audit-workspace-card')),
      }))()`,
    )
    await clickSelector(client, '.admin-ticket-create-action')
    await fillPlaceholder(client, '例如 遇龙河成人票', '遇龙河学生票')
    await clickSelector(client, '.admin-ticket-save-action')
    await waitFor(client, includesText('已新增 遇龙河学生票'), 'admin ticket create notice')
    await clickSelector(client, '.admin-ticket-price-action')
    await fillPlaceholder(client, '票种价格', '99')
    await clickSelector(client, '.admin-ticket-save-action')
    await waitFor(client, includesText('¥ 99.00'), 'admin ticket price changed')
    await clickSelector(client, '.admin-ticket-status-action')
    await waitFor(client, includesText('已下架'), 'admin ticket status changed')
    adminTicketsState = await evaluate(
      client,
      `(() => ({
        hasCreatedTicket: document.body.textContent.includes('遇龙河学生票'),
        hasPriceEdited: document.body.textContent.includes('¥ 99.00'),
        hasStatusChanged: document.body.textContent.includes('已下架'),
        hasAuditBoundary: document.body.textContent.includes('价格变更需管理员会话与审计记录'),
        hasNoSensitiveFields: !document.body.textContent.includes('sessionToken') &&
          !document.body.textContent.includes('csrfToken') &&
          !document.body.textContent.includes('passwordHash') &&
          !document.body.textContent.includes('SELECT '),
      }))()`,
    )
    await clickSelector(client, '.admin-ticket-delete-action')
    await clickSelector(client, '.ant-popconfirm-buttons .ant-btn-primary')
    await waitFor(client, includesText('已从 mock 列表删除'), 'admin ticket deleted')
    adminTicketsState = {
      ...adminTicketsState,
      ...(await evaluate(
        client,
        `(() => ({
          hasDeletedTicket: !document.querySelector('.admin-tickets-table')?.textContent.includes('遇龙河学生票'),
        }))()`,
      )),
    }
    await openAdminSidePage(client, '审计')
    await waitFor(client, `document.querySelector('.page-heading h1')?.textContent.includes('审计导出')`, 'admin audit page')
    await waitFor(client, includesText('异步导出任务'), 'admin audit export jobs panel')
    adminShellState = {
      ...adminShellState,
      ...(await evaluate(
        client,
        `(() => ({
          hasAuditWorkspace: Boolean(document.querySelector('.admin-audit-workspace-card')),
          hasMockAuditMode: document.body.textContent.includes('演示审计'),
          hasMockCheckInAuditMode: document.body.textContent.includes('演示核验审计'),
          hasMockCheckInFailureAuditMode: document.body.textContent.includes('演示失败审计'),
          hasCheckInLogCsvExportAction: [...document.querySelectorAll('.admin-check-in-log-csv-export-action')].some((button) =>
            button.textContent.includes('导出核验 CSV') && !button.disabled
          ),
          hasCheckInLogXlsxExportAction: [...document.querySelectorAll('.admin-check-in-log-xlsx-export-action')].some((button) =>
            button.textContent.includes('导出核验 XLSX') && !button.disabled
          ),
          hasCheckInFailureLogCsvExportAction: [...document.querySelectorAll('.admin-check-in-failure-log-csv-export-action')].some((button) =>
            button.textContent.includes('导出失败 CSV') && !button.disabled
          ),
          hasCheckInFailureLogXlsxExportAction: [...document.querySelectorAll('.admin-check-in-failure-log-xlsx-export-action')].some((button) =>
            button.textContent.includes('导出失败 XLSX') && !button.disabled
          ),
          hasRefundLogCsvExportAction: [...document.querySelectorAll('.admin-refund-log-csv-export-action')].some((button) =>
            button.textContent.includes('导出退款 CSV') && !button.disabled
          ),
          hasRefundLogXlsxExportAction: [...document.querySelectorAll('.admin-refund-log-xlsx-export-action')].some((button) =>
            button.textContent.includes('导出退款 XLSX') && !button.disabled
          ),
          hasCheckInAuditExportPanel: document.body.textContent.includes('核验审计导出') &&
            document.body.textContent.includes('只读导出：按票码、订单号、操作人和日期导出核验审计 CSV/XLSX'),
          hasCheckInFailureAuditPanel: document.body.textContent.includes('核验失败审计') &&
            document.body.textContent.includes('只读检索：按失败码、票码、操作人和日期定位核验业务失败尝试'),
          hasExportJobsPanel: Boolean(document.querySelector('.admin-export-jobs-panel')),
          hasExportJobsBoundary: document.body.textContent.includes('异步导出任务') &&
            document.body.textContent.includes('创建任务必须走管理员会话和防伪校验') &&
            document.body.textContent.includes('不提交管理员内部编号、任务状态、文件名、存储位置或下载链接') &&
            document.body.textContent.includes('前端不读取后端存储位置'),
          hasMockExportJobsMode: document.body.textContent.includes('演示导出任务'),
          hasExportJobRows: document.body.textContent.includes('mock-export-job-order-csv-260701') &&
            document.body.textContent.includes('mock-export-job-check-in-xlsx-260701') &&
            document.body.textContent.includes('mock-export-job-failure-csv-260701'),
          hasExportJobCreateAction: [...document.querySelectorAll('.admin-export-job-create-action')].some((button) =>
            button.textContent.includes('创建任务') && !button.disabled
          ),
          hasExportJobDownloadBoundary: [...document.querySelectorAll('.admin-export-job-download-action')].some((button) =>
            button.textContent.includes('下载') && !button.disabled
          ) && [...document.querySelectorAll('.admin-export-job-download-action')].some((button) =>
            button.textContent.includes('下载') && button.disabled
          ),
          hasNoExportJobInternalFields: !document.body.textContent.includes('13911112222') &&
            !document.body.textContent.includes('11010519491231002X') &&
            !document.body.textContent.includes('sessionToken') &&
            !document.body.textContent.includes('csrfToken') &&
            !document.body.textContent.includes('passwordHash') &&
            !document.body.textContent.includes('SELECT '),
        }))()`,
      )),
    }
    adminPageSeparationState.audit = await evaluate(
      client,
      `(() => ({
        hash: location.hash,
        heading: document.querySelector('.page-heading h1')?.textContent.trim() || '',
        hasAccessCard: Boolean(document.querySelector('.admin-access-card')),
        hasReportWorkspace: Boolean(document.querySelector('.admin-report-workspace-card')),
        hasTicketsWorkspace: Boolean(document.querySelector('.admin-tickets-workspace-card')),
        hasOrdersWorkspace: Boolean(document.querySelector('.admin-orders-workspace-card')),
        hasAuditWorkspace: Boolean(document.querySelector('.admin-audit-workspace-card')),
      }))()`,
    )
    await clickSelector(client, '.admin-export-job-create-action')
    await waitFor(client, includesText('mock-export-job-created-001'), 'admin export job mock create result')
    adminExportJobCreateState = await evaluate(
      client,
      `(() => ({
        hasCreatedAlert: document.body.textContent.includes('异步导出任务已创建'),
        hasCreatedJobId: document.body.textContent.includes('mock-export-job-created-001'),
        hasPendingStatus: document.body.textContent.includes('PENDING') ||
          [...document.querySelectorAll('.admin-export-job-table .ant-tag')].some((tag) => tag.textContent.includes('待处理')),
        keepsCreateBoundary: document.body.textContent.includes('前端只提交导出类型、文件格式和允许的筛选条件'),
        hasNoSensitiveExportPayload: !document.body.textContent.includes('13911112222') &&
          !document.body.textContent.includes('11010519491231002X') &&
          !document.body.textContent.includes('sessionToken') &&
          !document.body.textContent.includes('passwordHash') &&
          !document.body.textContent.includes('SELECT '),
      }))()`,
    )
    await openAdminSidePage(client, '报表')
    await waitFor(client, `document.querySelector('.page-heading h1')?.textContent.includes('运营报表')`, 'admin reports page')
    await waitFor(client, includesText('支付对账'), 'admin reports payment reconciliation panel')
    adminShellState = {
      ...adminShellState,
      ...(await evaluate(
        client,
        `(() => ({
          hasReportWorkspace: Boolean(document.querySelector('.admin-report-workspace-card')),
          hasMockReportsMode: document.body.textContent.includes('演示报表'),
          hasReportReadModel: document.body.textContent.includes('运营报表') &&
            document.body.textContent.includes('统计周期') &&
            document.body.textContent.includes('趋势仅显示有订单活动时间桶') &&
            document.body.textContent.includes('产品维度') &&
            document.body.textContent.includes('小时趋势') &&
            document.body.textContent.includes('每日趋势') &&
            document.body.textContent.includes('月度趋势'),
          hasCsvExportAction: [...document.querySelectorAll('.admin-report-export-action')].some((button) =>
            button.textContent.includes('导出订单 CSV') && !button.disabled
          ),
          hasXlsxExportAction: [...document.querySelectorAll('.admin-report-xlsx-export-action')].some((button) =>
            button.textContent.includes('导出订单 XLSX') && !button.disabled
          ),
        }))()`,
      )),
    }
    adminPageSeparationState.reports = await evaluate(
      client,
      `(() => ({
        hash: location.hash,
        heading: document.querySelector('.page-heading h1')?.textContent.trim() || '',
        hasReportWorkspace: Boolean(document.querySelector('.admin-report-workspace-card')),
        hasTicketsWorkspace: Boolean(document.querySelector('.admin-tickets-workspace-card')),
        hasOrdersWorkspace: Boolean(document.querySelector('.admin-orders-workspace-card')),
        hasAuditWorkspace: Boolean(document.querySelector('.admin-audit-workspace-card')),
      }))()`,
    )
    adminReportState = await evaluate(
      client,
      `(() => {
        const reportMetricGrid = document.querySelector('.admin-report-metric-grid')
        const reportMetricColumnCount = reportMetricGrid
          ? getComputedStyle(reportMetricGrid).gridTemplateColumns.split(' ').filter(Boolean).length
          : 0

        return {
          hasNetPaidAmount: document.body.textContent.includes('¥ 30220.00'),
          hasFourColumnSummaryMetrics: reportMetricColumnCount === 4,
          hasPaymentReconciliationPanel: document.body.textContent.includes('支付对账') &&
            document.body.textContent.includes('订单净收款') &&
            document.body.textContent.includes('支付捕获金额') &&
            document.body.textContent.includes('未对账差额') &&
            document.body.textContent.includes('存在差异'),
          hasNoEnglishTicketName: !document.body.textContent.includes('Adult Ticket'),
          hasProductBreakdown: document.body.textContent.includes('遇龙河竹筏漂流') &&
            document.body.textContent.includes('成人票'),
          hasReadOnlyBoundary: document.body.textContent.includes('报表接口只读取运营数据'),
          hasDateFilters: document.querySelector('.admin-report-date-from input')?.value === '2026-06-26' &&
            document.querySelector('.admin-report-date-to input')?.value === '2026-06-28',
          hasZeroFillControl: document.body.textContent.includes('趋势仅显示有订单活动时间桶') &&
            Boolean(document.querySelector('.admin-report-include-empty')),
          hasCsvExportAction: [...document.querySelectorAll('.admin-report-export-action')].some((button) =>
            button.textContent.includes('导出订单 CSV') && !button.disabled
          ),
          hasXlsxExportAction: [...document.querySelectorAll('.admin-report-xlsx-export-action')].some((button) =>
            button.textContent.includes('导出订单 XLSX') && !button.disabled
          ),
          hasPaymentReconciliationCsvExportAction: [...document.querySelectorAll('.admin-payment-reconciliation-csv-export-action')].some((button) =>
            button.textContent.includes('导出对账 CSV') && !button.disabled
          ),
          hasPaymentReconciliationXlsxExportAction: [...document.querySelectorAll('.admin-payment-reconciliation-xlsx-export-action')].some((button) =>
            button.textContent.includes('导出对账 XLSX') && !button.disabled
          ),
          hasProductBreakdownCsvExportAction: [...document.querySelectorAll('.admin-product-breakdown-csv-export-action')].some((button) =>
            button.textContent.includes('导出产品 CSV') && !button.disabled
          ),
          hasProductBreakdownXlsxExportAction: [...document.querySelectorAll('.admin-product-breakdown-xlsx-export-action')].some((button) =>
            button.textContent.includes('导出产品 XLSX') && !button.disabled
          ),
          hasPaymentReconciliationBoundary: document.body.textContent.includes('不展示支付流水号') &&
            !document.body.textContent.includes('transactionNo') &&
            !document.body.textContent.includes('channelTradeNo'),
          hasTrendExportScope: document.body.textContent.includes('趋势 CSV/XLSX 导出跟随当前日期范围和补零口径'),
          hasDailyTrendCsvExportAction: [...document.querySelectorAll('.admin-report-daily-trend-csv-export-action')].some((button) =>
            button.textContent.includes('导出日趋势 CSV') && !button.disabled
          ),
          hasHourlyTrendCsvExportAction: [...document.querySelectorAll('.admin-report-hourly-trend-csv-export-action')].some((button) =>
            button.textContent.includes('导出小时趋势 CSV') && !button.disabled
          ),
          hasMonthlyTrendCsvExportAction: [...document.querySelectorAll('.admin-report-monthly-trend-csv-export-action')].some((button) =>
            button.textContent.includes('导出月趋势 CSV') && !button.disabled
          ),
          hasDailyTrendXlsxExportAction: [...document.querySelectorAll('.admin-report-daily-trend-xlsx-export-action')].some((button) =>
            button.textContent.includes('导出日趋势 XLSX') && !button.disabled
          ),
          hasHourlyTrendXlsxExportAction: [...document.querySelectorAll('.admin-report-hourly-trend-xlsx-export-action')].some((button) =>
            button.textContent.includes('导出小时趋势 XLSX') && !button.disabled
          ),
          hasMonthlyTrendXlsxExportAction: [...document.querySelectorAll('.admin-report-monthly-trend-xlsx-export-action')].some((button) =>
            button.textContent.includes('导出月趋势 XLSX') && !button.disabled
          ),
          hasTrendAmount: document.body.textContent.includes('¥ 11940.00'),
          hasHourlyTrend: document.body.textContent.includes('小时趋势') &&
            document.body.textContent.includes('2026-06-28 14:00') &&
            document.body.textContent.includes('27 单 · 44 张票'),
          hasHourlyTrendAmount: document.body.textContent.includes('¥ 6340.00'),
          hasMonthlyTrend: document.body.textContent.includes('月度趋势') &&
            document.body.textContent.includes('2026-06') &&
            document.body.textContent.includes('134 单 · 215 张票'),
          hasMonthlyTrendAmount: document.body.textContent.includes('¥ 30220.00'),
          hasNoPhone: !document.body.textContent.includes('buyerPhone') &&
            !document.body.textContent.includes('13911112222'),
          hasNoIdNumber: !document.body.textContent.includes('idNumber') &&
            !document.body.textContent.includes('11010519491231002X'),
          hasNoSqlText: !document.body.textContent.includes('SQL'),
        }
      })()`,
    )
    await clickSelector(client, '.admin-report-include-empty')
    await waitFor(client, includesText('趋势补齐空时间桶'), 'admin report zero fill enabled')
    adminReportZeroFillState = await evaluate(
      client,
      `(() => ({
        hasZeroFillCopy: document.body.textContent.includes('趋势补齐空时间桶'),
        hasHourlyZeroBucket: document.body.textContent.includes('2026-06-26 00:00') &&
          document.body.textContent.includes('0 单 · 0 张票'),
      }))()`,
    )
    await evaluate(
      client,
      `(() => {
        const originalCreateObjectUrl = URL.createObjectURL.bind(URL)
        const originalAnchorClick = HTMLAnchorElement.prototype.click
        window.__adminReportTrendDownloads = []
        URL.createObjectURL = (blob) => {
          const entry = {
            blobSize: blob.size,
            blobType: blob.type,
            download: '',
            href: '',
          }
          window.__adminReportTrendDownloads.push(entry)
          window.__lastAdminReportTrendDownload = entry
          return originalCreateObjectUrl(blob)
        }
        HTMLAnchorElement.prototype.click = function () {
          const entry = window.__lastAdminReportTrendDownload
          if (entry && !entry.download) {
            entry.download = this.download
            entry.href = this.href
            return
          }

          window.__adminReportTrendDownloads.push({
            blobSize: 0,
            blobType: '',
            download: this.download,
            href: this.href,
          })
        }
        window.__restoreAdminReportTrendDownloads = () => {
          URL.createObjectURL = originalCreateObjectUrl
          HTMLAnchorElement.prototype.click = originalAnchorClick
        }
        return true
      })()`,
    )
    await clickSelector(client, '.admin-report-hourly-trend-csv-export-action')
    await waitFor(
      client,
      `window.__adminReportTrendDownloads?.some((entry) => entry.download === 'admin-hourly-trend-20260626-20260628.csv')`,
      'admin hourly trend CSV mock download',
    )
    await clickSelector(client, '.admin-report-hourly-trend-xlsx-export-action')
    await waitFor(
      client,
      `window.__adminReportTrendDownloads?.some((entry) => entry.download === 'admin-hourly-trend-20260626-20260628.xlsx')`,
      'admin hourly trend XLSX mock download',
    )
    await clickSelector(client, '.admin-payment-reconciliation-csv-export-action')
    await waitFor(
      client,
      `window.__adminReportTrendDownloads?.some((entry) => entry.download === 'admin-payment-reconciliation-20260626-20260628.csv')`,
      'admin payment reconciliation CSV mock download',
    )
    await clickSelector(client, '.admin-payment-reconciliation-xlsx-export-action')
    await waitFor(
      client,
      `window.__adminReportTrendDownloads?.some((entry) => entry.download === 'admin-payment-reconciliation-20260626-20260628.xlsx')`,
      'admin payment reconciliation XLSX mock download',
    )
    await clickSelector(client, '.admin-product-breakdown-csv-export-action')
    await waitFor(
      client,
      `window.__adminReportTrendDownloads?.some((entry) => entry.download === 'admin-product-breakdown-20260626-20260628.csv')`,
      'admin product breakdown CSV mock download',
    )
    await clickSelector(client, '.admin-product-breakdown-xlsx-export-action')
    await waitFor(
      client,
      `window.__adminReportTrendDownloads?.some((entry) => entry.download === 'admin-product-breakdown-20260626-20260628.xlsx')`,
      'admin product breakdown XLSX mock download',
    )
    adminReportTrendExportState = await evaluate(
      client,
      `(() => ({
        hasHourlyTrendCsvDownload: window.__adminReportTrendDownloads?.some((entry) =>
          entry.blobType === 'text/csv;charset=utf-8' &&
          entry.blobSize > 0 &&
          entry.download === 'admin-hourly-trend-20260626-20260628.csv'
        ),
        hasHourlyTrendXlsxDownload: window.__adminReportTrendDownloads?.some((entry) =>
          entry.blobType === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' &&
          entry.blobSize > 0 &&
          entry.download === 'admin-hourly-trend-20260626-20260628.xlsx'
        ),
        hasPaymentReconciliationCsvDownload: window.__adminReportTrendDownloads?.some((entry) =>
          entry.blobType === 'text/csv;charset=utf-8' &&
          entry.blobSize > 0 &&
          entry.download === 'admin-payment-reconciliation-20260626-20260628.csv'
        ),
        hasPaymentReconciliationXlsxDownload: window.__adminReportTrendDownloads?.some((entry) =>
          entry.blobType === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' &&
          entry.blobSize > 0 &&
          entry.download === 'admin-payment-reconciliation-20260626-20260628.xlsx'
        ),
        hasProductBreakdownCsvDownload: window.__adminReportTrendDownloads?.some((entry) =>
          entry.blobType === 'text/csv;charset=utf-8' &&
          entry.blobSize > 0 &&
          entry.download === 'admin-product-breakdown-20260626-20260628.csv'
        ),
        hasProductBreakdownXlsxDownload: window.__adminReportTrendDownloads?.some((entry) =>
          entry.blobType === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' &&
          entry.blobSize > 0 &&
          entry.download === 'admin-product-breakdown-20260626-20260628.xlsx'
        ),
      }))()`,
    )
    await evaluate(client, 'window.__restoreAdminReportTrendDownloads?.()')
    await openAdminSidePage(client, '订单')
    await waitFor(client, `document.querySelector('.page-heading h1')?.textContent.includes('订单运营')`, 'admin orders page')
    await waitFor(client, includesText('订单运营列表'), 'admin orders list page')
    adminShellState = {
      ...adminShellState,
      ...(await evaluate(
        client,
        `(() => ({
          hasOrdersWorkspace: Boolean(document.querySelector('.admin-orders-workspace-card')),
          hasMockOrdersMode: document.body.textContent.includes('演示订单'),
          hasOrderReadModel: document.body.textContent.includes('订单运营列表') &&
            document.body.textContent.includes('YT2606280001'),
          hasBatchCheckInPanel: document.body.textContent.includes('批量票码核验') &&
            document.body.textContent.includes('状态变更只提交待核验票码'),
          hasBatchCheckInAction: [...document.querySelectorAll('.admin-batch-check-in-action')].some((button) =>
            button.textContent.includes('批量核验') && button.disabled
          ),
          hasBatchUndoCheckInPanel: document.body.textContent.includes('批量撤销核验') &&
            document.body.textContent.includes('状态变更只提交待撤销票码'),
          hasBatchUndoCheckInAction: [...document.querySelectorAll('.admin-batch-undo-check-in-action')].some((button) =>
            button.textContent.includes('批量撤销') && button.disabled
          ),
          hasMaskedPhone: document.body.textContent.includes('139****2222'),
          hasNoFullMockPhone: !document.body.textContent.includes('13911112222'),
          hasDisabledFutureActions: [...document.querySelectorAll('.admin-card-stack button:disabled')].some((button) =>
            button.textContent.includes('后续接入')
          ),
          hasNoLegacyRefundEntry: ![...document.querySelectorAll('button')].some((button) =>
            button.textContent.includes('进入退款处理')
          ),
          hasNoExecutableCheckInAction: ![...document.querySelectorAll('button')].some((button) =>
            button.textContent.includes('核验通过')
          ),
          orderFutureActionsDisabled: (() => {
            const actions = [...document.querySelectorAll('.admin-order-future-action')]
            return actions.length > 0 && actions.every((button) => button.disabled)
          })(),
        }))()`,
      )),
    }
    adminPageSeparationState.orders = await evaluate(
      client,
      `(() => ({
        hash: location.hash,
        heading: document.querySelector('.page-heading h1')?.textContent.trim() || '',
        hasReportWorkspace: Boolean(document.querySelector('.admin-report-workspace-card')),
        hasTicketsWorkspace: Boolean(document.querySelector('.admin-tickets-workspace-card')),
        hasOrdersWorkspace: Boolean(document.querySelector('.admin-orders-workspace-card')),
        hasAuditWorkspace: Boolean(document.querySelector('.admin-audit-workspace-card')),
      }))()`,
    )
    await fillPlaceholder(client, '每行一个核验码', 'TK2606280007A\nTK-BATCH-MISSING')
    await waitFor(
      client,
      `(() => [...document.querySelectorAll('.admin-batch-check-in-action')].some((button) =>
        button.textContent.includes('批量核验') && !button.disabled
      ))()`,
      'admin batch check-in action enabled',
    )
    await clickSelector(client, '.admin-batch-check-in-action')
    await waitFor(client, includesText('批量核验完成'), 'admin batch check-in result')
    adminBatchCheckInState = await evaluate(
      client,
      `(() => {
        const text = document.querySelector('.admin-batch-check-in-panel')?.textContent || ''
        return {
          hasPanel: text.includes('批量票码核验'),
          hasBoundary: text.includes('状态变更只提交待核验票码') &&
            text.includes('逐票业务失败不阻断同批其他票码'),
          hasResultSummary: text.includes('共 2 个票码，成功 1 个，失败 1 个。'),
          hasSuccessRow: text.includes('TK2606280007A') &&
            text.includes('YT2606280007') &&
            text.includes('ITEM-260628-007-A'),
          hasFailureRow: text.includes('TK-BATCH-MISSING') &&
            text.includes('TICKET_NOT_FOUND'),
          hasNoInternalAdminId: !text.includes('adminUserId'),
          hasNoOrderInternalId: !text.includes('orderId'),
          hasNoFullPhone: !text.includes('13411118888'),
          hasNoSessionText: !text.includes('session'),
          hasNoCsrfText: !text.includes('CSRF') && !text.includes('csrf'),
          hasNoPasswordText: !text.includes('password'),
          hasNoHashText: !text.includes('hash'),
          hasNoSqlText: !text.includes('SQL'),
        }
      })()`,
    )
    await fillPlaceholder(client, '每行一个撤销核验码', 'TK2606280007A\nTK-UNDO-MISSING')
    await fillPlaceholder(client, '可选撤销原因', '现场误核销')
    await waitFor(
      client,
      `(() => [...document.querySelectorAll('.admin-batch-undo-check-in-action')].some((button) =>
        button.textContent.includes('批量撤销') && !button.disabled
      ))()`,
      'admin batch undo check-in action enabled',
    )
    await clickSelector(client, '.admin-batch-undo-check-in-action')
    await waitFor(client, includesText('批量撤销核验完成'), 'admin batch undo check-in result')
    adminBatchUndoCheckInState = await evaluate(
      client,
      `(() => {
        const text = document.querySelector('.admin-batch-undo-check-in-panel')?.textContent || ''
        return {
          hasPanel: text.includes('批量撤销核验'),
          hasBoundary: text.includes('状态变更只提交待撤销票码和可选原因') &&
            text.includes('逐票业务失败不阻断同批其他票码'),
          hasResultSummary: text.includes('共 2 个票码，成功 1 个，失败 1 个。'),
          hasReasonInput: Boolean(document.querySelector('.admin-batch-undo-check-in-reason-input')),
          hasReasonEcho: text.includes('本次原因：现场误核销'),
          hasSuccessRow: text.includes('TK2606280007A') &&
            text.includes('YT2606280007') &&
            text.includes('ITEM-260628-007-A'),
          hasFailureRow: text.includes('TK-UNDO-MISSING') &&
            text.includes('TICKET_NOT_FOUND'),
          hasNoInternalAdminId: !text.includes('adminUserId'),
          hasNoOrderInternalId: !text.includes('orderId'),
          hasNoFullPhone: !text.includes('13411118888'),
          hasNoSessionText: !text.includes('session'),
          hasNoCsrfText: !text.includes('CSRF') && !text.includes('csrf'),
          hasNoPasswordText: !text.includes('password'),
          hasNoHashText: !text.includes('hash'),
          hasNoSqlText: !text.includes('SQL'),
        }
      })()`,
    )
    await openAdminSidePage(client, '审计')
    await waitFor(client, `document.querySelector('.page-heading h1')?.textContent.includes('审计导出')`, 'admin audit page after batch actions')
    await waitFor(client, includesText('退款审计检索'), 'admin refund audit search panel')
    await waitFor(client, includesText('核验审计导出'), 'admin check-in audit export panel')
    await evaluate(
      client,
      `(() => {
        const originalCreateObjectUrl = URL.createObjectURL.bind(URL)
        const originalAnchorClick = HTMLAnchorElement.prototype.click
        window.__checkInAuditDownloads = []
        URL.createObjectURL = (blob) => {
          window.__checkInAuditDownloads.push({
            blobSize: blob.size,
            blobType: blob.type,
          })
          return originalCreateObjectUrl(blob)
        }
        HTMLAnchorElement.prototype.click = function () {
          window.__checkInAuditDownloads.push({
            download: this.download,
            href: this.href,
          })
        }
        window.__restoreCheckInAuditDownloads = () => {
          URL.createObjectURL = originalCreateObjectUrl
          HTMLAnchorElement.prototype.click = originalAnchorClick
        }
        return true
      })()`,
    )
    await fillPlaceholderIn(client, '.admin-check-in-log-export-panel', '票码', 'TK2606280001A')
    await fillPlaceholderIn(client, '.admin-check-in-log-export-panel', '起始日期 YYYY-MM-DD', '2026-06-28')
    await fillPlaceholderIn(client, '.admin-check-in-log-export-panel', '截至日期 YYYY-MM-DD', '2026-06-28')
    await clickSelector(client, '.admin-check-in-log-csv-export-action')
    await waitFor(
      client,
      `window.__checkInAuditDownloads?.some((entry) => entry.download === 'admin-check-in-logs-20260628-20260628.csv')`,
      'admin check-in audit CSV mock download',
    )
    await clickSelector(client, '.admin-check-in-log-xlsx-export-action')
    await waitFor(
      client,
      `window.__checkInAuditDownloads?.some((entry) => entry.download === 'admin-check-in-logs-20260628-20260628.xlsx')`,
      'admin check-in audit XLSX mock download',
    )
    adminCheckInAuditExportState = await evaluate(
      client,
      `(() => ({
        hasCsvBlobType: window.__checkInAuditDownloads?.some((entry) =>
          entry.blobType === 'text/csv;charset=utf-8' &&
          entry.blobSize > 0
        ),
        hasCsvFileName: window.__checkInAuditDownloads?.some((entry) =>
          entry.download === 'admin-check-in-logs-20260628-20260628.csv'
        ),
        hasXlsxBlobType: window.__checkInAuditDownloads?.some((entry) =>
          entry.blobType === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' &&
          entry.blobSize > 0
        ),
        hasXlsxFileName: window.__checkInAuditDownloads?.some((entry) =>
          entry.download === 'admin-check-in-logs-20260628-20260628.xlsx'
        ),
      }))()`,
    )
    await evaluate(client, 'window.__restoreCheckInAuditDownloads?.()')
    await waitFor(client, includesText('核验失败审计'), 'admin check-in failure audit search panel')
    await waitFor(client, includesText('mock-check-in-failure-260701-001'), 'admin check-in failure audit initial missing ticket row')
    adminCheckInFailureLogSearchState = await evaluate(
      client,
      `(() => {
        const panel = document.querySelector('.admin-check-in-failure-log-panel')
        const text = panel?.textContent || ''
        return {
          hasPanel: text.includes('核验失败审计'),
          hasReadOnlyBoundary: text.includes('只读检索'),
          hasMissingTicketFailure: text.includes('票码不存在') &&
            text.includes('TK-MISSING-260701') &&
            text.includes('mock-check-in-failure-260701-001'),
          hasAlreadyUsedFailure: text.includes('票码已核销') &&
            text.includes('mock-check-in-failure-260701-002'),
          hasUndoFailure: text.includes('票码未核销') &&
            text.includes('mock-check-in-failure-260701-004'),
          hasOperatorDisplay: text.includes('运营管理员') &&
            text.includes('@admin'),
          hasNoInternalAdminId: !text.includes('adminUserId'),
          hasNoOrderInternalId: !text.includes('orderId'),
          hasNoFullPhone: !text.includes('13911112222') && !text.includes('13711115555'),
          hasNoIdNumber: !text.includes('idNumber') && !text.includes('11010519491231002X'),
          hasNoSessionText: !text.includes('session'),
          hasNoCsrfText: !text.includes('CSRF') && !text.includes('csrf'),
          hasNoPasswordText: !text.includes('password'),
          hasNoHashText: !text.includes('hash'),
          hasNoSqlText: !text.includes('SQL'),
        }
      })()`,
    )
    await fillPlaceholder(client, '失败日期从', '2026-07-02')
    await fillPlaceholder(client, '失败日期至', '2026-07-01')
    await waitFor(
      client,
      `document.querySelector('.admin-check-in-failure-log-panel')?.textContent.includes('ADMIN_CHECK_IN_FAILURE_LOG_DATE_RANGE_INVALID')`,
      'admin check-in failure audit invalid date range error',
    )
    adminCheckInFailureLogSearchState = {
      ...adminCheckInFailureLogSearchState,
      ...(await evaluate(
        client,
        `(() => ({
          hasInvalidDateRangeError: document.querySelector('.admin-check-in-failure-log-panel')?.textContent.includes('ADMIN_CHECK_IN_FAILURE_LOG_DATE_RANGE_INVALID'),
        }))()`,
      )),
    }
    await clickSelector(client, '.admin-check-in-failure-log-reset-action')
    await waitFor(client, includesText('mock-check-in-failure-260701-001'), 'admin check-in failure audit reset invalid date range')
    await selectAntOption(client, '.admin-check-in-failure-log-control', '.admin-check-in-failure-log-popup', '票码不存在')
    await fillPlaceholder(client, '失败票码', 'MISSING')
    await fillPlaceholder(client, '失败操作人用户名', 'admin')
    await fillPlaceholder(client, '失败日期从', '2026-07-01')
    await fillPlaceholder(client, '失败日期至', '2026-07-01')
    await waitFor(
      client,
      `(() => {
        const text = document.querySelector('.admin-check-in-failure-log-panel')?.textContent || ''
        return text.includes('mock-check-in-failure-260701-001') && !text.includes('mock-check-in-failure-260701-002')
      })()`,
      'admin check-in failure audit filtered row',
    )
    await evaluate(
      client,
      `(() => {
        const originalCreateObjectUrl = URL.createObjectURL.bind(URL)
        const originalAnchorClick = HTMLAnchorElement.prototype.click
        window.__checkInFailureAuditDownloads = []
        URL.createObjectURL = (blob) => {
          window.__checkInFailureAuditDownloads.push({
            blobSize: blob.size,
            blobType: blob.type,
          })
          return originalCreateObjectUrl(blob)
        }
        HTMLAnchorElement.prototype.click = function () {
          window.__checkInFailureAuditDownloads.push({
            download: this.download,
            href: this.href,
          })
        }
        window.__restoreCheckInFailureAuditDownloads = () => {
          URL.createObjectURL = originalCreateObjectUrl
          HTMLAnchorElement.prototype.click = originalAnchorClick
        }
        return true
      })()`,
    )
    await clickSelector(client, '.admin-check-in-failure-log-csv-export-action')
    await waitFor(
      client,
      `window.__checkInFailureAuditDownloads?.some((entry) => entry.download === 'admin-check-in-failure-logs-20260701-20260701.csv')`,
      'admin check-in failure audit CSV mock download',
    )
    await clickSelector(client, '.admin-check-in-failure-log-xlsx-export-action')
    await waitFor(
      client,
      `window.__checkInFailureAuditDownloads?.some((entry) => entry.download === 'admin-check-in-failure-logs-20260701-20260701.xlsx')`,
      'admin check-in failure audit XLSX mock download',
    )
    adminCheckInFailureAuditExportState = await evaluate(
      client,
      `(() => ({
        hasCsvBlobType: window.__checkInFailureAuditDownloads?.some((entry) =>
          entry.blobType === 'text/csv;charset=utf-8' &&
          entry.blobSize > 0
        ),
        hasCsvFileName: window.__checkInFailureAuditDownloads?.some((entry) =>
          entry.download === 'admin-check-in-failure-logs-20260701-20260701.csv'
        ),
        hasXlsxBlobType: window.__checkInFailureAuditDownloads?.some((entry) =>
          entry.blobType === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' &&
          entry.blobSize > 0
        ),
        hasXlsxFileName: window.__checkInFailureAuditDownloads?.some((entry) =>
          entry.download === 'admin-check-in-failure-logs-20260701-20260701.xlsx'
        ),
      }))()`,
    )
    await evaluate(client, 'window.__restoreCheckInFailureAuditDownloads?.()')
    adminCheckInFailureLogSearchState = {
      ...adminCheckInFailureLogSearchState,
      ...(await evaluate(
        client,
        `(() => {
          const text = document.querySelector('.admin-check-in-failure-log-panel')?.textContent || ''
          return {
            filterKeepsMissingTicketLog: text.includes('mock-check-in-failure-260701-001') &&
              text.includes('运营管理员') &&
              text.includes('@admin'),
            filterHidesAlreadyUsedLog: !text.includes('mock-check-in-failure-260701-002') &&
              !text.includes('票码已核销'),
          }
        })()`,
      )),
    }
    await clickSelector(client, '.admin-check-in-failure-log-reset-action')
    await waitFor(client, includesText('mock-check-in-failure-260701-002'), 'admin check-in failure audit clear filters')
    await waitFor(client, includesText('暴雨停航'), 'admin refund audit search initial full row')
    await evaluate(
      client,
      `(() => {
        const originalCreateObjectUrl = URL.createObjectURL.bind(URL)
        const originalAnchorClick = HTMLAnchorElement.prototype.click
        window.__refundAuditDownloads = []
        URL.createObjectURL = (blob) => {
          window.__refundAuditDownloads.push({
            blobSize: blob.size,
            blobType: blob.type,
          })
          return originalCreateObjectUrl(blob)
        }
        HTMLAnchorElement.prototype.click = function () {
          window.__refundAuditDownloads.push({
            download: this.download,
            href: this.href,
          })
        }
        window.__restoreRefundAuditDownloads = () => {
          URL.createObjectURL = originalCreateObjectUrl
          HTMLAnchorElement.prototype.click = originalAnchorClick
        }
        return true
      })()`,
    )
    await clickSelector(client, '.admin-refund-log-csv-export-action')
    await waitFor(
      client,
      `window.__refundAuditDownloads?.some((entry) => entry.download === 'admin-refund-logs-start-end.csv')`,
      'admin refund audit CSV mock download',
    )
    await clickSelector(client, '.admin-refund-log-xlsx-export-action')
    await waitFor(
      client,
      `window.__refundAuditDownloads?.some((entry) => entry.download === 'admin-refund-logs-start-end.xlsx')`,
      'admin refund audit XLSX mock download',
    )
    adminRefundAuditExportState = await evaluate(
      client,
      `(() => ({
        hasCsvBlobType: window.__refundAuditDownloads?.some((entry) =>
          entry.blobType === 'text/csv;charset=utf-8' &&
          entry.blobSize > 0
        ),
        hasCsvFileName: window.__refundAuditDownloads?.some((entry) =>
          entry.download === 'admin-refund-logs-start-end.csv'
        ),
        hasXlsxBlobType: window.__refundAuditDownloads?.some((entry) =>
          entry.blobType === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' &&
          entry.blobSize > 0
        ),
        hasXlsxFileName: window.__refundAuditDownloads?.some((entry) =>
          entry.download === 'admin-refund-logs-start-end.xlsx'
        ),
      }))()`,
    )
    await evaluate(client, 'window.__restoreRefundAuditDownloads?.()')
    adminRefundLogSearchState = await evaluate(
      client,
      `(() => {
        const panel = document.querySelector('.admin-refund-log-panel')
        const text = panel?.textContent || ''
        return {
          hasPanel: text.includes('退款审计检索'),
          hasReadOnlyBoundary: text.includes('跨订单只读检索'),
          hasFullRefundLog: text.includes('整单退款') &&
            text.includes('¥ 256.00') &&
            text.includes('mock-refund-request-260628-004'),
          hasPartialRefundLog: text.includes('部分退款') &&
            text.includes('儿童票临时取消'),
          hasOperatorDisplay: text.includes('运营李娜') &&
            text.includes('@ops_lina'),
          hasNoInternalAdminId: !text.includes('adminUserId'),
          hasNoFullPhone: !text.includes('13911112222') && !text.includes('13711115555'),
          hasNoIdNumber: !text.includes('idNumber') && !text.includes('11010519491231002X'),
          hasNoSessionText: !text.includes('session'),
          hasNoCsrfText: !text.includes('CSRF') && !text.includes('csrf'),
          hasNoPasswordText: !text.includes('password'),
          hasNoHashText: !text.includes('hash'),
          hasNoSqlText: !text.includes('SQL'),
        }
      })()`,
    )
    await fillPlaceholder(client, '开始日期', '2026-06-29')
    await fillPlaceholder(client, '结束日期', '2026-06-28')
    await waitFor(
      client,
      `document.querySelector('.admin-refund-log-panel')?.textContent.includes('ADMIN_REFUND_LOG_DATE_RANGE_INVALID')`,
      'admin refund audit search invalid date range error',
    )
    adminRefundLogSearchState = {
      ...adminRefundLogSearchState,
      ...(await evaluate(
        client,
        `(() => ({
          hasInvalidDateRangeError: document.querySelector('.admin-refund-log-panel')?.textContent.includes('ADMIN_REFUND_LOG_DATE_RANGE_INVALID'),
        }))()`,
      )),
    }
    await clickSelector(client, '.admin-refund-log-reset-action')
    await waitFor(client, includesText('mock-refund-request-260628-004'), 'admin refund audit search reset invalid date range')
    await fillPlaceholder(client, '搜索审计订单号', 'YT2606280003')
    await waitFor(
      client,
      `document.querySelector('.admin-refund-log-panel')?.textContent.includes('儿童票临时取消')`,
      'admin refund audit search order filter result',
    )
    await selectAntOption(client, '.admin-refund-log-type-select', '.admin-refund-log-type-popup', '部分退款')
    await fillPlaceholder(client, '操作人用户名', 'admin')
    await fillPlaceholder(client, '开始日期', '2026-06-28')
    await fillPlaceholder(client, '结束日期', '2026-06-28')
    await waitFor(
      client,
      `(() => {
        const text = document.querySelector('.admin-refund-log-panel')?.textContent || ''
        return text.includes('mock-refund-request-260628-003') && !text.includes('mock-refund-request-260628-004')
      })()`,
      'admin refund audit search filtered row',
    )
    adminRefundLogSearchState = {
      ...adminRefundLogSearchState,
      ...(await evaluate(
        client,
        `(() => {
          const text = document.querySelector('.admin-refund-log-panel')?.textContent || ''
          return {
            filterKeepsPartialLog: text.includes('mock-refund-request-260628-003') &&
              text.includes('运营管理员') &&
              text.includes('@admin'),
            filterHidesFullLog: !text.includes('mock-refund-request-260628-004') &&
              !text.includes('暴雨停航'),
          }
        })()`,
      )),
    }
    await clickSelector(client, '.admin-refund-log-reset-action')
    await waitFor(client, includesText('mock-refund-request-260628-004'), 'admin refund audit search clear filters')
    await openAdminSidePage(client, '订单')
    await waitFor(client, includesText('订单运营列表'), 'admin orders page before partial refund')
    await fillPlaceholder(client, '搜索订单号', 'YT2606280006')
    await waitFor(
      client,
      `document.querySelector('.admin-orders-table')?.textContent.includes('YT2606280006')`,
      'admin partial refund order filter result',
    )
    await clickTableRowContaining(client, '.admin-orders-table', 'YT2606280006')
    await waitFor(client, includesText('部分退款'), 'admin partial refund action panel')
    adminPartialRefundState = await evaluate(
      client,
      `(() => {
        const drawerText = document.querySelector('.admin-order-detail-drawer')?.textContent || ''
        return {
          disablesBeforeSelection: [...document.querySelectorAll('.admin-partial-refund-action')].some((button) =>
            button.textContent.includes('部分退款') && button.disabled
          ),
          hasBoundary: drawerText.includes('只提交选中的票项和退款原因') &&
            drawerText.includes('金额、状态和库存由后端计算'),
          hasItemSelector: drawerText.includes('ITEM-260628-006-A') &&
            drawerText.includes('ITEM-260628-006-B'),
          hasNoInternalAdminId: !drawerText.includes('adminUserId'),
          hasNoFullPhone: !drawerText.includes('13511117777'),
          hasNoSqlText: !drawerText.includes('SQL'),
        }
      })()`,
    )
    const selectedPartialRefundItem = await evaluate(
      client,
      `(() => {
        ${visibleElementScript}
        const label = [...document.querySelectorAll('.admin-partial-refund-item')].find((element) =>
          isVisible(element) && element.textContent.includes('ITEM-260628-006-A')
        )
        if (!label) return false
        label.click()
        return true
      })()`,
    )
    assert(selectedPartialRefundItem, 'admin partial refund item checkbox should be selectable')
    await waitFor(
      client,
      `(() => {
        ${visibleElementScript}
        return [...document.querySelectorAll('.admin-partial-refund-action')].some((button) =>
          isVisible(button) && button.textContent.includes('部分退款') && !button.disabled
        )
      })()`,
      'admin partial refund action enabled after item selection',
    )
    await fillPlaceholder(client, '部分退款原因，选填，最多 100 字', '只退成人票')
    await clickSelector(client, '.admin-partial-refund-action')
    await waitFor(client, includesText('确认对选中票项执行部分退款？'), 'admin partial refund confirmation')
    await clickByText(client, '确认部分退款')
    await waitFor(client, includesText('部分退款成功'), 'admin partial refund success')
    await waitFor(client, includesText('mock-partial-refund-request-260628-006'), 'admin partial refund audit log')
    adminPartialRefundState = {
      ...adminPartialRefundState,
      ...(await evaluate(
        client,
        `(() => {
          const drawerText = document.querySelector('.admin-order-detail-drawer')?.textContent || ''
          return {
            hasSuccess: drawerText.includes('部分退款成功') &&
              drawerText.includes('订单 YT2606280006 已部分退款 ¥ 128.00，票项 1 张。'),
            hasPartialStatus: drawerText.includes('部分退款') &&
              drawerText.includes('¥ 68.00'),
            hasAuditLog: drawerText.includes('部分') &&
              drawerText.includes('只退成人票') &&
              drawerText.includes('mock-partial-refund-request-260628-006'),
            keepsRemainingRefundable: [...document.querySelectorAll('.admin-partial-refund-action')].some((button) =>
              button.textContent.includes('部分退款') && button.disabled
            ),
            refundedItemDisabled: [...document.querySelectorAll('.admin-partial-refund-item')].some((element) =>
              element.textContent.includes('ITEM-260628-006-A') &&
              Boolean(element.querySelector('input')?.disabled)
            ),
          }
        })()`,
      )),
    }
    await clickSelector(client, '.admin-order-detail-drawer .ant-drawer-close')
    await openAdminSidePage(client, '审计')
    await waitFor(
      client,
      `document.querySelector('.admin-refund-log-panel')?.textContent.includes('mock-partial-refund-request-260628-006')`,
      'admin partial refund global audit log',
    )
    adminPartialRefundState = {
      ...adminPartialRefundState,
      ...(await evaluate(
        client,
        `(() => {
          const globalAuditText = document.querySelector('.admin-refund-log-panel')?.textContent || ''
          return {
            globalAuditUpdated: globalAuditText.includes('mock-partial-refund-request-260628-006') &&
              globalAuditText.includes('只退成人票'),
          }
        })()`,
      )),
    }
    await openAdminSidePage(client, '订单')
    await waitFor(client, includesText('订单运营列表'), 'admin orders page after partial refund audit check')
    await fillPlaceholder(client, '搜索订单号', 'YT2606280005')
    await waitFor(
      client,
      `document.querySelector('.admin-orders-table')?.textContent.includes('YT2606280005')`,
      'admin full refund order filter result',
    )
    await clickTableRowContaining(client, '.admin-orders-table', 'YT2606280005')
    await waitFor(client, includesText('整单退款'), 'admin full refund action panel')
    await fillPlaceholder(client, '退款原因，选填，最多 100 字', '游客行程取消')
    adminFullRefundState = await evaluate(
      client,
      `(() => {
        const drawerText = document.querySelector('.admin-order-detail-drawer')?.textContent || ''
        return {
          canSubmit: [...document.querySelectorAll('.admin-full-refund-action')].some((button) =>
            button.textContent.includes('整单退款') && !button.disabled
          ),
          hasBoundary: drawerText.includes('只提交退款原因') &&
            drawerText.includes('退款金额、票项和库存回补由后端计算'),
          hasReasonInput: Boolean(document.querySelector('.admin-refund-reason-input')),
          hasNoInternalAdminId: !drawerText.includes('adminUserId'),
          hasNoFullPhone: !drawerText.includes('13611116666'),
          hasNoSqlText: !drawerText.includes('SQL'),
        }
      })()`,
    )
    await clickSelector(client, '.admin-full-refund-action')
    await waitFor(client, includesText('确认对这笔订单执行整单退款？'), 'admin full refund confirmation')
    await clickByText(client, '确认退款')
    await waitFor(client, includesText('整单退款成功'), 'admin full refund success')
    await waitFor(client, includesText('mock-refund-request-260628-005'), 'admin full refund audit log')
    adminFullRefundState = {
      ...adminFullRefundState,
      ...(await evaluate(
        client,
        `(() => {
          const drawerText = document.querySelector('.admin-order-detail-drawer')?.textContent || ''
          return {
            hasSuccess: drawerText.includes('整单退款成功') &&
              drawerText.includes('订单 YT2606280005 已退款 ¥ 128.00，票项 1 张。'),
            hasRefundedStatus: drawerText.includes('已退款') &&
              drawerText.includes('¥ 0.00'),
            hasAuditLog: drawerText.includes('整单') &&
              drawerText.includes('游客行程取消') &&
              drawerText.includes('mock-refund-request-260628-005'),
            disablesAfterRefund: [...document.querySelectorAll('.admin-full-refund-action')].some((button) =>
              button.textContent.includes('整单退款') && button.disabled
            ) && drawerText.includes('退款不可用'),
          }
        })()`,
      )),
    }
    await clickSelector(client, '.admin-order-detail-drawer .ant-drawer-close')
    await openAdminSidePage(client, '审计')
    await waitFor(
      client,
      `document.querySelector('.admin-refund-log-panel')?.textContent.includes('mock-refund-request-260628-005')`,
      'admin full refund global audit log',
    )
    adminFullRefundState = {
      ...adminFullRefundState,
      ...(await evaluate(
        client,
        `(() => {
          const globalAuditText = document.querySelector('.admin-refund-log-panel')?.textContent || ''
          return {
            globalAuditUpdated: globalAuditText.includes('mock-refund-request-260628-005') &&
              globalAuditText.includes('游客行程取消'),
          }
        })()`,
      )),
    }
    await openAdminSidePage(client, '订单')
    await waitFor(client, includesText('订单运营列表'), 'admin orders page after full refund audit check')
    await selectAntOption(client, '.admin-order-status-select', '.admin-order-status-popup', '待支付')
    await waitFor(client, includesText('YT2606280002'), 'admin order status filter result')
    adminFilterState = await evaluate(
      client,
      `(() => ({
        createdOrderVisible: document.body.textContent.includes('YT2606280002'),
        hidesPaidOrderByStatus: !document.body.textContent.includes('YT2606280001'),
      }))()`,
    )
    await clickByText(client, '清空')
    await fillPlaceholder(client, '搜索订单号', 'YT2606280003')
    await waitFor(
      client,
      `document.querySelector('.admin-orders-table')?.textContent.includes('YT2606280003')`,
      'admin order number filter result',
    )
    adminFilterState = {
      ...adminFilterState,
      ...(await evaluate(
        client,
        `(() => ({
          hidesOtherOrderByOrderNo: !document.querySelector('.admin-orders-table')?.textContent.includes('YT2606280001'),
          orderNoFilterVisible: document.querySelector('.admin-orders-table')?.textContent.includes('YT2606280003'),
        }))()`,
      )),
    }
    await clickByText(client, '清空')
    await selectAntOption(client, '.admin-order-payment-select', '.admin-order-payment-popup', '部分退款')
    await waitFor(
      client,
      `document.querySelector('.admin-orders-table')?.textContent.includes('YT2606280003')`,
      'admin payment status filter result',
    )
    adminFilterState = {
      ...adminFilterState,
      ...(await evaluate(
        client,
        `(() => ({
          hidesPaidOrder: !document.querySelector('.admin-orders-table')?.textContent.includes('YT2606280001'),
          partialRefundOrderVisible: document.querySelector('.admin-orders-table')?.textContent.includes('YT2606280003'),
        }))()`,
      )),
    }
    await clickTableRowContaining(client, '.admin-orders-table', 'YT2606280003')
    await waitFor(client, includesText('退款审计日志'), 'admin refund audit log panel')
    await waitFor(client, includesText('儿童票临时取消'), 'admin refund audit log reason')
    adminRefundAuditState = await evaluate(
      client,
      `(() => {
        const drawerText = document.querySelector('.admin-order-detail-drawer')?.textContent || ''
        return {
          hasPartialLog: drawerText.includes('部分') &&
            drawerText.includes('¥ 68.00'),
          hasReason: drawerText.includes('儿童票临时取消'),
          hasRequestId: drawerText.includes('mock-refund-request-260628-003'),
          hasOperatorDisplay: drawerText.includes('运营管理员 @admin'),
          hasReadOnlyBoundary: drawerText.includes('只读查看，不提交操作人、金额或状态。'),
          hasNoInternalAdminId: !drawerText.includes('adminUserId'),
          hasNoFullPhone: !drawerText.includes('13711115555'),
          hasNoSqlText: !drawerText.includes('SQL'),
        }
      })()`,
    )
    await clickSelector(client, '.admin-order-detail-drawer .ant-drawer-close')
    await clickByText(client, '清空')
    await fillPlaceholder(client, '手机号后四位', '139****2222')
    await waitFor(client, includesText('YT2606280001'), 'admin buyer phone suffix filter result')
    adminFilterState = {
      ...adminFilterState,
      ...(await evaluate(
        client,
        `(() => ({
          hidesOtherMaskedPhone: !document.body.textContent.includes('138****9999'),
          phoneFilterOrderVisible: document.body.textContent.includes('YT2606280001'),
        }))()`,
      )),
    }
    await clickTableRowContaining(client, '.admin-orders-table', 'YT2606280001')
    await waitFor(client, includesText('订单详情'), 'admin order detail drawer')
    await waitFor(client, includesText('TK2606280001A'), 'admin order detail ticket code')
    adminDetailState = await evaluate(
      client,
      `(() => ({
        hasDetailSummaryCard: Boolean(document.querySelector('.admin-order-state-card')) &&
          document.querySelector('.admin-order-state-card')?.textContent.includes('可核验'),
        hasCheckInAction: [...document.querySelectorAll('.admin-check-in-action')].some((button) =>
          button.textContent.includes('核验') && !button.disabled
        ),
        hasFullRefundAction: [...document.querySelectorAll('.admin-full-refund-action')].some((button) =>
          button.textContent.includes('整单退款') && !button.disabled
        ),
        hasMaskedPhone: document.body.textContent.includes('139****2222'),
        hasNoFullPhone: !document.body.textContent.includes('13911112222'),
        hasReadOnlyBoundary: document.body.textContent.includes('只读安全边界'),
        hasRefundBoundary: document.body.textContent.includes('只提交退款原因') &&
          document.body.textContent.includes('退款金额、票项和库存回补由后端计算'),
        hasRefundStatePath: [...document.querySelectorAll('.admin-refund-state-path')].some((element) =>
          element.textContent.includes('已支付订单') && element.textContent.includes('符合退款规则')
        ),
        hasRefundAuditEmptyState: document.body.textContent.includes('暂无退款审计记录'),
        hasNoEnglishTicketName: !document.body.textContent.includes('Adult Ticket'),
        hasTicketCode: document.body.textContent.includes('TK2606280001A'),
      }))()`,
    )
    await clickSelector(client, '.admin-order-detail-drawer .admin-check-in-action')
    await waitFor(client, includesText('确认核验'), 'admin check-in confirmation')
    await clickByText(client, '确认核验')
    await waitFor(client, includesText('票码核验成功'), 'admin check-in success alert')
    adminDetailState = {
      ...adminDetailState,
      ...(await evaluate(
        client,
        `(() => ({
          hasCheckInSuccess: document.body.textContent.includes('票码核验成功') &&
            document.body.textContent.includes('ITEM-260628-001-A'),
          hasUsedTicketState: (() => {
            const itemRow = [...document.querySelectorAll('.admin-order-items-table .ant-table-row')]
              .find((row) => row.textContent.includes('ITEM-260628-001-A'))
            return Boolean(itemRow?.textContent.includes('已核验'))
          })(),
          disablesCheckedInAction: (() => {
            const itemRow = [...document.querySelectorAll('.admin-order-items-table .ant-table-row')]
              .find((row) => row.textContent.includes('ITEM-260628-001-A'))
            const button = itemRow?.querySelector('.admin-check-in-action')
            return Boolean(button?.textContent.includes('核验') && button.disabled)
          })(),
          disablesRefundAfterCheckIn: [...document.querySelectorAll('.admin-full-refund-action')].some((button) =>
            button.textContent.includes('整单退款') && button.disabled
          ) && document.body.textContent.includes('退款不可用'),
        }))()`,
      )),
    }
    await clickSelector(client, '.admin-order-detail-drawer .ant-drawer-close')
    await client.send('Emulation.setDeviceMetricsOverride', {
      deviceScaleFactor: 1,
      height: 1112,
      mobile: false,
      width: 834,
    })
    await waitFor(client, `window.matchMedia('(max-width: 960px)').matches`, 'admin intermediate viewport')
    adminIntermediateState = await evaluate(
      client,
      `(() => {
        const contentRoots = [document.body, document.querySelector('#root'), document.querySelector('.app-shell')]
          .filter(Boolean)
        const clientWidth = document.documentElement.clientWidth
        const scrollWidth = Math.max(...contentRoots.map((element) => element.scrollWidth))
        return {
          clientWidth,
          hasAccessCard: Boolean(document.querySelector('.admin-access-card')),
          hasAuthenticatedWorkbench: Boolean(document.querySelector('.admin-workbench-grid.is-authenticated')),
          scrollWidth,
        }
      })()`,
    )
    await client.send('Emulation.setDeviceMetricsOverride', {
      deviceScaleFactor: 1,
      height: 1024,
      mobile: false,
      width: 768,
    })
    await waitFor(
      client,
      `(() => {
        const table = document.querySelector('.admin-orders-table')
        return window.matchMedia('(max-width: 768px)').matches &&
          table &&
          getComputedStyle(table).display === 'none'
      })()`,
      'admin tablet orders card layout',
    )
    adminTabletState = await evaluate(
      client,
      `(() => {
        const contentRoots = [document.body, document.querySelector('#root'), document.querySelector('.app-shell')]
          .filter(Boolean)
        const clientWidth = document.documentElement.clientWidth
        const scrollWidth = Math.max(...contentRoots.map((element) => element.scrollWidth))
        return {
          clientWidth,
          hasAccessCard: Boolean(document.querySelector('.admin-access-card')),
          hasAuthenticatedWorkbench: Boolean(document.querySelector('.admin-workbench-grid.is-authenticated')),
          hasExportJobsPanel: Boolean(document.querySelector('.admin-export-jobs-panel')),
          hasMobileOrderCards: getComputedStyle(document.querySelector('.admin-orders-mobile-list')).display !== 'none',
          hasOperationCards: document.querySelectorAll('.admin-operation-card').length >= 3,
          hasOperationsWorkflowStrip: Boolean(document.querySelector('.admin-operations-workflow-strip')),
          operationsWorkflowItemCount: document.querySelectorAll('.admin-operations-workflow-item').length,
          hasOperationsBoundaryStrip: Boolean(document.querySelector('.admin-operations-boundary-strip')),
          scrollWidth,
        }
      })()`,
    )
    await client.send('Emulation.setDeviceMetricsOverride', {
      deviceScaleFactor: 1,
      height: viewport.height,
      mobile: true,
      width: viewport.width,
    })
    await waitFor(
      client,
      `(() => {
        const table = document.querySelector('.admin-orders-table')
        return window.matchMedia('(max-width: 768px)').matches &&
          table &&
          getComputedStyle(table).display === 'none'
      })()`,
      'admin mobile orders layout',
    )
    const adminMobileState = await evaluate(
      client,
      `(() => {
        const contentRoots = [document.body, document.querySelector('#root'), document.querySelector('.app-shell')]
          .filter(Boolean)
        const clientWidth = document.documentElement.clientWidth
        const scrollWidth = Math.max(...contentRoots.map((element) => element.scrollWidth))
        return {
          clientWidth,
          hasExportJobsPanel: Boolean(document.querySelector('.admin-export-jobs-panel')),
          hasMobileOrderCards: getComputedStyle(document.querySelector('.admin-orders-mobile-list')).display !== 'none',
          hasMobileTabbar: getComputedStyle(document.querySelector('.admin-mobile-tabbar')).display === 'grid',
          mobileTabbarLabels: [...document.querySelectorAll('.admin-mobile-tabbar button')].map((button) => button.textContent.trim()),
          hasOperationCards: document.querySelectorAll('.admin-operation-card').length >= 3,
          hasOperationsWorkflowStrip: Boolean(document.querySelector('.admin-operations-workflow-strip')),
          operationsWorkflowItemCount: document.querySelectorAll('.admin-operations-workflow-item').length,
          hasOperationsBoundaryStrip: Boolean(document.querySelector('.admin-operations-boundary-strip')),
          hasWorkbenchGrid: Boolean(document.querySelector('.admin-workbench-grid')),
          scrollWidth,
          wideElements: scrollWidth === clientWidth
          ? []
          : [...document.querySelectorAll('body *')]
            .filter((element) => element.scrollWidth > clientWidth)
            .slice(0, 24)
            .map((element) => ({
              className: element.className || '',
              scrollWidth: element.scrollWidth,
              tagName: element.tagName,
              text: element.textContent.trim().slice(0, 80),
            })),
        }
      })()`,
    )
    await clickSelector(client, '.admin-mobile-tabbar button:nth-child(4)')
    Object.assign(adminMobileState, await evaluate(
      client,
      `(() => ({
        hashAfterMobileOrderTab: location.hash,
        activeMobileTabLabel: document.querySelector('.admin-mobile-tabbar button.is-active')?.textContent.trim() || '',
        hasOrderAnchor: Boolean(document.querySelector('#admin-orders')),
      }))()`,
    ))
    await client.send('Emulation.setDeviceMetricsOverride', {
      deviceScaleFactor: 1,
      height: 900,
      mobile: false,
      width: 1280,
    })
    await clickByText(client, '返回游客端')
    await waitFor(
      client,
      `location.hash === '#/visitor/booking' &&
        Boolean(document.querySelector('.visitor-shell')) &&
        document.querySelector('.page-heading h1')?.textContent.includes('购买门票')`,
      'admin return to visitor shell',
    )
    adminReturnToVisitorState = await evaluate(
      client,
      `(() => ({
        hasVisitorShell: Boolean(document.querySelector('.visitor-shell')),
        hash: location.hash,
        hidesAdminShell: !Boolean(document.querySelector('.admin-shell')),
        title: document.querySelector('.page-heading h1')?.textContent.trim() ?? '',
      }))()`,
    )
    finishE2eSmoke({
      adminBatchCheckInState,
      adminBatchUndoCheckInState,
      adminCheckInAuditExportState,
      adminCheckInFailureAuditExportState,
      adminCheckInFailureLogSearchState,
      adminDetailState,
      adminExportJobCreateState,
      adminFilterState,
      adminFullRefundState,
      adminIntermediateState,
      adminLoggedOutState,
      adminMobileState,
      adminPageSeparationState,
      adminPartialRefundState,
      adminRefundAuditExportState,
      adminRefundAuditState,
      adminRefundLogSearchState,
      adminReportState,
      adminReportTrendExportState,
      adminReportZeroFillState,
      adminReturnToVisitorState,
      adminShellState,
      adminTabletState,
      adminTicketsState,
      apiBaseUrl,
      bookingStepState,
      catalogFallbackState,
      desktopAuthActionState,
      desktopBookingVisualState,
      desktopDetailState,
      e2ePhone,
      e2eUsername,
      emptyOrdersState,
      emptyTimeSlotsState,
      loggedOutOrdersState,
      mobileBookingVisualState,
      mobileDateStripState,
      mobileDetailActionState,
      mobileTicketCardState,
      mock,
      orderDetailErrorState,
      orderStatusFilterState,
      pageState,
      paidPageState,
      sessionFailureState,
      timeSlotFallbackState,
    })
  })
}

run().catch((error) => {
  console.error(error)
  process.exitCode = 1
})
