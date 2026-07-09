import { readFile } from 'node:fs/promises'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import vm from 'node:vm'
import ts from 'typescript'

const rootDir = dirname(dirname(fileURLToPath(import.meta.url)))
const sourceDir = join(rootDir, 'src')

export function assert(condition, message) {
  if (!condition) {
    throw new Error(message)
  }
}

export function assertThrows(callback, code, message) {
  try {
    callback()
  } catch (error) {
    assert(error?.code === code, `${message}. actual=${error?.code ?? error}`)
    return
  }

  throw new Error(`${message}. expected throw ${code}`)
}

export async function parseSource(relativePath) {
  const path = join(sourceDir, relativePath)
  const text = await readFile(path, 'utf8')

  return {
    path,
    sourceFile: ts.createSourceFile(path, text, ts.ScriptTarget.Latest, true, ts.ScriptKind.TS),
    text,
  }
}

export function visit(node, callback) {
  callback(node)
  ts.forEachChild(node, (child) => visit(child, callback))
}

export function findTypeAlias(sourceFile, name) {
  let match

  visit(sourceFile, (node) => {
    if (ts.isTypeAliasDeclaration(node) && node.name.text === name) {
      match = node
    }
  })

  assert(match, `Missing type alias ${name}`)
  return match
}

export function findFunction(sourceFile, name) {
  let match

  visit(sourceFile, (node) => {
    if (ts.isFunctionDeclaration(node) && node.name?.text === name) {
      match = node
    }
  })

  assert(match, `Missing function ${name}`)
  return match
}

export function findRuntimeDeclaration(sourceFile, name) {
  let match

  visit(sourceFile, (node) => {
    if (!match && ts.isFunctionDeclaration(node) && node.name?.text === name) {
      match = node
    }
  })

  visit(sourceFile, (node) => {
    if (match || !ts.isVariableStatement(node)) {
      return
    }

    const hasDeclaration = node.declarationList.declarations.some((declaration) =>
      ts.isIdentifier(declaration.name) && declaration.name.text === name,
    )

    if (hasDeclaration) {
      match = node
    }
  })

  assert(match, `Missing runtime declaration ${name}`)
  return match.getText(sourceFile).replace(/^export /, '')
}

export function propertyContract(typeAlias) {
  const sourceFile = typeAlias.getSourceFile()
  const typeNode = typeAlias.type
  assert(ts.isTypeLiteralNode(typeNode), `${typeAlias.name.text} must be a type literal`)

  return Object.fromEntries(
    typeNode.members
      .filter(ts.isPropertySignature)
      .map((member) => [
        member.name.getText(sourceFile),
        {
          optional: Boolean(member.questionToken),
          type: member.type?.getText(sourceFile) ?? 'unknown',
        },
      ]),
  )
}

export function assertExactPropertyContract(sourceFile, typeName, expected) {
  const actual = propertyContract(findTypeAlias(sourceFile, typeName))

  assert(
    JSON.stringify(actual) === JSON.stringify(expected),
    `${typeName} contract mismatch. actual=${JSON.stringify(actual)} expected=${JSON.stringify(expected)}`,
  )
}

export function assertTypeAliasText(sourceFile, typeName, expected) {
  const actual = findTypeAlias(sourceFile, typeName).type.getText(sourceFile)

  assert(actual === expected, `${typeName} alias mismatch. actual=${actual} expected=${expected}`)
}

export function stringLiteralUnion(typeAlias) {
  const typeNode = typeAlias.type
  assert(ts.isUnionTypeNode(typeNode), `${typeAlias.name.text} must be a string literal union`)

  return typeNode.types.map((node) => {
    assert(ts.isLiteralTypeNode(node) && ts.isStringLiteral(node.literal), `${typeAlias.name.text} must only use string literals`)
    return node.literal.text
  })
}

export function assertStringLiteralUnion(sourceFile, typeName, expected) {
  const actual = stringLiteralUnion(findTypeAlias(sourceFile, typeName)).sort()
  const sortedExpected = [...expected].sort()

  assert(
    JSON.stringify(actual) === JSON.stringify(sortedExpected),
    `${typeName} union mismatch. actual=${actual.join(',')} expected=${sortedExpected.join(',')}`,
  )
}

