import { Text } from "@react-email/components"
import { LinkButton } from "../ui/Button"
import { Heading } from "../ui/Heading"
import { Layout } from "../ui/Layout"
import { Link } from "../ui/Link"

type ConfirmEmailProps = {
  project_name: string
  username: string
  message: string
  link: string
  valid_for: string
}

// Email address confirmation email.
export default function ConfirmEmail({
  project_name = "{{ project_name }}",
  username = "{{ username }}",
  message = "{{ message }}",
  link = "{{ link }}",
  valid_for = "{{ valid_for }}",
}: ConfirmEmailProps) {
  return (
    <Layout
      title={`${project_name} - Confirm your email`}
      preview={`Confirm your email for ${project_name}`}
      project_name={project_name}
    >
      <Heading>Confirm your email</Heading>
      <Text style={bodyTextStyle}>Hi {username},</Text>
      <Text style={bodyTextStyle}>{message}</Text>
      <LinkButton href={link}>Confirm email</LinkButton>
      <Text style={supportingTextStyle}>
        Or copy and paste this link into your browser:
        <br />
        <Link href={link}>{link}</Link>
      </Text>
      <Text style={supportingTextStyle}>
        This link will expire in {valid_for}.
      </Text>
      <Text style={supportingTextStyle}>
        If you didn't request this, you can safely ignore this email.
      </Text>
    </Layout>
  )
}

const bodyTextStyle = {
  color: "#334155",
  fontSize: "15px",
  lineHeight: "26px",
  margin: "0 0 18px",
}

const supportingTextStyle = {
  color: "#64748b",
  fontSize: "14px",
  lineHeight: "23px",
  margin: "0 0 16px",
}
