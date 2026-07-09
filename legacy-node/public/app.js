const API_BASE = window.location.origin;
const STORAGE_KEY = 'yulong-auth-session';

const state = {
  auth: null,
  currentVisitor: null,
  ticketTypes: [],
  routeProducts: [],
  adminRouteProducts: [],
  piers: [],
  offlineSaleNotices: [],
  adminTimeSlots: [],
  timeSlots: [],
  visitorOrders: [],
  reportItems: [],
  businessDate: '',
};

const elements = {
  loginScreen: document.querySelector('[data-login-screen]'),
  appShell: document.querySelector('[data-app-shell]'),
  visitorLoginForm: document.querySelector('[data-visitor-login-form]'),
  visitorLoginResult: document.querySelector('[data-visitor-login-result]'),
  adminLoginForm: document.querySelector('[data-admin-login-form]'),
  adminLoginResult: document.querySelector('[data-admin-login-result]'),
  loginTitle: document.querySelector('[data-login-title]'),
  loginCopy: document.querySelector('[data-login-copy]'),
  loginHint: document.querySelector('[data-login-hint]'),
  showAdminLogin: document.querySelector('[data-show-admin-login]'),
  showVisitorLogin: document.querySelector('[data-show-visitor-login]'),
  logoutButton: document.querySelector('[data-logout]'),
  accountName: document.querySelector('[data-account-name]'),
  accountDetail: document.querySelector('[data-account-detail]'),
  apiBase: document.querySelector('[data-api-base]'),
  authScope: document.querySelector('[data-auth-scope]'),
  currentBusinessDate: document.querySelector('[data-current-business-date]'),
  dashboardTitle: document.querySelector('[data-dashboard-title]'),
  dashboardCopy: document.querySelector('[data-dashboard-copy]'),
  serviceStatus: document.querySelector('[data-service-status]'),
  dbStatus: document.querySelector('[data-db-status]'),
  currentVisitorSummary: document.querySelector('[data-current-visitor-summary]'),
  productSummary: document.querySelector('[data-product-summary]'),
  slotSummary: document.querySelector('[data-slot-summary]'),
  reportSummary: document.querySelector('[data-report-summary]'),
  visitorSections: document.querySelectorAll('[data-visitor-section]'),
  adminSections: document.querySelectorAll('[data-admin-section]'),
  visitorLinks: document.querySelectorAll('[data-visitor-link]'),
  adminLinks: document.querySelectorAll('[data-admin-link]'),
  visitorForm: document.querySelector('[data-visitor-form]'),
  visitorResult: document.querySelector('[data-visitor-result]'),
  visitorOrders: document.querySelector('[data-visitor-orders]'),
  reloadVisitorOrders: document.querySelector('[data-reload-visitor-orders]'),
  orderForm: document.querySelector('[data-order-form]'),
  orderResult: document.querySelector('[data-order-result]'),
  visitorOrderTag: document.querySelector('[data-visitor-order-tag]'),
  tempLock: document.querySelector('[data-temp-lock]'),
  routeProductForm: document.querySelector('[data-route-product-form]'),
  routeProductResult: document.querySelector('[data-route-product-result]'),
  adminTicketPreview: document.querySelector('[data-admin-ticket-preview]'),
  adminTimeSlotForm: document.querySelector('[data-admin-time-slot-form]'),
  adminTimeSlotResult: document.querySelector('[data-admin-time-slot-result]'),
  adminTimeSlotRouteSelect: document.querySelector('[data-admin-time-slot-route-select]'),
  adminTimeSlotDate: document.querySelector('[data-admin-time-slot-date]'),
  adminTimeSlotList: document.querySelector('[data-admin-time-slot-list]'),
  startPierSelect: document.querySelector('[data-start-pier-select]'),
  endPierSelect: document.querySelector('[data-end-pier-select]'),
  checkinForm: document.querySelector('[data-checkin-form]'),
  checkinResult: document.querySelector('[data-checkin-result]'),
  refundForm: document.querySelector('[data-refund-form]'),
  refundResult: document.querySelector('[data-refund-result]'),
  routeProductLists: document.querySelectorAll('[data-route-product-list]'),
  adminRouteProductList: document.querySelector('[data-admin-route-product-list]'),
  pierList: document.querySelector('[data-pier-list]'),
  ticketTypeList: document.querySelector('[data-ticket-type-list]'),
  offlineNoticeList: document.querySelector('[data-offline-notice-list]'),
  timeSlotList: document.querySelector('[data-time-slot-list]'),
  reportBody: document.querySelector('[data-report-body]'),
  noticeBusinessDate: document.querySelector('[data-notice-business-date]'),
  reportStart: document.querySelector('[data-report-start]'),
  reportEnd: document.querySelector('[data-report-end]'),
  refreshButton: document.querySelector('[data-refresh]'),
  ticketTypeSelects: document.querySelectorAll('[data-ticket-type-select]'),
  timeSlotSelect: document.querySelector('[data-time-slot-select]'),
  visitDateInputs: document.querySelectorAll('[data-visit-date]'),
};

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