export function objectPropertyValueText(objectLiteral, key, sourceFile) {
  if (!objectLiteral) {
    return undefined
  }

  const property = objectLiteral.properties.find((candidate) => {
    if (ts.isPropertyAssignment(candidate)) {
      return candidate.name.getText(sourceFile) === key
    }

    if (ts.isShorthandPropertyAssignment(candidate)) {
      return candidate.name.text === key
    }

    return false
  })

  if (property && ts.isPropertyAssignment(property)) {
    return property.initializer.getText(sourceFile)
  }

  if (property && ts.isShorthandPropertyAssignment(property)) {
    return property.name.text
  }

  return undefined
}

export function endpointPathText(argument, sourceFile) {
  if (ts.isStringLiteral(argument) || ts.isNoSubstitutionTemplateLiteral(argument)) {
    return argument.text
  }

  if (ts.isTemplateExpression(argument)) {
    return argument.head.text + argument.templateSpans.map((span) => '${}' + span.literal.text).join('')
  }

  return argument.getText(sourceFile)
}

export function collectApiRequests(sourceFile) {
  const requests = []

  visit(sourceFile, (node) => {
    if (!ts.isCallExpression(node) || node.expression.getText(sourceFile) !== 'apiRequest') {
      return
    }

    const [pathArg, optionsArg] = node.arguments
    assert(pathArg, 'apiRequest call must include a path')

    const options = optionsArg && ts.isObjectLiteralExpression(optionsArg) ? optionsArg : undefined
    const methodText = options ? objectPropertyValueText(options, 'method', sourceFile) : undefined
    const idempotencyKeyText = options ? objectPropertyValueText(options, 'idempotencyKey', sourceFile) : undefined

    requests.push({
      hasIdempotencyKey: Boolean(idempotencyKeyText),
      method: methodText ? methodText.replaceAll(/['"]/g, '') : 'GET',
      path: endpointPathText(pathArg, sourceFile),
      skipCsrf: objectPropertyValueText(options, 'skipCsrf', sourceFile) === 'true',
      text: node.getText(sourceFile),
      typeArgument: node.typeArguments?.[0]?.getText(sourceFile),
    })
  })

  return requests
}

export function assertEndpoint(requests, expected) {
  const match = requests.find((request) => request.path === expected.path && request.method === expected.method)

  assert(match, `Missing endpoint ${expected.method} ${expected.path}`)

  if (expected.idempotencyKey) {
    assert(match.hasIdempotencyKey, `${expected.method} ${expected.path} must pass Idempotency-Key`)
  }

  if (expected.typeArgument) {
    assert(
      match.typeArgument === expected.typeArgument,
      `${expected.method} ${expected.path} type mismatch. actual=${match.typeArgument} expected=${expected.typeArgument}`,
    )
  }

  if (expected.skipCsrf) {
    assert(match.skipCsrf, `${expected.method} ${expected.path} must skip CSRF bootstrap recursion`)
  }

  if (expected.method !== 'GET' && !expected.skipCsrf) {
    assert(!match.skipCsrf, `${expected.method} ${expected.path} must stay CSRF-protected`)
  }

  return match
}

export function assertContains(text, needle, label) {
  assert(text.includes(needle), `${label} must contain ${needle}`)
}

export function assertNotContains(text, needle, label) {
  assert(!text.includes(needle), `${label} must not contain ${needle}`)
}

export function readStoreZipEntryText(bytes, expectedName) {
  const decoder = new TextDecoder()
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength)
  let offset = 0

  while (offset + 30 <= bytes.length) {
    const signature = view.getUint32(offset, true)

    if (signature === 0x02014B50 || signature === 0x06054B50) {
      break
    }

    assert(signature === 0x04034B50, `Unexpected ZIP local header at ${offset}`)
    const compressionMethod = view.getUint16(offset + 8, true)
    const compressedSize = view.getUint32(offset + 18, true)
    const fileNameLength = view.getUint16(offset + 26, true)
    const extraLength = view.getUint16(offset + 28, true)
    const fileNameStart = offset + 30
    const contentStart = fileNameStart + fileNameLength + extraLength
    const contentEnd = contentStart + compressedSize
    const fileName = decoder.decode(bytes.slice(fileNameStart, fileNameStart + fileNameLength))

    if (fileName === expectedName) {
      assert(compressionMethod === 0, `${expectedName} must use store compression in mock XLSX`)
      return decoder.decode(bytes.slice(contentStart, contentEnd))
    }

    offset = contentEnd
  }

  throw new Error(`Missing ZIP entry ${expectedName}`)
}

export function loadRuntimeFunctions(sourceFile, functionNames) {
  const sourceFiles = Array.isArray(sourceFile) ? sourceFile : [sourceFile]
  const snippets = functionNames.map((name) => {
    for (const candidate of sourceFiles) {
      try {
        return findRuntimeDeclaration(candidate, name)
      } catch {
        // Try the next source file in the runtime bundle.
      }
    }

    throw new Error(`Missing runtime declaration ${name}`)
  })
  const source = [
    ...snippets,
    `globalThis.__apiContractRuntime = { ${functionNames.join(', ')}, __checkInAuditAppends: globalThis.__checkInAuditAppends }`,
  ].join('\n')
  const runtimeGlobalThis = { __checkInAuditAppends: [] }
  const { outputText } = ts.transpileModule(source, {
    compilerOptions: {
      module: ts.ModuleKind.ESNext,
      target: ts.ScriptTarget.ES2022,
    },
  })
  const context = {
    ApiError: class ApiError extends Error {
      constructor(error) {
        super(error.message)
        this.code = error.code
        this.requestId = error.request_id
      }
    },
    addMockAdminRefundAuditLog: () => {},
    addMockAdminCheckInAuditLog: (log) => runtimeGlobalThis.__checkInAuditAppends.push(log),
    Blob,
    TextEncoder,
    URLSearchParams,
    globalThis: runtimeGlobalThis,
  }

  vm.runInNewContext(outputText, context)
  return context.globalThis.__apiContractRuntime
}

export function findCallExpression(node, predicate) {
  let match

  visit(node, (candidate) => {
    if (!match && ts.isCallExpression(candidate) && predicate(candidate)) {
      match = candidate
    }
  })

  return match
}

export function findIfStatement(node, expressionText) {
  let match

  visit(node, (candidate) => {
    if (!match && ts.isIfStatement(candidate) && candidate.expression.getText(candidate.getSourceFile()) === expressionText) {
      match = candidate
    }
  })

  return match
}

export function assertFetchOptions(apiRequestFunction) {
  const sourceFile = apiRequestFunction.getSourceFile()
  const fetchCall = findCallExpression(
    apiRequestFunction,
    (call) => call.expression.getText(sourceFile) === 'fetch' && call.arguments[0]?.getText(sourceFile) === 'buildUrl(path)',
  )

  assert(fetchCall, 'apiRequest must call fetch(buildUrl(path), options)')
  const options = fetchCall.arguments[1]
  assert(options && ts.isObjectLiteralExpression(options), 'apiRequest fetch options must be an object literal')
  assert(objectPropertyValueText(options, 'credentials', sourceFile) === "'include'", 'apiRequest fetch must include session cookies')
  assert(objectPropertyValueText(options, 'headers', sourceFile) === 'headers', 'apiRequest fetch must pass prepared headers')
  assert(objectPropertyValueText(options, 'method', sourceFile) === 'method', 'apiRequest fetch must pass selected method')
  assert(objectPropertyValueText(options, 'body', sourceFile)?.includes('JSON.stringify(options.body)'), 'apiRequest fetch must serialize request body')
}

export function assertHeadersSetInBranch(functionNode, expressionText, headerNameText, valueText, label) {
  const sourceFile = functionNode.getSourceFile()
  const branch = findIfStatement(functionNode, expressionText)

  assert(branch, `${label} branch is missing`)
  const headerCall = findCallExpression(
    branch.thenStatement,
    (call) =>
      call.expression.getText(sourceFile) === 'headers.set' &&
      call.arguments[0]?.getText(sourceFile) === headerNameText &&
      call.arguments[1]?.getText(sourceFile) === valueText,
  )

  assert(headerCall, `${label} branch must set ${headerNameText}`)
}

export function assertTypeExportBarrel(source, maxLines) {
  const lineCount = source.text.trim().split(/\r?\n/).length
  assert(lineCount <= maxLines, `shared API type barrel must stay small. actual lines=${lineCount} limit=${maxLines}`)

  for (const statement of source.sourceFile.statements) {
    assert(ts.isExportDeclaration(statement), 'shared API type barrel must only contain export declarations')
    assert(statement.isTypeOnly, 'shared API type barrel must only contain export type declarations')
    assert(statement.moduleSpecifier, 'shared API type barrel exports must point at domain modules')
    assert(
      statement.moduleSpecifier.getText(source.sourceFile).startsWith("'./types/"),
      `shared API type barrel export must target ./types/*: ${statement.getText(source.sourceFile)}`,
    )
  }
}
