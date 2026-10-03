---
name: zod-docs-first
description: Requires consulting the official Zod 4 docs, and checking whether the contract already carries the rule, before writing or changing any Zod schema. Use whenever the task touches Zod, including z.object schemas, refinements, transforms, string formats, error messages and error maps, zodResolver form validation, z.infer types, the generated frontend/src/client/zod.gen.ts, the SDK request validators, or the @hey-api/openapi-ts zod plugin settings. Also use when adding or upgrading zod, or when a Zod API looks unfamiliar or like Zod 3, because Zod 4 deprecated or removed several APIs (message, string-format methods, extend on refined schemas) and memory of older versions is often wrong. Make sure to use this skill even if the user only says "validation", "schema" or "form rules".
---

# Zod docs first

Zod 4 changed its API (`error` replaces `message`, string formats are top-level functions such as `z.email()`, `.extend()` throws on a schema that already has refinements). Memory of Zod 3 is often wrong, so read the current docs before writing Zod-specific code. In this repo there is a second question to ask first: most rules should not be written in Zod at all.

## When this applies

Read the docs, and check the contract, before you write or change:

- A schema, refinement, transform, default or coercion
- A string format, number rule or enum
- An error message, a custom error map or the way errors are shown
- A form's resolver or the types inferred from its schema
- The generated `zod.gen.ts`, the generator config, or the SDK's request validation
- The `zod` dependency version

Mechanical edits that touch no Zod API (renaming a field, fixing copy) don't need a lookup.

## How Zod is used in this repo

- **The contract owns the field rules.** Backend models in `backend/app/models.py` generate `backend/openapi.json`, which generates `frontend/src/client/zod.gen.ts` (`bash scripts/generate-client.sh`; never edit the generated files). A length, format or required rule is changed in the backend and regenerated, not retyped in a form.
- **Forms compose generated schemas.** A form imports a generated export (for example `zUserRegister`) and layers only rules the contract cannot express on top, such as confirm-password. Optional wrappers on generated fields are removed with `.unwrap()`.
- **Messages come from one place.** `lib/form-errors.ts` words the browser's messages and is passed to each resolver as `zodResolver(schema, { error: formError })`.
- **The SDK validates every request.** The generator runs with `validator.request: "zod"`, and `lib/api.ts` turns a failed parse into an `ApiError` with status 422. Responses are not validated.
- **Types come from the schema.** Form types are `z.infer<typeof schema>`; API types come from the generated `types.gen.ts`. Don't declare a third copy by hand.

If a rule is missing from the generated schema, the right fix is usually in the backend model, not in the frontend.

## Sources, in order of preference

These are starting points. Follow links and search until you can ground the decision in the docs.

1. **Installed package**: `frontend/node_modules/zod` (check `package.json` for the exact version). It ships types and locales, no docs, so use it for exact signatures.
2. **Docs index**: https://zod.dev/llms.txt lists every page and the anchors inside the long API page.
3. **Full corpus**: https://zod.dev/llms-full.txt is about 290 KB. Never read it end to end; download it to a file and `rg` it for the API you need.
4. **Pages**:
   - https://zod.dev (docs home)
   - https://zod.dev/api (every schema type, method and format)
   - Pages named in the index: error customization, error formatting, basics, the migration guide from Zod 3, codecs, JSON Schema, Zod Mini and Core, library authors, metadata

There is no `.md` variant of the pages. Use the migration guide whenever code looks like Zod 3.

## Workflow

1. **Ask whether the contract already has the rule.** If it does, use the generated export. If it should, change the backend and regenerate.
2. **Name the Zod API** you need in one line, then find it in the API page or with `rg` over the full corpus.
3. **Write it the Zod 4 way**: top-level formats (`z.email()`, not `z.string().email()`), `error` not `message`, `.safeExtend()` for a schema that already has refinements, `z.infer`, `z.input` or `z.output` for types, and `safeParse` where you handle the failure yourself.
4. **Verify**: `bunx tsc --noEmit`, `bun run test:unit`, and the Playwright spec for the form when a form changed.
5. **Cite the pages you used** so the user can check them. If the docs and your memory disagree, the docs win; if they are silent, say the choice is your own.

## Notes

- Docs describe the latest release; the installed version can lag, so check it when behavior may differ.
- Don't paste long excerpts into the code or the reply. Summarize, link and apply.