function formatMoney(value) {
  return Number(value || 0).toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

function translateMessage(message) {
  const raw = String(message || '').trim();
  const messageMap = {
    'admin logged in': '管理员登录成功',
    'visitor logged in': '游客登录成功',
    'temporary visitor logged in': '临时游客登录成功',
    'visitor registered': '实名注册成功',
    'visitor loaded': '游客信息加载完成',
    'visitor orders loaded': '订单记录加载完成',
    'order created': '订单创建成功',
    'checkin completed': '核销完成',
    'refund applied': '退款处理完成',
    'ticket types retrieved': '票种加载完成',
    'time slots retrieved': '时段加载完成',
    'route products loaded': '线路产品加载完成',
    'piers retrieved': '码头列表加载完成',
    'admin route products retrieved': '后台线路产品加载完成',
    'route product created': '线路产品创建成功',
    'route product disabled': '线路产品已删除并停用',
    'route product restored': '线路产品已恢复启用',
    'admin time slots retrieved': '可售时段加载完成',
    'time slot created': '可售时段创建成功',
    'time slot updated': '可售时段已更新',
    'sales report loaded': '销售日报加载完成',
    'offline sale notices loaded': '窗口状态加载完成',
    'service is running': '服务运行正常',
    'database is running': '数据库连接正常',
    'database is unavailable': '数据库暂时不可用',
    'database ping returned false': '数据库健康检查未通过',
    'username is required': '请填写管理员账号',
    'password is required': '请填写管理员密码',
    'phone is required': '请填写手机号',
    'visitorName is required': '请填写游客姓名',
    'idType is required': '请选择证件类型',
    'idNumber is required': '请填写证件号码',
    'buyerName is required': '请填写购票人姓名',
    'buyerPhone is required': '请填写购票人手机号',
    'orderSource is required': '请选择订单来源',
    'productName is required': '请填写线路名称',
    'ticketName is required': '请填写票种名称',
    'tripType is required': '请选择行程类型',
    'startPierId must be a positive integer': '请选择起点码头',
    'endPierId must be a positive integer': '请选择终点码头',
    'raftCapacity must be a positive integer': '每筏人数必须大于 0',
    'routeProductId must be a positive integer': '线路产品编号不正确',
    'items must be a non-empty array': '请至少选择一张门票',
    'ticketCode is required': '请填写票码',
    'checkinGate is required': '请填写闸机编号',
    'reason is required': '请填写退款原因',
    'originalPrice must be a valid number': '原价必须是有效数字',
    'salePrice must be a valid number': '售价必须是有效数字',
    'sale price must be a valid number': '票价必须是有效数字',
    'sale price must not exceed original price': '售价不能高于原价',
    'start and end pier must be different': '起点码头和终点码头不能相同',
    unauthorized: '请先登录',
    forbidden: '没有权限执行该操作',
    'registered visitor account required': '请先完成实名注册',
    'invalid admin credentials': '管理员账号或密码错误',
    'visitor not found': '未找到该游客',
    'ticket type not found': '未找到该票种',
    'route product not found': '未找到该线路产品',
    'time slot not found': '未找到该可售时段',
    'ticket not found': '未找到该门票',
    'ticket already used': '该门票已核销',
    'ticket cannot be checked in': '该门票当前不能核销',
    'time slot quota is not enough': '该时段余票不足',
    'time slot does not match ticket type': '入园时段与票种不匹配',
    'slotStartTime is required': '请填写开始时间',
    'slotEndTime is required': '请填写结束时间',
    'slotStartTime must be in HH:MM format': '开始时间格式不正确',
    'slotEndTime must be in HH:MM format': '结束时间格式不正确',
    'slot end time must be after start time': '结束时间必须晚于开始时间',
    'quotaTotal must be a non-negative integer': '可售库存必须是大于或等于 0 的整数',
    'quotaTotal must not be less than sold quota': '可售库存不能小于已售数量',
    'status must be ENABLED or DISABLED': '状态只能选择启用或停用',
    'all items must belong to the same scenic spot': '同一订单中的门票必须属于同一景区',
    'failed to create visitor session': '创建游客登录状态失败',
    'failed to create order': '订单创建失败',
    'failed to create ticket type': '基础票种创建失败',
    'failed to create route product': '线路产品创建失败',
    'failed to create order item': '订单明细创建失败',
    'failed to update time slot quota': '更新时段余票失败',
    'failed to save time slot': '保存可售时段失败',
    'failed to create checkin record': '核销记录创建失败',
    'failed to update ticket item': '更新门票状态失败',
    'startDate must be less than or equal to endDate': '开始日期不能晚于结束日期',
    'Not Found': '接口不存在',
    'Internal Server Error': '服务器内部错误',
  };

  if (messageMap[raw]) {
    return messageMap[raw];
  }

  if (raw.includes('duplicate key value violates unique constraint')) {
    if (raw.includes('uk_visitor_id_doc')) {
      return '该证件号码已经注册，请更换证件号码或使用原账号登录。';
    }
    if (raw.includes('uk_visitor_phone')) {
      return '该手机号已经注册，请直接用手机号登录或更换手机号。';
    }
    return '提交的数据已存在，请检查手机号或证件号码是否重复。';
  }

  if (raw.includes('must be a positive integer')) {
    return '编号必须是大于 0 的整数';
  }

  if (raw.includes('must be a valid date in YYYY-MM-DD format')) {
    return '日期格式不正确，请重新选择日期';
  }

  if (/[A-Za-z]/.test(raw)) {
    return '操作失败，请检查填写内容后重试。';
  }

  return raw || '操作失败，请稍后重试';
}

function formatResultPayload(payload, ok = true) {
  if (typeof payload === 'string') {
    return translateMessage(payload);
  }

  if (!payload || typeof payload !== 'object') {
    return ok ? '操作成功' : '操作失败';
  }

  const data = payload.data || {};
  const lines = [payload.success === false || !ok ? '操作失败' : '操作成功'];
  if (payload.message) {
    lines.push(translateMessage(payload.message));
  }

  const visitor = data.visitor || data;
  if (visitor.visitorName && visitor.id) {
    lines.push(`游客：${visitor.visitorName}`);
    lines.push(`游客编号：${visitor.id}`);
  }

  if (data.user) {
    lines.push(`当前身份：${displayLabel(data.user.scope || data.user.role, 'scope')}`);
    if (data.user.displayName) {
      lines.push(`账号名称：${data.user.displayName}`);
    }
  }

  if (data.ticketType) {
    lines.push(`票种：${data.ticketType.ticketName || '--'}`);
    if (data.ticketType.id) {
      lines.push(`票种编号：${data.ticketType.id}`);
    }
  }

  if (data.routeProduct) {
    lines.push(`线路：${data.routeProduct.productName || '--'}`);
    if (data.routeProduct.id) {
      lines.push(`线路编号：${data.routeProduct.id}`);
    }
    if (data.routeProduct.ticketTypeId) {
      lines.push(`关联票种：${data.routeProduct.ticketTypeId}`);
    }
    if (data.routeProduct.status) {
      lines.push(`状态：${displayLabel(data.routeProduct.status, 'status')}`);
    }
  }

  if (data.orderNo) {
    lines.push(`订单号：${data.orderNo}`);
  }

  const firstItem = data.items?.[0];
  if (firstItem?.ticketCode) {
    lines.push(`票码：${firstItem.ticketCode}`);
  }
  if (firstItem?.orderItemId) {
    lines.push(`订单明细编号：${firstItem.orderItemId}`);
  }

  return lines.join('\n');
}

function showResult(element, payload, ok = true) {
  if (!element) {
    return;
  }

  element.hidden = false;
  element.dataset.state = ok ? 'ok' : 'bad';
  element.textContent = formatResultPayload(payload, ok);
}

function setStatus(element, ok, message) {
  if (!element) {
    return;
  }

  element.textContent = translateMessage(message);
  element.dataset.state = ok ? 'ok' : 'bad';
}

function setLoginMode(mode) {
  const adminMode = mode === 'admin';
  elements.visitorLoginForm.hidden = adminMode;
  elements.adminLoginForm.hidden = !adminMode;
  elements.visitorLoginResult.hidden = true;
  elements.adminLoginResult.hidden = true;

  elements.loginTitle.textContent = adminMode ? '管理员登录' : '游客登录';
  elements.loginCopy.textContent = adminMode
    ? '输入后台账号密码进入管理端，处理线路产品、窗口状态、销售日报、核销和退款。'
    : '输入手机号即可进入游客端。未注册手机号会自动创建临时游客账号，实名注册后可下单和查看订单。';
  elements.loginHint.textContent = adminMode
    ? '管理员登录后才显示后台操作区。'
    : '临时游客只能浏览线路、时段和窗口状态。';
}

function getTodayBusinessDate() {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function getAuthUser() {
  return state.auth?.user || null;
}

function isAdmin() {
  return getAuthUser()?.role === 'ADMIN';
}

function isVisitor() {
  return getAuthUser()?.role === 'VISITOR';
}

function isRegisteredVisitor() {
  const user = getAuthUser();
  return user?.role === 'VISITOR' && user?.scope === 'REGISTERED';
}

function isTempVisitor() {
  const user = getAuthUser();
  return user?.role === 'VISITOR' && user?.scope === 'TEMP';
}

function mapUserToVisitor(user) {
  if (!user || user.role !== 'VISITOR') {
    return null;
  }

  return {
    id: Number(user.visitorId || user.id),
    visitorName: user.visitorName || user.displayName,
    idType: user.idType,
    idNumber: user.idNumber,
    phone: user.phone || '',
    gender: user.gender || '',
    birthDate: user.birthDate || '',
  };
}

async function request(path, options = {}) {
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  if (state.auth?.token) {
    headers.Authorization = `Bearer ${state.auth.token}`;
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });
  const body = await response.json().catch(() => ({}));

  if (!response.ok || body.success === false) {
    throw new Error(body.message || `请求失败：${response.status}`);
  }

  return body;
}

function renderEmptyCard(message, detail = '当前条件下没有可展示的数据') {
  return `
    <article class="ticket-row empty-row">
      <div>
        <strong>${escapeHtml(message)}</strong>
        <span>${escapeHtml(detail)}</span>
      </div>
      <em>--</em>
    </article>
  `;
}

function statusTone(status) {
  const toneMap = {
    ENABLED: 'ok',
    DISABLED: 'bad',
    ON_SALE: 'ok',
    STOPPED: 'bad',
    SOLD_OUT: 'warn',
    UNCONFIGURED: 'warn',
    PAID: 'ok',
    PENDING_PAYMENT: 'warn',
    CANCELLED: 'bad',
    REFUNDED: 'bad',
    PARTIAL_REFUNDED: 'warn',
    COMPLETED: 'ok',
    UNUSED: 'ok',
    USED: 'idle',
    UNKNOWN: 'idle',
    MALE: 'ok',
    FEMALE: 'warn',
  };

  return toneMap[status] || 'idle';
}

function displayLabel(value, type = 'status') {
  const maps = {
    status: {
      ENABLED: '启用',
      DISABLED: '停用',
      ON_SALE: '售票中',
      STOPPED: '停售',
      SOLD_OUT: '已售罄',
      UNCONFIGURED: '未配置',
      PAID: '已支付',
      PENDING_PAYMENT: '待支付',
      CANCELLED: '已取消',
      REFUNDED: '已退款',
      PARTIAL_REFUNDED: '部分退款',
      COMPLETED: '已完成',
      UNUSED: '未使用',
      USED: '已核销',
      UNKNOWN: '未知',
      MALE: '男',
      FEMALE: '女',
      UNKNOWN_GENDER: '未知',
    },
    tripType: {
      ONE_WAY: '单程',
      ROUND_TRIP: '往返',
    },
    ticketCategory: {
      RAFT: '竹筏票',
      DEFAULT: '默认票',
      ADULT: '成人票',
      CHILD: '儿童票',
      STUDENT: '学生票',
      SENIOR: '老人票',
    },
    orderSource: {
      ONLINE: '线上下单',
      OFFLINE: '窗口下单',
      WINDOW: '窗口下单',
    },
    scope: {
      ADMIN: '管理员',
      VISITOR: '游客',
      REGISTERED: '实名游客',
      TEMP: '临时游客',
    },
    pierType: {
      DEPARTURE: '起点码头',
      ARRIVAL: '终点码头',
      BOTH: '双向码头',
    },
  };

  if (!value) {
    return '--';
  }

  const mapped = maps[type]?.[value];
  if (mapped) {
    return mapped;
  }

  return /[A-Za-z]/.test(String(value)) ? '未识别' : value;
}

function setNodeListHidden(nodes, hidden) {
  nodes.forEach((node) => {
    node.hidden = hidden;
  });
}

function setFormDisabled(form, disabled) {
  if (!form) {
    return;
  }

  Array.from(form.elements).forEach((element) => {
    element.disabled = disabled;
  });
}

function getSelectedTicketTypeId() {
  const selected = Array.from(elements.ticketTypeSelects).find((select) => select.value)?.value;
  return selected || state.routeProducts[0]?.ticketTypeId || state.ticketTypes[0]?.id || '';
}

function syncTicketTypeSelects(value) {
  elements.ticketTypeSelects.forEach((select) => {
    select.value = value;
  });
}

function syncVisitDateInputs(value) {
  elements.visitDateInputs.forEach((input) => {
    input.value = value;
  });
}

function getSelectableProducts() {
  if (state.routeProducts.length > 0) {
    return state.routeProducts.map((product) => ({
      id: product.ticketTypeId,
      label: product.productName,
      detail: `${displayLabel(product.tripType, 'tripType')} · ${product.windowPhone || '--'}`,
    }));
  }

  return state.ticketTypes.map((ticketType) => ({
    id: ticketType.id,
    label: ticketType.ticketName,
    detail: `¥${formatMoney(ticketType.salePrice)}`,
  }));
}

function renderAuthShell() {
  const user = getAuthUser();
  const signedIn = Boolean(user);
  document.body.dataset.auth = signedIn ? 'signed-in' : 'signed-out';
  elements.loginScreen.hidden = signedIn;
  elements.appShell.hidden = !signedIn;

  if (!signedIn) {
    return;
  }

  setNodeListHidden(elements.visitorSections, !isVisitor());
  setNodeListHidden(elements.adminSections, !isAdmin());
  setNodeListHidden(elements.visitorLinks, !isVisitor());
  setNodeListHidden(elements.adminLinks, !isAdmin());

  const accountName = user.role === 'ADMIN'
    ? `管理员：${user.displayName || user.username}`
    : `${user.scope === 'TEMP' ? '临时游客' : '实名游客'}：${user.displayName || user.visitorName}`;
  const accountDetail = user.role === 'ADMIN'
    ? `账号 ${user.username} · 后台权限`
    : `手机号 ${user.phone || '--'} · 游客编号 ${user.visitorId || user.id}`;

  elements.accountName.textContent = accountName;
  elements.accountDetail.textContent = accountDetail;
  elements.authScope.textContent = displayLabel(user.scope || user.role, 'scope');
  elements.currentVisitorSummary.textContent = accountName;
  elements.currentVisitorSummary.dataset.state = isTempVisitor() ? 'warn' : 'ok';

  if (isAdmin()) {
    elements.dashboardTitle.textContent = '管理员后台';
    elements.dashboardCopy.textContent = '查看线路产品、窗口售票状态和销售日报，并完成门票核销、退款等后台操作。';
  } else {
    elements.dashboardTitle.textContent = isTempVisitor() ? '游客端：临时访问' : '游客端：实名购票';
    elements.dashboardCopy.textContent = isTempVisitor()
      ? '临时游客可以浏览线路产品、可售时段和窗口公告，实名注册后开放下单和订单查询。'
      : '实名游客可以浏览线路产品、创建订单，并查看自己的订单记录。';
  }

  if (elements.visitorOrderTag) {
    elements.visitorOrderTag.textContent = isTempVisitor() ? '需实名注册' : '游客购票';
  }
  if (elements.tempLock) {
    elements.tempLock.hidden = !isTempVisitor();
  }
  setFormDisabled(elements.orderForm, isTempVisitor() || !isVisitor());
  if (elements.reloadVisitorOrders) {
    elements.reloadVisitorOrders.disabled = !isRegisteredVisitor();
  }

  if (isVisitor() && state.currentVisitor) {
    const visitor = state.currentVisitor;
    if (elements.visitorForm) {
      elements.visitorForm.phone.value = visitor.phone || elements.visitorForm.phone.value;
      elements.visitorForm.visitorName.value = visitor.visitorName || elements.visitorForm.visitorName.value;
      if (visitor.idType && visitor.idType !== 'TEMP_PHONE') {
        elements.visitorForm.idType.value = visitor.idType;
      }
      if (visitor.idNumber && visitor.idType !== 'TEMP_PHONE') {
        elements.visitorForm.idNumber.value = visitor.idNumber;
      }
    }
    if (elements.orderForm) {
      elements.orderForm.buyerName.value = visitor.visitorName || elements.orderForm.buyerName.value;
      elements.orderForm.buyerPhone.value = visitor.phone || elements.orderForm.buyerPhone.value;
    }
  }
}

function renderTicketTypeSelects() {
  const options = getSelectableProducts();
  const markup = options.length
    ? options.map((option) => `<option value="${escapeHtml(option.id)}">${escapeHtml(option.label)}</option>`).join('')
    : '<option value="">暂无可选线路产品</option>';

  elements.ticketTypeSelects.forEach((select) => {
    const previous = select.value;
    select.innerHTML = markup;
    if (!options.length) {
      select.value = '';
      return;
    }

    select.value = options.some((option) => String(option.id) === String(previous))
      ? previous
      : String(options[0].id);
  });

  syncTicketTypeSelects(getSelectedTicketTypeId());
}

function renderRouteProducts() {
  elements.productSummary.textContent = `${state.routeProducts.length} 条`;

  if (!state.routeProducts.length) {
    elements.routeProductLists.forEach((list) => {
      list.innerHTML = renderEmptyCard('暂无线路产品', '请确认系统已配置线路产品');
    });
    return;
  }

  const markup = state.routeProducts.map((product) => `
    <article class="ticket-row">
      <div>
        <strong>${escapeHtml(product.productName)}</strong>
        <span>${escapeHtml(displayLabel(product.tripType, 'tripType'))} · ${escapeHtml(product.raftCapacity || '--')} 人筏 · 电话 ${escapeHtml(product.windowPhone || '--')}</span>
      </div>
      <em data-state="${statusTone(product.saleStatus)}">${escapeHtml(displayLabel(product.saleStatus, 'status'))}</em>
    </article>
  `).join('');

  elements.routeProductLists.forEach((list) => {
    list.innerHTML = markup;
  });
  renderTicketTypeSelects();
}

function renderPiers() {
  if (!elements.pierList) {
    return;
  }

  if (!state.piers.length) {
    elements.pierList.innerHTML = renderEmptyCard('暂无可用码头', '请先在数据库中维护码头基础数据');
    return;
  }

  elements.pierList.innerHTML = state.piers.map((pier) => `
    <article class="ticket-row">
      <div>
        <strong>${escapeHtml(pier.pierName)}</strong>
        <span>${escapeHtml(displayLabel(pier.pierType, 'pierType'))} · 电话 ${escapeHtml(pier.contactPhone || '--')} · 排序 ${escapeHtml(pier.sortNo)}</span>
      </div>
      <em data-state="${statusTone(pier.status)}">${escapeHtml(displayLabel(pier.status, 'status'))}</em>
    </article>
  `).join('');

  const optionMarkup = state.piers.length
    ? state.piers.map((pier) => `<option value="${escapeHtml(pier.id)}">${escapeHtml(pier.pierName)}</option>`).join('')
    : '<option value="">暂无可选码头</option>';

  const keepStartValue = elements.startPierSelect?.value;
  const keepEndValue = elements.endPierSelect?.value;
  if (elements.startPierSelect) {
    elements.startPierSelect.innerHTML = optionMarkup;
    elements.startPierSelect.value = state.piers.some((pier) => String(pier.id) === String(keepStartValue))
      ? keepStartValue
      : String(state.piers[0]?.id || '');
  }
  if (elements.endPierSelect) {
    elements.endPierSelect.innerHTML = optionMarkup;
    elements.endPierSelect.value = state.piers.some((pier) => String(pier.id) === String(keepEndValue))
      ? keepEndValue
      : String(state.piers[1]?.id || state.piers[0]?.id || '');
  }
}

function getAdminTimeSlotRouteProductId() {
  const selected = elements.adminTimeSlotRouteSelect?.value;
  return selected || state.adminRouteProducts[0]?.id || '';
}

function getAdminTimeSlotVisitDate() {
  return elements.adminTimeSlotDate?.value || state.businessDate || getTodayBusinessDate();
}

function renderAdminTimeSlotRouteSelect() {
  if (!elements.adminTimeSlotRouteSelect) {
    return;
  }

  const previous = elements.adminTimeSlotRouteSelect.value;
  const options = state.adminRouteProducts.map((product) => {
    const status = displayLabel(product.routeStatus, 'status');
    const label = `${product.productName} · ${product.ticketName || '--'} · ${status}`;
    return `<option value="${escapeHtml(product.id)}">${escapeHtml(label)}</option>`;
  });

  elements.adminTimeSlotRouteSelect.innerHTML = options.length
    ? options.join('')
    : '<option value="">暂无可选线路产品</option>';

  if (!options.length) {
    elements.adminTimeSlotRouteSelect.value = '';
    return;
  }

  const selected = state.adminRouteProducts.some((product) => String(product.id) === String(previous))
    ? previous
    : String(state.adminRouteProducts[0].id);
  elements.adminTimeSlotRouteSelect.value = selected;
}

function renderAdminRouteProducts() {
  if (!elements.adminRouteProductList) {
    renderAdminTimeSlotRouteSelect();
    renderAdminTicketPreview();
    return;
  }

  if (!state.adminRouteProducts.length) {
    elements.adminRouteProductList.innerHTML = renderEmptyCard('暂无后台线路产品', '管理员新增后会出现在这里');
    renderAdminTimeSlotRouteSelect();
    renderAdminTicketPreview();
    return;
  }

  elements.adminRouteProductList.innerHTML = state.adminRouteProducts.map((product) => {
    const active = String(product.routeStatus) === 'ENABLED';
    return `
      <article class="ticket-row admin-ticket-row">
        <div>
          <strong>${escapeHtml(product.productName)}</strong>
          <span>${escapeHtml(product.ticketName || '--')} · ${escapeHtml(displayLabel(product.tripType, 'tripType'))} · ${escapeHtml(product.startPierName || '--')} → ${escapeHtml(product.endPierName || '--')}</span>
          <span>票价 ¥${formatMoney(product.salePrice)} · 原价 ¥${formatMoney(product.originalPrice)} · ${escapeHtml(product.windowPhone || '--')}</span>
        </div>
        <div class="row-actions">
          <em data-state="${statusTone(product.routeStatus)}">${escapeHtml(displayLabel(product.routeStatus, 'status'))}</em>
          ${active
            ? `<button type="button" class="mini-button" data-delete-route-product="${escapeHtml(product.id)}">删除/停用</button>`
            : `<button type="button" class="mini-button" data-restore-route-product="${escapeHtml(product.id)}">恢复启用</button>`}
        </div>
      </article>
    `;
  }).join('');

  elements.adminRouteProductList.querySelectorAll('[data-delete-route-product]').forEach((button) => {
    button.addEventListener('click', async () => {
      const routeProductId = Number(button.dataset.deleteRouteProduct);
      if (!routeProductId) {
        return;
      }

      button.disabled = true;
      try {
        const result = await request(`/api/admin/route-products/${routeProductId}`, {
          method: 'DELETE',
        });
        showResult(elements.routeProductResult, result);
        await Promise.all([loadAdminRouteProducts(), loadRouteProducts(), loadTicketTypes()]);
        await loadAdminTimeSlots();
      } catch (error) {
        showResult(elements.routeProductResult, error.message, false);
      } finally {
        button.disabled = false;
      }
    });
  });

  elements.adminRouteProductList.querySelectorAll('[data-restore-route-product]').forEach((button) => {
    button.addEventListener('click', async () => {
      const routeProductId = Number(button.dataset.restoreRouteProduct);
      if (!routeProductId) {
        return;
      }

      button.disabled = true;
      try {
        const result = await request(`/api/admin/route-products/${routeProductId}/restore`, {
          method: 'PATCH',
        });
        showResult(elements.routeProductResult, result);
        await Promise.all([loadAdminRouteProducts(), loadRouteProducts(), loadTicketTypes()]);
        await loadAdminTimeSlots();
      } catch (error) {
        showResult(elements.routeProductResult, error.message, false);
      } finally {
        button.disabled = false;
      }
    });
  });

  renderAdminTimeSlotRouteSelect();
  renderAdminTicketPreview();
}

function getAdminTicketUsageEntries() {
  const entries = [];
  const seen = new Set();

  if (state.adminRouteProducts.length) {
    state.adminRouteProducts.forEach((product) => {
      if (!product.ticketName) {
        return;
      }

      const key = String(product.ticketTypeId || product.ticketName);
      if (seen.has(key)) {
        return;
      }
      seen.add(key);

      entries.push({
        ticketName: product.ticketName,
        ticketCategory: product.ticketCategory,
        routeName: product.productName,
        routeStatus: product.routeStatus,
        ticketStatus: product.ticketStatus,
      });
    });
    return entries;
  }

  state.ticketTypes.forEach((ticketType) => {
    if (!ticketType.ticketName) {
      return;
    }

    const key = String(ticketType.id || ticketType.ticketName);
    if (seen.has(key)) {
      return;
    }
    seen.add(key);

    entries.push({
      ticketName: ticketType.ticketName,
      ticketCategory: ticketType.ticketCategory,
      routeName: '',
      routeStatus: ticketType.status,
      ticketStatus: ticketType.status,
    });
  });

  return entries;
}

function renderAdminTicketPreview() {
  if (!elements.adminTicketPreview) {
    return;
  }

  const entries = getAdminTicketUsageEntries();
  if (!entries.length) {
    elements.adminTicketPreview.innerHTML = `
      <strong>已占用票种名</strong>
      <span>暂无已占用票种名</span>
    `;
    return;
  }

  elements.adminTicketPreview.innerHTML = `
    <strong>已占用票种名</strong>
    <div class="ticket-badge-grid">
      ${entries.map((entry) => `
        <article class="ticket-badge">
          <strong>${escapeHtml(entry.ticketName)}</strong>
          <span>${escapeHtml(displayLabel(entry.ticketCategory || 'DEFAULT', 'ticketCategory'))}${entry.routeName ? ` · ${escapeHtml(entry.routeName)}` : ''}</span>
          <span>${escapeHtml(displayLabel(entry.routeStatus, 'status'))} · 票种${escapeHtml(displayLabel(entry.ticketStatus, 'status'))}</span>
        </article>
      `).join('')}
    </div>
  `;
}

function renderTicketTypes() {
  if (!elements.ticketTypeList) {
    renderAdminTicketPreview();
    renderTicketTypeSelects();
    return;
  }

  if (!state.ticketTypes.length) {
    elements.ticketTypeList.innerHTML = renderEmptyCard('暂无基础票种', '请确认系统已配置基础票种');
    renderAdminTicketPreview();
    return;
  }

  elements.ticketTypeList.innerHTML = state.ticketTypes.map((ticketType) => `
    <article class="ticket-row">
      <div>
        <strong>${escapeHtml(ticketType.ticketName)}</strong>
        <span>原价 ¥${formatMoney(ticketType.originalPrice)} · 售价 ¥${formatMoney(ticketType.salePrice)} · ${escapeHtml(displayLabel(ticketType.ticketCategory || 'DEFAULT', 'ticketCategory'))}</span>
      </div>
      <em data-state="${statusTone(ticketType.status)}">${escapeHtml(displayLabel(ticketType.status, 'status'))}</em>
    </article>
  `).join('');
  renderAdminTicketPreview();
  renderTicketTypeSelects();
}

function renderAdminTimeSlots() {
  if (!elements.adminTimeSlotList) {
    return;
  }

  if (!isAdmin()) {
    elements.adminTimeSlotList.innerHTML = renderEmptyCard('请先以管理员身份登录', '管理员登录后可维护可售时段');
    return;
  }

  if (!state.adminRouteProducts.length) {
    elements.adminTimeSlotList.innerHTML = renderEmptyCard('暂无可配置线路产品', '请先新增线路产品再配置时段');
    return;
  }

  if (!state.adminTimeSlots.length) {
    elements.adminTimeSlotList.innerHTML = renderEmptyCard('暂无可售时段', '选择线路产品和日期后可新增时段');
    return;
  }

  elements.adminTimeSlotList.innerHTML = state.adminTimeSlots.map((slot) => `
    <article class="slot-row">
      <div>
        <strong>${escapeHtml(slot.slotStartTime || '全天')} - ${escapeHtml(slot.slotEndTime || '不限')}</strong>
        <span>${escapeHtml(slot.visitDate)} · 库存 ${escapeHtml(slot.quotaTotal)} · 已售 ${escapeHtml(slot.quotaSold)} · 已核销 ${escapeHtml(slot.quotaCheckedIn)}</span>
      </div>
      <em data-state="${statusTone(slot.status)}">${escapeHtml(displayLabel(slot.status, 'status'))}</em>
    </article>
  `).join('');
}

function renderOfflineSaleNotices() {
  if (!elements.offlineNoticeList) {
    return;
  }

  if (!state.offlineSaleNotices.length) {
    elements.offlineNoticeList.innerHTML = renderEmptyCard('今日暂无窗口公告', '默认视为“未配置”，可继续演示待配置状态');
    return;
  }

  elements.offlineNoticeList.innerHTML = state.offlineSaleNotices.map((notice) => `
    <article class="notice-row">
      <div class="notice-main">
        <div>
          <strong>${escapeHtml(notice.productName)}</strong>
          <span>${escapeHtml(notice.businessDate)} · ${escapeHtml(notice.windowPhone || '--')} · ${escapeHtml(displayLabel(notice.tripType, 'tripType'))}</span>
        </div>
        <b data-state="${statusTone(notice.saleStatus)}">${escapeHtml(displayLabel(notice.saleStatus, 'status'))}</b>
      </div>
      <p>${escapeHtml(notice.remark || '暂无窗口备注')}</p>
    </article>
  `).join('');
}

function renderTimeSlots() {
  elements.slotSummary.textContent = `${state.timeSlots.length} 个`;

  if (!state.timeSlots.length) {
    elements.timeSlotList.innerHTML = renderEmptyCard('暂无可预约时段', '当前线路产品在该日期下没有可售配额');
    elements.timeSlotSelect.innerHTML = '<option value="">暂无可选时段</option>';
    return;
  }

  elements.timeSlotList.innerHTML = state.timeSlots.map((slot) => `
    <article class="slot-row">
      <div>
        <strong>${escapeHtml(slot.slotStartTime || '全天')} - ${escapeHtml(slot.slotEndTime || '不限')}</strong>
        <span>${escapeHtml(slot.visitDate)} · 剩余 ${escapeHtml(slot.remainingQuota)}</span>
      </div>
      <em>${escapeHtml(slot.quotaSold)}/${escapeHtml(slot.quotaTotal)}</em>
    </article>
  `).join('');

  elements.timeSlotSelect.innerHTML = state.timeSlots.map((slot) => `
    <option value="${escapeHtml(slot.id)}">${escapeHtml(slot.visitDate)} ${escapeHtml(slot.slotStartTime || '全天')} 剩余 ${escapeHtml(slot.remainingQuota)}</option>
  `).join('');
}

function renderReport() {
  if (!elements.reportBody) {
    return;
  }

  if (!state.reportItems.length) {
    elements.reportSummary.textContent = '--';
    elements.reportBody.innerHTML = '<tr><td colspan="3">暂无数据</td></tr>';
    return;
  }

  const totalCount = state.reportItems.reduce((sum, item) => sum + Number(item.soldCount), 0);
  const totalAmount = state.reportItems.reduce((sum, item) => sum + Number(item.soldAmount), 0);
  elements.reportSummary.textContent = `${totalCount} 张 · ¥${formatMoney(totalAmount)}`;
  elements.reportBody.innerHTML = state.reportItems.map((item) => `
    <tr>
      <td>${escapeHtml(item.visitDate)}</td>
      <td>${escapeHtml(item.soldCount)}</td>
      <td>¥${formatMoney(item.soldAmount)}</td>
    </tr>
  `).join('');
}

function renderVisitorOrders() {
  if (!elements.visitorOrders) {
    return;
  }

  if (isTempVisitor()) {
    elements.visitorOrders.innerHTML = renderEmptyCard('临时游客无法查看订单', '完成实名注册后会开放我的订单');
    return;
  }

  if (!isRegisteredVisitor()) {
    elements.visitorOrders.innerHTML = renderEmptyCard('请先以实名游客登录', '游客注册完成后可以查看自己的订单');
    return;
  }

  if (!state.visitorOrders.length) {
    elements.visitorOrders.innerHTML = renderEmptyCard('当前游客暂无订单', '创建订单后会显示在这里');
    return;
  }

  elements.visitorOrders.innerHTML = state.visitorOrders.map((order) => `
    <article class="order-card">
      <div class="order-card-head">
        <div>
          <strong>${escapeHtml(order.orderNo)}</strong>
          <span>${escapeHtml(order.orderTime || '--')} · ${escapeHtml(displayLabel(order.orderSource, 'orderSource'))}</span>
        </div>
          <div class="order-card-summary">
          <b data-state="${statusTone(order.orderStatus)}">${escapeHtml(displayLabel(order.orderStatus, 'status'))}</b>
          <span>¥${formatMoney(order.payableAmount)}</span>
        </div>
      </div>
      <div class="order-meta">
        <span>支付 ${escapeHtml(displayLabel(order.paymentStatus, 'status'))}</span>
        <span>购票人 ${escapeHtml(order.buyerName)} ${escapeHtml(order.buyerPhone)}</span>
        <span>明细 ${escapeHtml(order.items.length)} 条</span>
      </div>
      <div class="order-items">
        ${order.items.map((item) => `
          <article class="order-item">
            <div>
              <strong>${escapeHtml(item.productName)}</strong>
              <span>${escapeHtml(item.ticketCode)} · ${escapeHtml(item.visitDate)} · ${escapeHtml(item.ticketName)}</span>
            </div>
            <em data-state="${statusTone(item.itemStatus)}">${escapeHtml(displayLabel(item.itemStatus, 'status'))}</em>
          </article>
        `).join('')}
      </div>
    </article>
  `).join('');
}

async function loadHealth() {
  try {
    const service = await request('/api/health');
    setStatus(elements.serviceStatus, true, service.message);
  } catch (error) {
    setStatus(elements.serviceStatus, false, error.message);
  }

  try {
    const db = await request('/api/db/health');
    setStatus(elements.dbStatus, true, db.message);
  } catch (error) {
    setStatus(elements.dbStatus, false, error.message);
  }
}

async function loadTicketTypes() {
  const result = await request('/api/ticket-types');
  state.ticketTypes = result.data || [];
  renderTicketTypes();
}

async function loadRouteProducts() {
  const result = await request('/api/route-products');
  state.routeProducts = result.data || [];
  renderRouteProducts();
}

async function loadPiers() {
  if (!isAdmin()) {
    state.piers = [];
    renderPiers();
    return;
  }

  const result = await request('/api/piers');
  state.piers = result.data || [];
  renderPiers();
}

async function loadAdminRouteProducts() {
  if (!isAdmin()) {
    state.adminRouteProducts = [];
    renderAdminRouteProducts();
    return;
  }

  const result = await request('/api/admin/route-products');
  state.adminRouteProducts = result.data || [];
  renderAdminRouteProducts();
}

async function loadAdminTimeSlots() {
  if (!isAdmin()) {
    state.adminTimeSlots = [];
    renderAdminTimeSlots();
    return;
  }

  const routeProductId = getAdminTimeSlotRouteProductId();
  const visitDate = getAdminTimeSlotVisitDate();

  if (!routeProductId || !visitDate) {
    state.adminTimeSlots = [];
    renderAdminTimeSlots();
    return;
  }

  const query = new URLSearchParams({
    routeProductId,
    visitDate,
  });
  const result = await request(`/api/admin/time-slots?${query.toString()}`);
  state.adminTimeSlots = result.data || [];
  renderAdminTimeSlots();
}

async function loadOfflineSaleNotices() {
  const businessDate = elements.noticeBusinessDate?.value || state.businessDate || getTodayBusinessDate();
  state.businessDate = businessDate;
  elements.currentBusinessDate.textContent = businessDate;
  if (elements.noticeBusinessDate) {
    elements.noticeBusinessDate.value = businessDate;
  }

  const query = new URLSearchParams({ businessDate });
  const result = await request(`/api/reports/offline-sale-notices?${query.toString()}`);
  state.offlineSaleNotices = (result.data || []).map((notice) => ({
    ...notice,
    saleStatus: notice.saleStatus || 'UNCONFIGURED',
  }));
  renderOfflineSaleNotices();
}

async function loadTimeSlots() {
  const ticketTypeId = getSelectedTicketTypeId();
  const visitDate = elements.visitDateInputs[0]?.value;

  if (!ticketTypeId || !visitDate) {
    state.timeSlots = [];
    renderTimeSlots();
    return;
  }

  const query = new URLSearchParams({ ticketTypeId, visitDate });
  const result = await request(`/api/time-slots?${query.toString()}`);
  state.timeSlots = result.data || [];
  renderTimeSlots();
}

async function loadReport() {
  if (!isAdmin()) {
    state.reportItems = [];
    renderReport();
    return;
  }

  const ticketTypeId = getSelectedTicketTypeId();
  const startDate = elements.reportStart?.value;
  const endDate = elements.reportEnd?.value;

  if (!ticketTypeId || !startDate || !endDate) {
    state.reportItems = [];
    renderReport();
    return;
  }

  const query = new URLSearchParams({ ticketTypeId, startDate, endDate });
  const result = await request(`/api/reports/sales?${query.toString()}`);
  state.reportItems = result.data.items || [];
  renderReport();
}

async function loadVisitorOrders() {
  if (!isRegisteredVisitor() || !state.currentVisitor?.id) {
    state.visitorOrders = [];
    renderVisitorOrders();
    return;
  }

  const result = await request(`/api/visitors/${state.currentVisitor.id}/orders`);
  state.visitorOrders = result.data.orders || [];
  renderVisitorOrders();
}

async function loadDashboardData() {
  renderAuthShell();
  await loadHealth();

  if (!state.auth) {
    return;
  }

  try {
    const tasks = [loadTicketTypes(), loadRouteProducts(), loadOfflineSaleNotices()];
    if (isAdmin()) {
      tasks.push(loadPiers(), loadAdminRouteProducts());
    }

    await Promise.all(tasks);
    await loadTimeSlots();
    if (isAdmin()) {
      await loadAdminTimeSlots();
    }
    await Promise.all([loadReport(), loadVisitorOrders()]);
  } catch (error) {
    showResult(isAdmin() ? elements.adminLoginResult : elements.visitorLoginResult, error.message, false);
  }
}

function persistAuth(data) {
  state.auth = {
    token: data.token,
    user: data.user,
  };
  state.currentVisitor = data.visitor || mapUserToVisitor(data.user);
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify({
    auth: state.auth,
    currentVisitor: state.currentVisitor,
  }));
}

