export class CdpClient {
  constructor(url) {
    this.id = 0
    this.pending = new Map()
    this.socket = new WebSocket(url)
  }

  connect() {
    return new Promise((resolve, reject) => {
      this.socket.addEventListener('open', resolve, { once: true })
      this.socket.addEventListener('error', reject, { once: true })
      this.socket.addEventListener('message', (event) => {
        const message = JSON.parse(event.data)
        const pending = this.pending.get(message.id)

        if (!pending) {
          return
        }

        this.pending.delete(message.id)

        if (message.error) {
          pending.reject(new Error(message.error.message))
          return
        }

        pending.resolve(message.result)
      })
    })
  }

  send(method, params = {}) {
    const id = ++this.id
    const payload = JSON.stringify({ id, method, params })

    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject })
      this.socket.send(payload)
    })
  }

  close() {
    this.socket.close()
  }
}

export async function waitForJson(url, timeoutMs = 5000) {
  const deadline = Date.now() + timeoutMs
  let lastError

  while (Date.now() < deadline) {
    try {
      const response = await fetch(url)
      if (response.ok) {
        return await response.json()
      }
    } catch (error) {
      lastError = error
    }

    await new Promise((resolve) => setTimeout(resolve, 100))
  }

  throw lastError || new Error(`Timed out waiting for ${url}`)
}

export async function ensureRealApiReady(apiBaseUrl) {
  const checks = [
    { hint: 'Start the backend before running npm run test:e2e:real.', label: 'process health', path: '/api/health' },
    { hint: 'Start the backend database before running npm run test:e2e:real.', label: 'database health', path: '/api/health/db' },
  ]

  for (const check of checks) {
    const healthUrl = new URL(check.path, apiBaseUrl).toString()

    try {
      const response = await fetch(healthUrl)

      if (response.ok) {
        continue
      }

      throw new Error(`GET ${healthUrl} returned ${response.status}`)
    } catch (error) {
      throw new Error(
        `Real API ${check.label} check failed at ${healthUrl}. ${check.hint}\n${error.message}`,
      )
    }
  }
}

export async function evaluate(client, expression) {
  const result = await client.send('Runtime.evaluate', {
    awaitPromise: true,
    expression,
    returnByValue: true,
    userGesture: true,
  })

  if (result.exceptionDetails) {
    throw new Error(result.exceptionDetails.text || 'Runtime evaluation failed')
  }

  return result.result.value
}

export async function waitFor(client, expression, label, timeoutMs = 15000) {
  const deadline = Date.now() + timeoutMs

  while (Date.now() < deadline) {
    if (await evaluate(client, expression)) {
      return
    }

    await new Promise((resolve) => setTimeout(resolve, 100))
  }

  throw new Error(`Timed out waiting for ${label}`)
}

export async function waitForOptional(client, expression, timeoutMs = 1500) {
  try {
    await waitFor(client, expression, 'optional condition', timeoutMs)
    return true
  } catch {
    return false
  }
}

export function includesText(text) {
  return `document.body.textContent.includes(${JSON.stringify(text)})`
}

export function visiblePopoverIncludesText(text) {
  return `(() => {
    ${visibleElementScript}
    const candidates = [...document.querySelectorAll('.ant-popover, .ant-popover-inner, [role="tooltip"], [role="dialog"]')]
    return candidates.some((element) => isVisible(element) && element.textContent.includes(${JSON.stringify(text)}))
  })()`
}

export function headerIncludesText(text) {
  return `document.querySelector('.app-header')?.textContent.includes(${JSON.stringify(text)})`
}

export function hasPlaceholder(placeholder) {
  return `(() => {
    ${visibleElementScript}
    return [...document.querySelectorAll('input')].some((element) =>
    isVisible(element) && (element.placeholder || '').includes(${JSON.stringify(placeholder)})
  )
  })()`
}

export function enabledSelector(selector) {
  return `(() => {
    ${visibleElementScript}
    const target = document.querySelector(${JSON.stringify(selector)})
    return Boolean(target && isVisible(target) && !target.disabled)
  })()`
}

export function clickableText(text) {
  return `(() => {
    ${visibleElementScript}
    return [...document.querySelectorAll('button, [role="button"]')].some((element) =>
      isVisible(element) && element.textContent.includes(${JSON.stringify(text)}) && !element.disabled
    )
  })()`
}

export function visibleTextSelector(selector, text) {
  return `(() => {
    ${visibleElementScript}
    const target = document.querySelector(${JSON.stringify(selector)})
    return Boolean(target && isVisible(target) && target.textContent.includes(${JSON.stringify(text)}))
  })()`
}

export const visibleElementScript = `
  function isVisible(element) {
    return Boolean(element.offsetWidth || element.offsetHeight || element.getClientRects().length)
  }
`

