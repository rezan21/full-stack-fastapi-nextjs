const MAX_PAGE = 100_000

export function parsePage(value: string | string[] | undefined): number {
  const page = Number(Array.isArray(value) ? value[0] : value)
  return Number.isInteger(page) && page >= 1 ? Math.min(page, MAX_PAGE) : 1
}

export function pageCount(count: number, pageSize: number): number {
  return Math.max(1, Math.ceil(count / pageSize))
}

export function itemsPageHref(page: number): string {
  return page === 1 ? "/items" : `/items?page=${page}`
}
