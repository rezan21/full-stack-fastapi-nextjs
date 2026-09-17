const API_BASE = `${process.env.API_URL ?? "http://localhost:8000"}/api/v1`

export const createUser = async ({
  email,
  password,
}: {
  email: string
  password: string
}) => {
  const res = await fetch(`${API_BASE}/private/users/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      email,
      password,
      is_verified: true,
      full_name: "Test User",
    }),
  })
  if (!res.ok) {
    throw new Error(`Failed to create user: ${res.status}`)
  }
  return res.json()
}
