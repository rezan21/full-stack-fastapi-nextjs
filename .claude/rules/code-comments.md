---
paths:
  - "**/*.{ts,tsx,js,jsx,mjs,cjs,css,py}"
  - "**/Dockerfile*"
  - "**/*.sh"
  - ".pre-commit-config.yaml"
---

## Comments & Doc strings — default to none

Default to no code comments or docstrings. The code itself should be readable. The vendored `frontend/src/components/ui/` and the generated `frontend/src/client/` are out of scope.
Most comments mask a design problem. Before writing one, dissolve the need:

<!-- prettier-ignore -->
| Smell | Fix |
| --- | --- |
| Decorative section-banner comments (`# ── Run history setup ──`) | Use a plain one-line label instead, or extract a helper if the section deserves its own name |
| "What" comments restating the next line | Rename the variable/function |
| Comments about how a decision came about — alternatives tried, what changed and when, ticket/phase refs (`# P0-2:`, `# tried X first`) | Belongs in the commit message and PR description, not the code — the code only needs to say what's true now |
| Comparing this code to an alternative approach ("uses X instead of Y", "rather than Z", "stands in for W until...") | State only what this code does now — the comparison belongs in a PR description, if anywhere |
| A function/method summary that drifts into behavior, triggers, routing/call mechanism, or a specific vendor/library it happens to use internally — instead of stating identity — or enumerates its contents/sub-parts | Say what the thing is: not how or when it's invoked, not which provider it's implemented with, and not a list of what's currently inside it — all three go stale independently of the thing's actual contract |
| References to something else — another function/file by name, a plan, spec, or design doc (`# see handler in foo.py`, `# per events_planning/10`) | Goes stale the moment that thing moves, ships, or is renamed — let names and types express the link, or state the constraint directly |
| Comments narrating what each line does, one by one | Group related lines into a section and give it one short label — don't narrate statement-by-statement |
| Defensive "don't change this" notes | Encode the invariant in a test, assertion, or type |
| A comment added because a change was just made or a decision just taken (usage tips, pointers to a file you just created) | The change is the deliverable, not a reason to caption it — only comment if it independently meets one of the exceptions below |
| A mechanism that feels complex enough to "deserve" explaining (a cache, an intercepting route) — the urge to write more grows exactly here | Resist harder, not less — one factual line or nothing; the complexity is a reason to trust names and types, not narrate around them |

Default to **no comment**, with four narrow, mechanical exceptions:

- A function or method may carry a single-line summary of what it does, directly above its signature; in Python the one-line docstring is that summary. Apply this consistently within a file: if most functions there already have one, an outlier without one is a gap, not restraint. Test functions need none: the test name is the summary. A script that is run directly (a shell script, or a file under a `scripts/` directory) carries a one-line summary of what it does at the top, after any shebang.
- A Dockerfile build stage (`FROM ... AS <name>`) may carry a single-line comment describing that stage's purpose.
- Each hook in `.pre-commit-config.yaml` carries a one-line comment saying what it does.
- A function or render block long enough to have several distinct sections — logic or markup — may label each with one short comment (e.g. `// validate state`, `// upsert user`, `{/* playlists */}`) — a label, not a narration of what each line does.

Nothing else gets a comment — no inline notes explaining individual statements, config values, or one-off lines of logic. Keep every comment to one concise line naming what the thing does; don't restate what a decent name or type already says, and don't reintroduce any of the smells above. This one-line cap applies to docstrings too (Python, JSDoc, etc.) — multi-line isn't exempt just because the syntax allows it. The `one-line comments` pre-commit hooks enforce the cap (Python, shell and Dockerfiles; TS, JS and CSS); tool directives such as `noqa`, `type: ignore` and `biome-ignore` are exempt.

If explaining something properly would take more than two lines, that's not a cue to write a longer comment — it's a signal the implementation is the wrong one. Fix the design; don't caption it.

### Worked examples

The table and exceptions above state each rule; these pairs show them applied to real code from this project. Only the code is the example — "Don't"/"Do" are labels, not part of what's being judged.

Don't — every other function in this file has a one-liner; this one is the odd one out:

```ts
function mapRawVideo(item: RawLikedVideo): YoutubeLikedVideo { ... }
```

Do:

```ts
// Maps a raw YouTube video item to our shape.
function mapRawVideo(item: RawLikedVideo): YoutubeLikedVideo { ... }
```

Don't — narrates the choice (sheet vs. full page) and names the other route:

```ts
// Intercepts /library/[id] when navigated to from the grid, rendering it as a sheet instead of a full page.
export default async function VideoModalPage(...) { ... }
```

Do:

```ts
// Renders the video detail as a sheet.
export default async function VideoModalPage(...) { ... }
```

Don't — "rather than the request" justifies the choice against an alternative source:

```ts
// Returns the app's origin from GOOGLE_REDIRECT_URI rather than the request.
export function getAppOrigin(): string { ... }
```

Do:

```ts
// Returns the app's configured origin.
export function getAppOrigin(): string { ... }
```

Don't — mechanism detail plus a route reference that goes stale if the route changes:

```ts
// Grid of liked videos; clicking a tile opens its detail via /library/[id].
export function LibraryGrid(...) { ... }
```

Do:

```ts
// Grid of liked videos.
export function LibraryGrid(...) { ... }
```

Don't — names the specific provider (Gemini); swap providers later and this is wrong:

```ts
// Generates and caches a video's summary via Gemini, or returns the cached one if it already exists.
export async function generateVideoSummary(videoId: string): Promise<string> { ... }
```

