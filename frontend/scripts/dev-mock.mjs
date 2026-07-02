import { createServer as createViteServer } from 'vite'
import { createMockApi } from './e2e-mock-api.mjs'
import { closeServer, listen } from './e2e-runtime-utils.mjs'

const host = process.env.DEV_MOCK_HOST || '127.0.0.1'
const port = Number(process.env.DEV_MOCK_PORT || 5173)
const phone = process.env.DEV_MOCK_PHONE || '19900000001'
const visitorName = process.env.DEV_MOCK_VISITOR_NAME || '测试游客'

process.env.VITE_API_BASE_URL = ''
process.env.VITE_ADMIN_AUTH_MODE = 'mock'
process.env.VITE_ADMIN_ORDERS_MODE = 'mock'
process.env.VITE_ADMIN_REPORTS_MODE = 'mock'
process.env.VITE_ADMIN_REFUND_LOGS_MODE = 'mock'
process.env.VITE_ADMIN_CHECK_IN_LOGS_MODE = 'mock'
process.env.VITE_ADMIN_CHECK_IN_FAILURE_LOGS_MODE = 'mock'
process.env.VITE_ADMIN_EXPORT_JOBS_MODE = 'mock'

const mock = createMockApi({ phone, visitorName })
const mockAddress = await listen(mock.server, host)
const apiBaseUrl = `http://${host}:${mockAddress.port}`

const vite = await createViteServer({
  server: {
    host,
    port,
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
mock.state.allowedOrigin = new URL(appUrl).origin

console.log(`Mock API: ${apiBaseUrl}`)
console.log(`Frontend: ${appUrl}`)
console.log('Press Ctrl+C to stop.')

let shuttingDown = false

async function shutdown() {
  if (shuttingDown) {
    return
  }

  shuttingDown = true
  await vite.close()
  await closeServer(mock.server)
}

process.on('SIGINT', async () => {
  await shutdown()
  process.exit(0)
})

process.on('SIGTERM', async () => {
  await shutdown()
  process.exit(0)
})