let navigationCounter = 0

export async function navigateApp(client, appUrl) {
  const targetUrl = new URL(appUrl)
  targetUrl.searchParams.set('e2e_nav', String(++navigationCounter))
  await client.send('Page.navigate', { url: targetUrl.toString() })
}

export async function clickByText(client, text) {
  const clicked = await evaluate(
    client,
    `(() => {
      ${visibleElementScript}
      const elements = [...document.querySelectorAll('button, [role="button"]')]
      const target = elements.find((element) =>
        isVisible(element) && element.textContent.includes(${JSON.stringify(text)}) && !element.disabled
      )
      if (!target) return false
      target.click()
      return true
    })()`,
  )

  if (!clicked) {
    const candidates = await evaluate(
      client,
      `(() => {
        ${visibleElementScript}
        return [...document.querySelectorAll('button, [role="button"]')].map((element) => ({
        disabled: Boolean(element.disabled),
        visible: isVisible(element),
        text: element.textContent.trim(),
      }))
      })()`,
    )
    throw new Error(`Could not click ${text}. Candidates: ${JSON.stringify(candidates)}`)
  }
}

export async function clickSegmentedOption(client, text) {
  const clicked = await evaluate(
    client,
    `(() => {
      ${visibleElementScript}
      const target = [...document.querySelectorAll('.ant-segmented-item')].find((element) =>
        isVisible(element) && element.textContent.includes(${JSON.stringify(text)})
      )
      if (!target) return false
      target.click()
      return true
    })()`,
  )

  if (!clicked) {
    throw new Error(`Could not click segmented option ${text}`)
  }
}

export async function selectAntOption(client, selector, popupSelector, text) {
  await pointerClickSelector(client, selector)
  await waitFor(
    client,
    `(() => {
      ${visibleElementScript}
      return [...document.querySelectorAll(${JSON.stringify(`${popupSelector} .ant-select-item-option`)})].some((element) =>
        isVisible(element) && element.textContent.includes(${JSON.stringify(text)})
      )
    })()`,
    `select option ${text}`,
  )

  const clicked = await evaluate(
    client,
    `(() => {
      ${visibleElementScript}
      const target = [...document.querySelectorAll(${JSON.stringify(`${popupSelector} .ant-select-item-option`)})].find((element) =>
        isVisible(element) && element.textContent.includes(${JSON.stringify(text)})
      )
      if (!target) return false
      target.click()
      return true
    })()`,
  )

  if (!clicked) {
    throw new Error(`Could not select ${text}`)
  }
}

export async function clickSideMenuItem(client, text) {
  const clicked = await evaluate(
    client,
    `(() => {
      ${visibleElementScript}
      const target = [...document.querySelectorAll('.side-menu .ant-menu-item, [role="menuitem"]')].find((element) =>
        isVisible(element) && element.textContent.includes(${JSON.stringify(text)})
      )
      if (!target) return false
      target.click()
      return true
    })()`,
  )

  if (!clicked) {
    throw new Error(`Could not click side menu item ${text}`)
  }
}

export async function clickTableRowContaining(client, selector, text) {
  const clicked = await evaluate(
    client,
    `(() => {
      ${visibleElementScript}
      const target = [...document.querySelectorAll(${JSON.stringify(`${selector} tbody tr`)})].find((element) =>
        isVisible(element) && element.textContent.includes(${JSON.stringify(text)})
      )
      if (!target) return false
      target.click()
      return true
    })()`,
  )

  if (!clicked) {
    throw new Error(`Could not click table row containing ${text}`)
  }
}

function activeDateChip(text) {
  return `(() => {
    ${visibleElementScript}
    return [...document.querySelectorAll('.date-chip')].some((element) =>
      isVisible(element) &&
      element.classList.contains('active') &&
      element.textContent.includes(${JSON.stringify(text)})
    )
  })()`
}

export async function clickDateChip(client, text) {
  const clicked = await evaluate(
    client,
    `(() => {
      ${visibleElementScript}
      const target = [...document.querySelectorAll('.date-chip')].find((element) =>
        isVisible(element) && element.textContent.includes(${JSON.stringify(text)})
      )
      if (!target) return false
      target.click()
      return true
    })()`,
  )

  if (!clicked) {
    throw new Error(`Could not click date chip ${text}`)
  }

  await waitFor(client, activeDateChip(text), `active date chip ${text}`)
}

export async function clickSelector(client, selector) {
  const clicked = await evaluate(
    client,
    `(() => {
      ${visibleElementScript}
      const target = document.querySelector(${JSON.stringify(selector)})
      if (!target || target.disabled || !isVisible(target)) return false
      target.click()
      return true
    })()`,
  )

  if (!clicked) {
    throw new Error(`Could not click ${selector}`)
  }
}

