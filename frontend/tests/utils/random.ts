export const randomEmail = () =>
  `test_${Math.random().toString(36).substring(7)}@example.com`

export const randomPassword = () => crypto.randomUUID()

export const randomItemTitle = () =>
  `Item ${Math.random().toString(36).substring(7)}`

export const randomItemDescription = () =>
  `Description ${Math.random().toString(36).substring(7)}`
