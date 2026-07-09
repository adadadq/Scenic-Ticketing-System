export function createE2eIdentity({ env = process.env, now = Date.now(), realApiBaseUrl = '' } = {}) {
  const runStamp = String(now)
  const visitorName = env.E2E_VISITOR_NAME || (realApiBaseUrl ? `测试游客${runStamp.slice(-4)}` : '张三')
  const phone = env.E2E_PHONE || (realApiBaseUrl ? `139${runStamp.slice(-8)}` : '13911112222')
  const username = env.E2E_USERNAME || (realApiBaseUrl ? `visitor_${runStamp.slice(-8)}` : 'zhangsan_001')
  const password = env.E2E_PASSWORD || 'Visitor123'

  return {
    password,
    phone,
    phoneWithSeparators: `${phone.slice(0, 3)} ${phone.slice(3, 7)}-${phone.slice(7)}`,
    runStamp,
    username,
    visitorName,
  }
}