export async function pointerClickSelector(client, selector) {
  const targetCenter = await evaluate(
    client,
    `(() => {
      ${visibleElementScript}
      const target = document.querySelector(${JSON.stringify(selector)})
      if (!target || target.disabled || !isVisible(target)) return null
      target.scrollIntoView({ block: 'center', inline: 'center' })
      const rect = target.getBoundingClientRect()
      return {
        x: rect.left + rect.width / 2,
        y: rect.top + rect.height / 2,
      }
    })()`,
  )

  if (!targetCenter) {
    throw new Error(`Could not pointer-click ${selector}`)
  }

  await client.send('Input.dispatchMouseEvent', {
    button: 'none',
    type: 'mouseMoved',
    x: targetCenter.x,
    y: targetCenter.y,
  })
  await client.send('Input.dispatchMouseEvent', {
    button: 'left',
    clickCount: 1,
    type: 'mousePressed',
    x: targetCenter.x,
    y: targetCenter.y,
  })
  await client.send('Input.dispatchMouseEvent', {
    button: 'left',
    clickCount: 1,
    type: 'mouseReleased',
    x: targetCenter.x,
    y: targetCenter.y,
  })
}

export async function openAuthSessionDiagnostic(client, label) {
  const hasDiagnosticDetails = visiblePopoverIncludesText('错误码：SESSION_LOOKUP_FAILED')
  const waitForDiagnosticDetails = async () => {
    return await waitForOptional(client, hasDiagnosticDetails, 3500)
  }

  const openFromStatusStrip = async () => {
    const clicked = await evaluate(
      client,
      `(() => {
        ${visibleElementScript}
        const target = [...document.querySelectorAll('.status-diagnostic-badge.is-error')].find((element) =>
          isVisible(element) && element.textContent.includes('会话异常')
        )
        if (!target) return false
        target.focus()
        target.click()
        return true
      })()`,
    )

    return clicked && await waitForDiagnosticDetails()
  }

  for (let attempt = 0; attempt < 3; attempt += 1) {
    if (await waitForDiagnosticDetails()) {
      return
    }

    await pointerClickSelector(client, '.auth-session-error-trigger')

    if (await waitForDiagnosticDetails()) {
      return
    }

    if (await openFromStatusStrip()) {
      return
    }
  }

  const bodyText = await evaluate(client, 'document.body.textContent.slice(0, 1000)')
  throw new Error(`Could not open ${label} diagnostic popover. Body text: ${JSON.stringify(bodyText)}`)
}

export async function fillPlaceholder(client, placeholder, value) {
  const filled = await evaluate(
    client,
    `(() => {
      ${visibleElementScript}
      const input = [...document.querySelectorAll('input, textarea')].find((element) =>
        isVisible(element) && (element.placeholder || '').includes(${JSON.stringify(placeholder)})
      )
      if (!input) return false
      const prototype = input instanceof HTMLTextAreaElement ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype
      const setter = Object.getOwnPropertyDescriptor(prototype, 'value').set
      setter.call(input, ${JSON.stringify(value)})
      input.dispatchEvent(new Event('input', { bubbles: true }))
      input.dispatchEvent(new Event('change', { bubbles: true }))
      return true
    })()`,
  )

  if (!filled) {
    throw new Error(`Could not fill input ${placeholder}`)
  }
}

export async function fillPlaceholderIn(client, rootSelector, placeholder, value) {
  const filled = await evaluate(
    client,
    `(() => {
      ${visibleElementScript}
      const root = document.querySelector(${JSON.stringify(rootSelector)})
      if (!root) return false
      const input = [...root.querySelectorAll('input, textarea')].find((element) =>
        isVisible(element) && (element.placeholder || '').includes(${JSON.stringify(placeholder)})
      )
      if (!input) return false
      const prototype = input instanceof HTMLTextAreaElement ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype
      const setter = Object.getOwnPropertyDescriptor(prototype, 'value').set
      setter.call(input, ${JSON.stringify(value)})
      input.dispatchEvent(new Event('input', { bubbles: true }))
      input.dispatchEvent(new Event('change', { bubbles: true }))
      return true
    })()`,
  )

  if (!filled) {
    throw new Error(`Could not fill input ${placeholder} in ${rootSelector}`)
  }
}

export async function fillSelector(client, selector, value) {
  const filled = await evaluate(
    client,
    `(() => {
      ${visibleElementScript}
      const input = document.querySelector(${JSON.stringify(selector)})
      if (!input || !isVisible(input)) return false
      const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set
      setter.call(input, ${JSON.stringify(value)})
      input.dispatchEvent(new Event('input', { bubbles: true }))
      input.dispatchEvent(new Event('change', { bubbles: true }))
      return true
    })()`,
  )

  if (!filled) {
    throw new Error(`Could not fill selector ${selector}`)
  }
}
