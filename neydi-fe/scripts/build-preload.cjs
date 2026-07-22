const Module = require('node:module')
const path = require('node:path')

const root = path.join(__dirname, '..')
const localPackages = [
  'baseline-browser-mapping',
  'browserslist',
  'caniuse-lite'
]

const resolveLocal = (request) => {
  if (!localPackages.includes(request)) {
    return null
  }

  try {
    return require.resolve(request, { paths: [root] })
  } catch {
    return null
  }
}

const originalResolveFilename = Module._resolveFilename

Module._resolveFilename = function (request, parent, isMain, options) {
  const local = resolveLocal(request)
  if (local) {
    return local
  }

  return originalResolveFilename.call(this, request, parent, isMain, options)
}
