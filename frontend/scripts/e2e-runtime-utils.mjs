import { rm } from 'node:fs/promises'
import { createServer as createHttpServer } from 'node:http'

export function assert(condition, message) {
  if (!condition) {
    throw new Error(message)
  }
}

export function assertDeepEqual(actual, expected, label) {
  const actualJson = JSON.stringify(actual)
  const expectedJson = JSON.stringify(expected)

  if (actualJson !== expectedJson) {
    throw new Error(`${label} mismatch\nactual:   ${actualJson}\nexpected: ${expectedJson}`)
  }
}

export function listen(server, host = '127.0.0.1') {
  return new Promise((resolve, reject) => {
    server.once('error', reject)
    server.listen(0, host, () => {
      server.off('error', reject)
      resolve(server.address())
    })
  })
}

export function closeServer(server) {
  return new Promise((resolve, reject) => {
    server.close((error) => {
      if (error?.code === 'ERR_SERVER_NOT_RUNNING') {
        resolve()
        return
      }

      if (error) {
        reject(error)
        return
      }

      resolve()
    })
  })
}

export async function findFreePort() {
  const server = createHttpServer()
  const address = await listen(server)
  await closeServer(server)
  return address.port
}

export function waitForProcessExit(child, timeoutMs = 2000) {
  return new Promise((resolve) => {
    if (child.exitCode !== null || child.signalCode !== null) {
      resolve()
      return
    }

    const timeout = setTimeout(resolve, timeoutMs)
    child.once('exit', () => {
      clearTimeout(timeout)
      resolve()
    })
  })
}

export async function removeDirectory(path) {
  let lastError

  for (let attempt = 0; attempt < 5; attempt += 1) {
    try {
      await rm(path, { force: true, recursive: true })
      return
    } catch (error) {
      lastError = error
      await new Promise((resolve) => setTimeout(resolve, 100))
    }
  }

  if (lastError?.code !== 'ENOENT') {
    throw lastError
  }
}
