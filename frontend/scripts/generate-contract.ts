// Writes the type check that ties each generated Zod schema to its generated TypeScript type.
import { readFileSync, writeFileSync } from "node:fs"

const client = new URL("../src/client/", import.meta.url)

// Returns the first capture group of every match in a generated file.
const exported = (file: string, pattern: RegExp) =>
  new Set(
    [...readFileSync(new URL(file, client), "utf8").matchAll(pattern)].map(
      (match) => match[1],
    ),
  )

const schemas = exported("zod.gen.ts", /^export const z(\w+) =/gm)
const types = exported("types.gen.ts", /^export type (\w+) =/gm)
const shared = [...schemas].filter((name) => types.has(name)).sort()

const checks = shared
  .map((name) => `  Expect<Matches<typeof Schemas.z${name}, Types.${name}>>,`)
  .join("\n")

writeFileSync(
  new URL("contract.gen.ts", client),
  `import type { z } from "zod"
import type * as Types from "./types.gen"
import type * as Schemas from "./zod.gen"

type Same<A, B> = [A] extends [B] ? ([B] extends [A] ? true : false) : false
type Expect<T extends true> = T
type Matches<S extends z.ZodType, T> = Same<z.input<S>, T>

export type ContractTypes = [
${checks}
]
`,
)
