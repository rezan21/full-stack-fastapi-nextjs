// Fails on comments that span more than one line.
import { execFileSync } from "node:child_process"
import { readFileSync } from "node:fs"
import ts from "typescript"

const CHECKED_FILES =
  /^(frontend|packages)\/(?!src\/(components\/ui|client)\/).*\.(ts|tsx|js|jsx|mjs|cjs|css)$/
const TOOL_DIRECTIVE =
  /^(\/\/\/|\/\/|\/\*+)\s*(biome-ignore|@ts-|eslint-|prettier-ignore|istanbul|c8 |<reference)/

// Runs a git command and returns its trimmed output.
const git = (...args: string[]) =>
  execFileSync("git", args, { encoding: "utf8" }).trim()
const root = git("rev-parse", "--show-toplevel")
const files = git("-C", root, "ls-files").split("\n")

// Returns every comment range in a source file.
function comments(file: string, text: string): ts.CommentRange[] {
  const source = ts.createSourceFile(file, text, ts.ScriptTarget.Latest, true)
  const found = new Map<number, ts.CommentRange>()
  const visit = (node: ts.Node) => {
    const children = node.getChildren(source)
    if (children.length === 0) {
      for (const range of ts.getLeadingCommentRanges(text, node.pos) ?? []) {
        found.set(range.pos, range)
      }
    }
    children.forEach(visit)
  }
  visit(source)
  return [...found.values()].sort((a, b) => a.pos - b.pos)
}

const problems: string[] = []
for (const file of files) {
  if (!CHECKED_FILES.test(file)) continue
  const text = readFileSync(`${root}/${file}`, "utf8")
  const lineAt = (pos: number) => text.slice(0, pos).split("\n").length
  const report = (pos: number, size: number) =>
    problems.push(`${file}:${lineAt(pos)}: comment spans ${size} lines`)

  // css
  if (file.endsWith(".css")) {
    for (const match of text.matchAll(/\/\*[\s\S]*?\*\//g)) {
      const size = match[0].split("\n").length
      if (size > 1) report(match.index ?? 0, size)
    }
    continue
  }

  // ts and js
  let run: { pos: number; size: number } | undefined
  const endRun = () => {
    if (run && run.size > 1) report(run.pos, run.size)
    run = undefined
  }
  for (const range of comments(file, text)) {
    const body = text.slice(range.pos, range.end)
    if (TOOL_DIRECTIVE.test(body)) {
      endRun()
      continue
    }
    if (range.kind === ts.SyntaxKind.MultiLineCommentTrivia) {
      endRun()
      const size = body.split("\n").length
      if (size > 1) report(range.pos, size)
      continue
    }
    const lineStart = text.lastIndexOf("\n", range.pos - 1) + 1
    const standalone = text.slice(lineStart, range.pos).trim() === ""
    if (standalone && run && lineAt(range.pos) === lineAt(run.pos) + run.size) {
      run.size++
    } else {
      endRun()
      if (standalone) run = { pos: range.pos, size: 1 }
    }
  }
  endRun()
}

// report
if (problems.length > 0) {
  console.error(`${problems.join("\n")}\nComments must fit on one line.`)
  process.exit(1)
}
