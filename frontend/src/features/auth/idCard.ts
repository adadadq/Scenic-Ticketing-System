const ID_CARD_RE = /^\d{17}[\dXx]$/
const ID_CARD_WEIGHTS = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
const ID_CARD_CHECK_CODES = '10X98765432'
const DAYS_IN_MONTH = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

function isLeapYear(year: number) {
  return year % 400 === 0 || (year % 4 === 0 && year % 100 !== 0)
}

function hasValidBirthDate(idNumber: string) {
  const year = Number(idNumber.slice(6, 10))
  const month = Number(idNumber.slice(10, 12))
  const day = Number(idNumber.slice(12, 14))

  if (year < 1 || month < 1 || month > 12 || day < 1) {
    return false
  }

  const daysInMonth = month === 2 && isLeapYear(year) ? 29 : DAYS_IN_MONTH[month - 1]

  return day <= daysInMonth
}

export function normalizeIdCard(value: string) {
  return value.trim().toUpperCase()
}

export function isValidIdCard(value: string) {
  const idNumber = normalizeIdCard(value)

  if (!ID_CARD_RE.test(idNumber) || !hasValidBirthDate(idNumber)) {
    return false
  }

  const sum = ID_CARD_WEIGHTS.reduce((total, weight, index) => total + Number(idNumber[index]) * weight, 0)

  return ID_CARD_CHECK_CODES[sum % 11] === idNumber[17]
}