function clearAuth() {
  state.auth = null;
  state.currentVisitor = null;
  state.visitorOrders = [];
  window.localStorage.removeItem(STORAGE_KEY);
  renderAuthShell();
  renderVisitorOrders();
}

async function hydrateAuth() {
  const raw = window.localStorage.getItem(STORAGE_KEY);
  if (!raw) {
    renderAuthShell();
    await loadHealth();
    return;
  }

  try {
    const cached = JSON.parse(raw);
    if (!cached?.auth?.token || !cached?.auth?.user) {
      throw new Error('invalid cache');
    }

    state.auth = cached.auth;
    state.currentVisitor = cached.currentVisitor || mapUserToVisitor(cached.auth.user);
    await request('/api/auth/me');
    await loadDashboardData();
  } catch (_error) {
    clearAuth();
    await loadHealth();
  }
}

async function handleVisitorLogin(event) {
  event.preventDefault();
  const form = new FormData(event.currentTarget);

  try {
    const result = await request('/api/auth/visitor/login', {
      method: 'POST',
      body: JSON.stringify({ phone: form.get('phone') }),
    });
    persistAuth(result.data);
    showResult(elements.visitorLoginResult, result);
    await loadDashboardData();
  } catch (error) {
    showResult(elements.visitorLoginResult, error.message, false);
  }
}

