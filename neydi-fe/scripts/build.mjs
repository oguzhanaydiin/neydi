import { spawnSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

const root = join(dirname(fileURLToPath(import.meta.url)), '..')

process.env.BROWSERSLIST_IGNORE_OLD_DATA = 'true'
process.env.BASELINE_BROWSER_MAPPING_IGNORE_OLD_DATA = 'true'

const result = spawnSync(
  process.execPath,
  [
    '--require',
    join(root, 'scripts/build-preload.cjs'),
    '--disable-warning=DEP0155',
    join(root, 'node_modules/nuxt/bin/nuxt.mjs'),
    'build'
  ],
  {
    cwd: root,
    stdio: 'inherit',
    env: process.env
  }
)

process.exit(result.status ?? 1)
