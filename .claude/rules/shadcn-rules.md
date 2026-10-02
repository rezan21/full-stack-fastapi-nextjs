---
paths:
  - "frontend/**/*.{tsx,css}"
---

# shadcn/ui Rules

This project uses shadcn/ui as the standard for all UI, going forward — no hand-rolled markup where a shadcn component already exists. Base UI primitives (`base-nova` style), `lucide-react` icons. Invoke the `shadcn` skill for anything shadcn-related.

## Component-first

- Before writing new UI, check `frontend/src/components/ui/` for an existing component. Don't hand-roll a `<button>`, styled `<div>`, or custom badge/alert/card/table row when a shadcn equivalent exists.
- Missing component → `npx shadcn@latest add <name>` from `frontend/`. Don't hand-write the primitive.
- Don't edit generated files in `frontend/src/components/ui/` for one-off styling; extend via `className`/variants at the call site instead.

## Base UI, not Radix

- This project's base is `base` (Base UI), not `radix`. Custom triggers use the `render` prop (`<DialogTrigger render={<Button />}>`), never `asChild`.
- If `render` swaps in a non-button element (`<a>`, `<span>`), pass `nativeButton={false}`.

## Styling

- Semantic color tokens only (`bg-background`, `text-foreground`, `text-muted-foreground`, `bg-card`, `bg-primary`, `bg-destructive`, `border-border`, …) — never raw Tailwind colors (`bg-zinc-50`, `text-red-500`) or hex values.
- `gap-*` on `flex`, never `space-x-*`/`space-y-*`. `size-*` when width and height match.
- No manual `dark:` color overrides — the `.dark` class plus the CSS variables in `globals.css` already handle theming.
- `frontend/src/app/globals.css` theme variables (`:root`, `.dark`, `@theme inline`) are managed by the shadcn CLI (`init`, `apply`). Prefer `npx shadcn@latest apply <preset>` over hand-editing those blocks, so they stay in sync with the registry.

## Composition

- Items live inside their Group (`DropdownMenuItem` → `DropdownMenuGroup`, `SelectItem` → `SelectGroup`).
- Full `Card` composition (`CardHeader`/`CardTitle`/`CardContent`/`CardFooter`) instead of dumping everything into `CardContent`.
- `Dialog`/`Sheet`/`Drawer` always need a `Title` (`sr-only` if visually hidden).