async function handleAdminLogin(event) {
  event.preventDefault();
  const form = new FormData(event.currentTarget);

  try {
    const result = await request('/api/auth/admin/login', {
      method: 'POST',
      body: JSON.stringify({
        username: form.get('username'),
        password: form.get('password'),
      }),
    });
    persistAuth(result.data);
    showResult(elements.adminLoginResult, result);
    await loadDashboardData();
  } catch (error) {
    showResult(elements.adminLoginResult, error.message, false);
  }
}

async function handleLogout() {
  try {
    await request('/api/auth/logout', { method: 'POST' });
  } catch (_error) {
    // 本地退出不依赖服务器响应。
  }

  clearAuth();
}

async function handleVisitorSubmit(event) {
  event.preventDefault();
  const form = new FormData(event.currentTarget);

  try {
    const result = await request('/api/visitors', {
      method: 'POST',
      body: JSON.stringify({
        visitorName: form.get('visitorName'),
        idType: form.get('idType'),
        idNumber: form.get('idNumber'),
        phone: form.get('phone'),
        gender: form.get('gender'),
        birthDate: form.get('birthDate'),
      }),
    });

    persistAuth(result.data);
    showResult(elements.visitorResult, result);
    await loadDashboardData();
  } catch (error) {
    showResult(elements.visitorResult, error.message, false);
  }
}

