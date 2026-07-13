import { spawn } from 'node:child_process'
import { access, mkdtemp, readFile } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { createServer as createViteServer } from 'vite'
import {
  CdpClient,
  ensureRealApiReady,
  navigateApp,
  waitForJson,
} from './e2e-browser-utils.mjs'
import { createMockApi } from './e2e-mock-api.mjs'
import {
  assert,
  closeServer,
  listen,
  removeDirectory,
  waitForProcessExit,
} from './e2e-runtime-utils.mjs'

async function waitForChromeDebuggingPort(userDataDir, timeoutMs = 5000) {
  const deadline = Date.now() + timeoutMs

  while (Date.now() < deadline) {
    try {
      const [port] = (await readFile(join(userDataDir, 'DevToolsActivePort'), 'utf8')).trim().split('\n')
      const debuggingPort = Number(port)
      if (Number.isInteger(debuggingPort) && debuggingPort > 0 && debuggingPort <= 65535) {
        return debuggingPort
      }
    } catch {
      await new Promise((resolve) => setTimeout(resolve, 100))
    }
  }

  throw new Error('Chrome did not publish its debugging port')
}

export async function withE2eHarness({
  chromePath,
  password,
  phone,
  realApiBaseUrl,
  username,
  viewport,
  visitorName,
}, runScenario) {
  if (realApiBaseUrl) {
    await ensureRealApiReady(realApiBaseUrl)
  }

  await access(chromePath).catch(() => {
    throw new Error(`Chrome executable not found at ${chromePath}. Set CHROME_PATH to override.`)
  })

  const mock = realApiBaseUrl ? null : createMockApi({ password, phone, username, visitorName })
  let chrome
  let chromeUserDataDir
  let client
  let vite

  try {
    const apiBaseUrl = realApiBaseUrl || await (async () => {
      const mockAddress = await listen(mock.server)
      return `http://127.0.0.1:${mockAddress.port}`
    })()
    process.env.VITE_API_BASE_URL = ''

    vite = await createViteServer({
      logLevel: 'error',
      server: {
        host: '127.0.0.1',
        port: 0,
        proxy: {
          '/api': {
            changeOrigin: true,
            target: apiBaseUrl,
          },
        },
      },
    })
    await vite.listen()
    const appUrl = vite.resolvedUrls.local[0]

    if (mock) {
      mock.state.allowedOrigin = new URL(appUrl).origin
    }

    chromeUserDataDir = await mkdtemp(join(tmpdir(), 'scenic-e2e-chrome-'))
    chrome = spawn(chromePath, [
      '--headless=new',
      '--remote-debugging-port=0',
      `--user-data-dir=${chromeUserDataDir}`,
      '--disable-gpu',
      '--no-first-run',
      '--no-default-browser-check',
    ], { stdio: 'ignore' })

    const debuggingPort = await waitForChromeDebuggingPort(chromeUserDataDir)
    await waitForJson(`http://127.0.0.1:${debuggingPort}/json/version`)
    const targetResponse = await fetch(`http://127.0.0.1:${debuggingPort}/json/new?${encodeURIComponent(appUrl)}`, {
      method: 'PUT',
    })
    assert(targetResponse.ok, 'Chrome did not create a new debugging target')
    const target = await targetResponse.json()

    client = new CdpClient(target.webSocketDebuggerUrl)
    await client.connect()
    await client.send('Runtime.enable')
    await client.send('Page.enable')
    await client.send('Emulation.setDeviceMetricsOverride', {
      deviceScaleFactor: 1,
      height: viewport.height,
      mobile: true,
      width: viewport.width,
    })
    await navigateApp(client, appUrl)

    return await runScenario({ apiBaseUrl, appUrl, client, mock })
  } finally {
    client?.close()
    if (chrome) {
      chrome.kill('SIGTERM')
      await waitForProcessExit(chrome)
    }
    await vite?.close()
    if (mock) {
      await closeServer(mock.server)
    }
    if (chromeUserDataDir) {
      await removeDirectory(chromeUserDataDir)
    }
  }
}
