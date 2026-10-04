import type { Metadata } from "next"
import { redirect } from "next/navigation"
import { PageHeader } from "@/components/Common/PageHeader"
import { DeleteAccount } from "@/components/Settings/DeleteAccount"
import { PasswordForm } from "@/components/Settings/PasswordForm"
import { ProfileForm } from "@/components/Settings/ProfileForm"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { getUser } from "@/lib/dal"

export const metadata: Metadata = { title: "Settings - FastAPI Template" }

// Account settings page.
export default async function Page() {
  const user = await getUser()
  if (!user) redirect("/login")

  return (
    <div className="flex flex-col gap-6">
      <PageHeader title="Settings" description="Manage your account settings" />

      <Tabs defaultValue="profile">
        <TabsList>
          <TabsTrigger value="profile">My profile</TabsTrigger>
          <TabsTrigger value="password">Password</TabsTrigger>
          <TabsTrigger value="danger">Danger zone</TabsTrigger>
        </TabsList>

        <TabsContent value="profile">
          <Card className="max-w-xl">
            <CardHeader>
              <CardTitle>My profile</CardTitle>
              <CardDescription>
                Your name and the email you sign in with
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ProfileForm user={user} />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="password">
          <Card className="max-w-xl">
            <CardHeader>
              <CardTitle>Password</CardTitle>
              <CardDescription>
                Choose a new password for your account
              </CardDescription>
            </CardHeader>
            <CardContent>
              <PasswordForm />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="danger">
          <Card className="max-w-xl">
            <CardHeader>
              <CardTitle>Delete account</CardTitle>
              <CardDescription>
                Permanently delete your account and all your items
              </CardDescription>
            </CardHeader>
            <CardContent>
              <DeleteAccount />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
