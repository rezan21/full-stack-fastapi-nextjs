import path from "node:path"
import { fileURLToPath } from "node:url"
import dotenv from "dotenv"

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

dotenv.config({ path: path.join(__dirname, "../../backend/.env") })

// Reads a required environment variable.
function getEnvVar(name: string): string {
  const value = process.env[name]
  if (!value) {
    throw new Error(`Environment variable ${name} is undefined`)
  }
  return value
}

export const e2eAdminEmail = "e2e-admin@example.com"
export const e2eUserEmail = "e2e-user@example.com"
export const e2eUserName = "E2E User"
export const e2ePassword = getEnvVar("E2E_PASSWORD")