async function handleOrderSubmit(event) {
  event.preventDefault();

  if (!isRegisteredVisitor()) {
    showResult(elements.orderResult, '临时游客不能下单，请先完成实名注册。', false);
    return;
  }

  const form = new FormData(event.currentTarget);
  const payload = {
    buyerName: form.get('buyerName'),
    buyerPhone: form.get('buyerPhone'),
    orderSource: 'ONLINE',
    items: [
      {
        ticketTypeId: Number(form.get('ticketTypeId')),
        timeSlotId: Number(form.get('timeSlotId')),
        visitDate: form.get('visitDate'),
      },
    ],
  };

  try {
    const result = await request('/api/orders', {
      method: 'POST',
      body: JSON.stringify(payload),
    });

    const firstItem = result.data.items?.[0];
    if (firstItem && elements.checkinForm && elements.refundForm) {
      elements.checkinForm.ticketCode.value = firstItem.ticketCode;
      elements.refundForm.orderItemId.value = firstItem.orderItemId;
    }

    showResult(elements.orderResult, result);
    await Promise.all([loadTimeSlots(), loadVisitorOrders()]);
  } catch (error) {
    showResult(elements.orderResult, error.message, false);
  }
}

async function handleRouteProductSubmit(event) {
  event.preventDefault();

  if (!isAdmin()) {
    showResult(elements.routeProductResult, '请使用管理员账号登录后再操作。', false);
    return;
  }

  const form = new FormData(event.currentTarget);
  const payload = {
    productName: form.get('productName'),
    ticketName: form.get('ticketName'),
    startPierId: form.get('startPierId'),
    endPierId: form.get('endPierId'),
    tripType: form.get('tripType'),
    raftCapacity: form.get('raftCapacity'),
    originalPrice: form.get('originalPrice'),
    salePrice: form.get('salePrice'),
    windowPhone: form.get('windowPhone'),
    ticketCategory: form.get('ticketCategory'),
    description: form.get('description'),
    refundRule: form.get('refundRule'),
    isRealNameRequired: form.get('isRealNameRequired') === 'on',
    routeStatus: form.get('routeStatus'),
  };

  try {
    const result = await request('/api/admin/route-products', {
      method: 'POST',
      body: JSON.stringify(payload),
    });

    showResult(elements.routeProductResult, result);
    await Promise.all([loadAdminRouteProducts(), loadRouteProducts(), loadTicketTypes(), loadPiers()]);
    await loadAdminTimeSlots();
  } catch (error) {
    showResult(elements.routeProductResult, error.message, false);
  }
}