Do:

```ts
// Returns a video's summary, generating and caching it first if none exists yet.
export async function generateVideoSummary(videoId: string): Promise<string> { ... }
```

Don't — "on click" is the trigger, "in place of the button" is the render mechanism; neither is identity:

```ts
// Generates a video's summary on click, then shows the result in place of the button.
export function GenerateSummaryButton({ videoId }: { videoId: string }) { ... }
```

Do:

```ts
// Generates and shows a video's summary.
export function GenerateSummaryButton({ videoId }: { videoId: string }) { ... }
```

Don't — enumerates specific contents (shell, fonts, sidebar nav) that each need this comment edited if they change:

```tsx
// Wraps every page with the base HTML shell, fonts, and the signed-in sidebar nav.
export default async function RootLayout(...) { ... }
```

Do:

```tsx
// Root layout for every page.
export default async function RootLayout(...) { ... }
```

A function doing real work still earns the exception even with no siblings to match — don't skip it just because nothing else in the file has one yet.

Don't — a media-query listener with real logic and no summary at all:

```ts
export function useIsMobile() { ... }
```

Do:

```ts
// Tracks whether the viewport is narrower than the mobile breakpoint.
export function useIsMobile() { ... }
```

Exception 3 (section labels) applied to JSX — each label marks a distinct block, not a line-by-line narration.

Don't — a long dropdown with no section breaks:

```tsx
<DropdownMenuContent>
  <DropdownMenuGroup>...</DropdownMenuGroup>
  <DropdownMenuSeparator />
  <DropdownMenuGroup>...</DropdownMenuGroup>
  <DropdownMenuSeparator />
  <DropdownMenuItem variant="destructive">...</DropdownMenuItem>
</DropdownMenuContent>
```

Do:

```tsx
<DropdownMenuContent>
  {/* identity */}
  <DropdownMenuGroup>...</DropdownMenuGroup>
  <DropdownMenuSeparator />
  {/* settings + appearance */}
  <DropdownMenuGroup>...</DropdownMenuGroup>
  <DropdownMenuSeparator />
  {/* disconnect */}
  <DropdownMenuItem variant="destructive">...</DropdownMenuItem>
</DropdownMenuContent>
```

Summaries name the role, not what is inside today. A field, mechanism, number or audience in the comment goes stale on a small change, and the comment must stay accurate when the code changes a little.

Don't — names the fields the form has today:

```tsx
// Email and password sign-in form.
export function LoginForm() { ... }
```

Do:

```tsx
// Login form.
export function LoginForm() { ... }
```

Don't — describes what the page renders; it is wrong the day the page stops greeting:

```tsx
// Dashboard greeting.
export default async function Page() { ... }
```

Do:

```tsx
// Dashboard page.
export default async function Page() { ... }
```

Don't — hashing and rehash behavior are implementation details that change independently of the contract (the tuple is already in the type):

```python
def verify_password(plain_password: str, hashed_password: str) -> tuple[bool, str | None]:
    """Return whether the password matches, plus an upgraded hash when the stored one is outdated."""
```

Do:

```python
def verify_password(plain_password: str, hashed_password: str) -> tuple[bool, str | None]:
    """Verify a password against its stored hash."""
```

Don't — the comment is a guard for an invariant; nothing fails if it is deleted or ignored:

```python
if not db_user:
    # Prevent timing attacks by running password verification even when user doesn't exist
    verify_password(password, DUMMY_HASH)
    return None
```

Do — drop the note and encode the invariant in a test:

```python
def test_authenticate_unknown_email_still_verifies_a_password_hash(db, monkeypatch) -> None:
    ...
    assert verified_hashes == [crud.DUMMY_HASH]
```

Don't — narrates each statement of a test; the names and assertions already say it:

```python
# Create a bcrypt hash directly (simulating legacy password)
bcrypt_hash = BcryptHasher().hash(password)
assert bcrypt_hash.startswith("$2")  # bcrypt hashes start with $2
# Verify the hash was upgraded to argon2
assert user.hashed_password.startswith("$argon2")
```

Do:

```python
bcrypt_hash = BcryptHasher().hash(password)
assert bcrypt_hash.startswith("$2")
assert user.hashed_password.startswith("$argon2")
```

Don't — a second line pointing at a URL that can move or die:

```dockerfile
# Install uv
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#installing-uv
COPY --from=ghcr.io/astral-sh/uv:0.9.26 /uv /uvx /bin/
```

Do:

```dockerfile
# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.9.26 /uv /uvx /bin/
```

Don't — generated boilerplate that exceeds the one-line cap and repeats what the file already holds (`revision` and `down_revision` are right below it):

```python
"""Add created_at to User and Item

Revision ID: fe56fa70289e
Revises: 1a31ce608336
Create Date: 2026-01-23 15:50:37.171462

"""
```

Do:

```python
"""Add created_at to User and Item"""
```

Don't — commented-out code; version control already keeps it:

```ts
projects: [
  { name: 'setup', testMatch: /.*\.setup\.ts/ },
  // {
  //   name: 'firefox',
  //   use: { ...devices['Desktop Firefox'] },
  // },
],
```

Do — delete the block:

```ts
projects: [
  { name: 'setup', testMatch: /.*\.setup\.ts/ },
],
```

Don't — a script with no summary, and a note that only restates the flag:

```sh
#! /usr/bin/env sh

# Exit in case of error
set -e
```

Do — one line saying what the script does, after the shebang:

```sh
#! /usr/bin/env sh
# Runs the backend tests against a disposable stack.

set -e
```
