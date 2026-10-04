import { Text } from "@react-email/components"
import { Heading } from "../ui/Heading"
import { Layout } from "../ui/Layout"

type NoticeProps = {
  project_name: string
  username: string
  message: string
}

// Security notice email.
export default function Notice({
  project_name = "{{ project_name }}",
  username = "{{ username }}",
  message = "{{ message }}",
}: NoticeProps) {
  return (
    <Layout
      title={`${project_name} - Security notice`}
      preview={`A security notice for your ${project_name} account`}
      project_name={project_name}
    >
      <Heading>Security notice</Heading>
      <Text style={bodyTextStyle}>Hi {username},</Text>
      <Text style={bodyTextStyle}>{message}</Text>
    </Layout>
  )
}

const bodyTextStyle = {
  color: "#334155",
  fontSize: "15px",
  lineHeight: "26px",
  margin: "0 0 18px",
}
