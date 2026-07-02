export function createChineseIdNumber(base17) {
  const factors = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
  const checksums = ['1', '0', 'X', '9', '8', '7', '6', '5', '4', '3', '2']
  const sum = [...base17].reduce((total, digit, index) => total + Number(digit) * factors[index], 0)

  return `${base17}${checksums[sum % 11]}`
}

export function createE2eIdentity({ env = process.env, now = Date.now(), realApiBaseUrl = '' } = {}) {
  const runStamp = String(now)
  const visitorName = env.E2E_VISITOR_NAME || (realApiBaseUrl ? `E2E User ${runStamp.slice(-4)}` : 'Zhang San')
  const phone = env.E2E_PHONE || (realApiBaseUrl ? `139${runStamp.slice(-8)}` : '13911112222')
  const idNumber = env.E2E_ID_NUMBER || (
    realApiBaseUrl ? createChineseIdNumber(`11010519900101${runStamp.slice(-3).padStart(3, '0')}`) : '11010519491231002X'
  )

  return {
    idNumber,
    phone,
    phoneWithSeparators: `${phone.slice(0, 3)} ${phone.slice(3, 7)}-${phone.slice(7)}`,
    runStamp,
    visitorName,
  }
}