async function handleAdminTimeSlotSubmit(event) {
  event.preventDefault();

  if (!isAdmin()) {
    showResult(elements.adminTimeSlotResult, '请使用管理员账号登录后再操作。', false);
    return;
  }

  const form = new FormData(event.currentTarget);
  const payload = {
    routeProductId: form.get('routeProductId'),
    visitDate: form.get('visitDate'),
    slotStartTime: form.get('slotStartTime'),
    slotEndTime: form.get('slotEndTime'),
    quotaTotal: form.get('quotaTotal'),
    status: form.get('status'),
  };

  try {
    const result = await request('/api/admin/time-slots', {
      method: 'POST',
      body: JSON.stringify(payload),
    });

    showResult(elements.adminTimeSlotResult, result);
    await Promise.all([loadAdminTimeSlots(), loadTimeSlots()]);
  } catch (error) {
    showResult(elements.adminTimeSlotResult, error.message, false);
  }
}

async function handleCheckinSubmit(event) {
  event.preventDefault();
  const form = new FormData(event.currentTarget);

  try {
    const result = await request('/api/checkins', {
      method: 'POST',
      body: JSON.stringify({
        ticketCode: form.get('ticketCode'),
        operatorId: Number(form.get('operatorId')),
        checkinGate: form.get('checkinGate'),
      }),
    });
    showResult(elements.checkinResult, result);
    await Promise.all([loadReport(), loadOfflineSaleNotices()]);
  } catch (error) {
    showResult(elements.checkinResult, error.message, false);
  }
}

