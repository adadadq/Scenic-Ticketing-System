export function normalizePhone(value?: string) {
  return value ? value.replace(/[\s-]/g, '') : value
}
