const ticketNameByCategory: Record<string, string> = {
  ADULT: '遇龙河成人票',
  CHILD: '遇龙河儿童票',
  FAMILY: '遇龙河家庭票',
  SENIOR: '遇龙河长者票',
  STUDENT: '遇龙河学生票',
}

const ticketNameByEnglishKeyword = [
  { keyword: 'adult', label: '遇龙河成人票' },
  { keyword: 'child', label: '遇龙河儿童票' },
  { keyword: 'family', label: '遇龙河家庭票' },
  { keyword: 'senior', label: '遇龙河长者票' },
  { keyword: 'student', label: '遇龙河学生票' },
] as const

const descriptionMap: Record<string, string> = {
  'day admission': '当天入园有效',
  'refundable before use': '未使用前可申请退款',
}

function hasChinese(value: string) {
  return /[\u4e00-\u9fff]/.test(value)
}

function normalize(value: string) {
  return value.trim().toLowerCase()
}

function hasAny(value: string, keywords: string[]) {
  return keywords.some((keyword) => value.includes(keyword))
}

export function scenicTicketName(value: string, category?: string | null) {
  const trimmed = value.trim()

  if (!trimmed) {
    return trimmed
  }

  if (hasChinese(trimmed)) {
    return trimmed
  }

  const normalizedCategory = category?.trim().toUpperCase()
  if (normalizedCategory && ticketNameByCategory[normalizedCategory]) {
    return ticketNameByCategory[normalizedCategory]
  }

  const normalizedValue = normalize(trimmed)
  const matchedTicket = ticketNameByEnglishKeyword.find(({ keyword }) => normalizedValue.includes(keyword))

  return matchedTicket?.label ?? value
}

export function scenicProductName(value: string, category?: string | null) {
  const trimmed = value.trim()

  if (!trimmed) {
    return trimmed
  }

  if (hasChinese(trimmed)) {
    return trimmed
  }

  const normalizedValue = normalize(trimmed)
  const ticketName = scenicTicketName(trimmed, category).replace(/^遇龙河/, '')

  if (hasAny(normalizedValue, ['golden dragon', 'jinlong']) && hasAny(normalizedValue, ['jiu county', 'jiuxian'])) {
    return `金龙桥至旧县${ticketName}`
  }

  if (normalizedValue.includes('yulong')) {
    if (ticketName && ticketName !== trimmed) {
      return `遇龙河竹筏${ticketName}`
    }

    return '遇龙河竹筏漂流'
  }

  return value
}

export function scenicDescription(value?: string | null) {
  const trimmed = value?.trim() ?? ''

  if (!trimmed) {
    return trimmed
  }

  if (hasChinese(trimmed)) {
    return trimmed
  }

  return descriptionMap[normalize(trimmed)] ?? trimmed
}