async function handleRefundSubmit(event) {
  event.preventDefault();
  const form = new FormData(event.currentTarget);

  try {
    const result = await request('/api/refunds', {
      method: 'POST',
      body: JSON.stringify({
        orderItemId: Number(form.get('orderItemId')),
        operatorId: Number(form.get('operatorId')),
        reason: form.get('reason'),
      }),
    });
    showResult(elements.refundResult, result);
    await Promise.all([loadTimeSlots(), loadReport(), loadOfflineSaleNotices()]);
  } catch (error) {
    showResult(elements.refundResult, error.message, false);
  }
}

function setInitialDates() {
  const today = getTodayBusinessDate();
  state.businessDate = today;
  elements.apiBase.textContent = '服务已连接';
  elements.currentBusinessDate.textContent = today;
  if (elements.noticeBusinessDate) {
    elements.noticeBusinessDate.value = today;
  }
  if (elements.adminTimeSlotDate) {
    elements.adminTimeSlotDate.value = today;
  }
  if (elements.reportStart) {
    elements.reportStart.value = today;
  }
  if (elements.reportEnd) {
    elements.reportEnd.value = today;
  }
  syncVisitDateInputs(today);
}

function bindEvents() {
  elements.visitorLoginForm?.addEventListener('submit', handleVisitorLogin);
  elements.adminLoginForm?.addEventListener('submit', handleAdminLogin);
  elements.showAdminLogin?.addEventListener('click', () => setLoginMode('admin'));
  elements.showVisitorLogin?.addEventListener('click', () => setLoginMode('visitor'));
  elements.logoutButton?.addEventListener('click', handleLogout);
  elements.visitorForm?.addEventListener('submit', handleVisitorSubmit);
  elements.orderForm?.addEventListener('submit', handleOrderSubmit);
  elements.routeProductForm?.addEventListener('submit', handleRouteProductSubmit);
  elements.adminTimeSlotForm?.addEventListener('submit', handleAdminTimeSlotSubmit);
  elements.checkinForm?.addEventListener('submit', handleCheckinSubmit);
  elements.refundForm?.addEventListener('submit', handleRefundSubmit);
  elements.refreshButton?.addEventListener('click', loadDashboardData);
  elements.reloadVisitorOrders?.addEventListener('click', loadVisitorOrders);
  elements.noticeBusinessDate?.addEventListener('change', loadOfflineSaleNotices);
  elements.reportStart?.addEventListener('change', loadReport);
  elements.reportEnd?.addEventListener('change', loadReport);
  elements.adminTimeSlotRouteSelect?.addEventListener('change', loadAdminTimeSlots);
  elements.adminTimeSlotDate?.addEventListener('change', loadAdminTimeSlots);

  elements.ticketTypeSelects.forEach((select) => {
    select.addEventListener('change', async (event) => {
      syncTicketTypeSelects(event.target.value);
      await Promise.all([loadTimeSlots(), loadReport()]);
    });
  });

  elements.visitDateInputs.forEach((input) => {
    input.addEventListener('change', async (event) => {
      syncVisitDateInputs(event.target.value);
      await loadTimeSlots();
    });
  });
}

setInitialDates();
bindEvents();
hydrateAuth();
