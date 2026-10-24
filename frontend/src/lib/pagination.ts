const MAX_PAGE = 100_000

// Parses a page number from a query value.
export function parsePage(value: string | string[] | undefined): number {
  const page = Number(Array.isArray(value) ? value[0] : value)
  return Number.isInteger(page) && page >= 1 ? Math.min(page, MAX_PAGE) : 1
}

// Returns the number of pages for a count of items.
export function pageCount(count: number, pageSize: number): number {
  return Math.max(1, Math.ceil(count / pageSize))
}

// Returns the skip and limit query for a page of a list.
export function pageQuery(page: number, pageSize: number) {
  return { skip: (page - 1) * pageSize, limit: pageSize }
}

// Returns the link to a page of a list, such as /items.
export function pageHref(path: string, page: number): string {
  return page === 1 ? path : `${path}?page=${page}`
}
