"use client"

import {
  AlertCircle,
  Bell,
  Columns3,
  Grid3x3,
  List,
  Mail,
  Rocket,
  Settings,
  Sparkles,
  Trash2,
} from "lucide-react"
import { useState } from "react"
import { toast } from "sonner"
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import {
  Avatar,
  AvatarFallback,
  AvatarGroup,
  AvatarGroupCount,
} from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Field, FieldGroup, FieldLabel } from "@/components/ui/field"
import {
  InputGroup,
  InputGroupAddon,
  InputGroupInput,
} from "@/components/ui/input-group"
import {
  Popover,
  PopoverContent,
  PopoverDescription,
  PopoverHeader,
  PopoverTitle,
  PopoverTrigger,
} from "@/components/ui/popover"
import { Progress } from "@/components/ui/progress"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Sheet,
  SheetClose,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet"
import { Skeleton } from "@/components/ui/skeleton"
import { Slider } from "@/components/ui/slider"
import { Spinner } from "@/components/ui/spinner"
import { Switch } from "@/components/ui/switch"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Textarea } from "@/components/ui/textarea"
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group"
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import useCustomToast from "@/hooks/useCustomToast"

const colorTokens: {
  name: string
  bg: string
  fg: string
  border?: boolean
}[] = [
  {
    name: "Background",
    bg: "bg-background",
    fg: "text-foreground",
    border: true,
  },
  { name: "Card", bg: "bg-card", fg: "text-card-foreground", border: true },
  {
    name: "Popover",
    bg: "bg-popover",
    fg: "text-popover-foreground",
    border: true,
  },
  { name: "Primary", bg: "bg-primary", fg: "text-primary-foreground" },
  { name: "Secondary", bg: "bg-secondary", fg: "text-secondary-foreground" },
  { name: "Muted", bg: "bg-muted", fg: "text-muted-foreground" },
  { name: "Accent", bg: "bg-accent", fg: "text-accent-foreground" },
  { name: "Destructive", bg: "bg-destructive/10", fg: "text-destructive" },
  {
    name: "Sidebar",
    bg: "bg-sidebar",
    fg: "text-sidebar-foreground",
    border: true,
  },
  {
    name: "Sidebar Primary",
    bg: "bg-sidebar-primary",
    fg: "text-sidebar-primary-foreground",
  },
  {
    name: "Sidebar Accent",
    bg: "bg-sidebar-accent",
    fg: "text-sidebar-accent-foreground",
  },
]

const chartTokens = [
  { name: "Chart 1", bg: "bg-chart-1" },
  { name: "Chart 2", bg: "bg-chart-2" },
  { name: "Chart 3", bg: "bg-chart-3" },
  { name: "Chart 4", bg: "bg-chart-4" },
  { name: "Chart 5", bg: "bg-chart-5" },
]

const radiusTokens = [
  { name: "sm", className: "rounded-sm", px: "6px" },
  { name: "md", className: "rounded-md", px: "8px" },
  { name: "lg", className: "rounded-lg", px: "10px" },
  { name: "xl", className: "rounded-xl", px: "14px" },
  { name: "2xl", className: "rounded-2xl", px: "18px" },
  { name: "3xl", className: "rounded-3xl", px: "22px" },
  { name: "4xl", className: "rounded-4xl", px: "26px" },
]

const typeScale = [
  {
    label: "Heading 1",
    tag: "h1",
    className: "font-heading text-4xl font-bold tracking-tight",
  },
  {
    label: "Heading 2",
    tag: "h2",
    className: "font-heading text-3xl font-semibold tracking-tight",
  },
  {
    label: "Heading 3",
    tag: "h3",
    className: "font-heading text-2xl font-semibold",
  },
  {
    label: "Heading 4",
    tag: "h4",
    className: "font-heading text-xl font-medium",
  },
] as const

const teamMembers = [
  { name: "Alex Rivera", role: "Product Designer", status: "Active" as const },
  { name: "Sam Chen", role: "Backend Engineer", status: "Active" as const },
  { name: "Priya Nair", role: "QA Engineer", status: "Away" as const },
]

// Showcase of the theme and components.
export function Showcase() {
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const [sliderValue, setSliderValue] = useState([40])

  return (
    <div className="flex flex-col gap-6">
      <Card>
        <CardHeader>
          <CardTitle>Design Tokens</CardTitle>
          <CardDescription>
            The semantic colors, radius and elevation driving every component
            below
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-6">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
            {colorTokens.map((token) => (
              <div
                key={token.name}
                className={`flex h-16 items-center justify-center rounded-lg text-sm font-medium ${token.bg} ${token.fg} ${token.border ? "border border-border" : ""}`}
              >
                {token.name}
              </div>
            ))}
          </div>
          <div className="flex flex-wrap gap-4">
            {chartTokens.map((token) => (
              <div
                key={token.name}
                className="flex flex-col items-center gap-1.5"
              >
                <div className={`size-10 rounded-full ${token.bg}`} />
                <span className="text-xs text-muted-foreground">
                  {token.name}
                </span>
              </div>
            ))}
          </div>

          <div className="flex flex-col gap-2.5">
            <span className="text-sm font-medium">Radius</span>
            <div className="flex flex-wrap gap-4">
              {radiusTokens.map((token) => (
                <div
                  key={token.name}
                  className="flex flex-col items-center gap-1.5"
                >
                  <div
                    className={`size-14 border-2 border-primary ${token.className}`}
                  />
                  <span className="text-xs text-muted-foreground">
                    {token.name} · {token.px}
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div className="flex flex-col gap-2.5">
            <span className="text-sm font-medium">Elevation</span>
            <div className="flex flex-wrap gap-4">
              <div className="flex flex-col items-center gap-1.5">
                <div className="flex size-14 items-center justify-center rounded-lg bg-card text-xs text-muted-foreground ring-1 ring-foreground/10">
                  Card
                </div>
                <span className="text-xs text-muted-foreground">
                  ring-1 ring-foreground/10
                </span>
              </div>
              <div className="flex flex-col items-center gap-1.5">
                <div className="flex size-14 items-center justify-center rounded-lg bg-popover text-xs text-muted-foreground shadow-md ring-1 ring-foreground/10">
                  Popover
                </div>
                <span className="text-xs text-muted-foreground">
                  shadow-md + ring
                </span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Typography</CardTitle>
          <CardDescription>
            The type scale and text styles used across the app
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-6">
          <div className="flex flex-col gap-3">
            {typeScale.map(({ label, tag: Tag, className }) => (
              <div key={label} className="flex items-baseline gap-3">
                <Tag className={className}>The quick brown fox</Tag>
                <span className="text-xs text-muted-foreground">{label}</span>
              </div>
            ))}
          </div>

          <div className="flex flex-col gap-3">
            <p className="text-lg text-muted-foreground">
              A lead paragraph introduces a section with slightly larger, muted
              text.
            </p>
            <p className="text-sm leading-relaxed">
              Body text is set at{" "}
              <code className="rounded bg-muted px-1.5 py-0.5 font-mono text-sm">
                text-sm
              </code>{" "}
              with relaxed line height for comfortable reading, and can include
              an{" "}
              <a
                href="https://ui.shadcn.com"
                target="_blank"
                rel="noreferrer"
                className="text-primary underline-offset-4 hover:underline"
              >
                inline link to shadcn/ui
              </a>{" "}
              styled with the primary color.
            </p>
            <p className="text-sm text-muted-foreground">
              Muted text is used for secondary or supporting information.
            </p>
            <p className="text-xs text-muted-foreground">
              Small text is used for captions, hints and metadata.
            </p>
            <blockquote className="border-l-2 border-border pl-4 text-sm text-muted-foreground italic">
              "Simplicity is the ultimate sophistication."
            </blockquote>
            <ul className="ml-5 list-disc text-sm">
              <li>Unordered list item one</li>
              <li>Unordered list item two</li>
            </ul>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Buttons</CardTitle>
            <CardDescription>Variants, sizes and states</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <div className="flex flex-wrap gap-2">
              <Button>Default</Button>
              <Button variant="secondary">Secondary</Button>
              <Button variant="outline">Outline</Button>
              <Button variant="ghost">Ghost</Button>
              <Button variant="destructive">Destructive</Button>
              <Button variant="link">Link</Button>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <Button size="xs">Extra small</Button>
              <Button size="sm">Small</Button>
              <Button size="lg">Large</Button>
              <Button size="icon" aria-label="Notifications">
                <Bell />
              </Button>
              <Button disabled>
                <Spinner data-icon="inline-start" />
                Loading
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Badges</CardTitle>
            <CardDescription>Status and label indicators</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <div className="flex flex-wrap gap-2">
              <Badge>Default</Badge>
              <Badge variant="secondary">Secondary</Badge>
              <Badge variant="outline">Outline</Badge>
              <Badge variant="destructive">Destructive</Badge>
              <Badge variant="ghost">Ghost</Badge>
            </div>
            <div className="flex flex-wrap gap-2">
              <Badge variant="secondary">
                <Sparkles data-icon="inline-start" />
                New
              </Badge>
              <Badge variant="outline">+20.1%</Badge>
              <Badge variant="destructive">
                <AlertCircle data-icon="inline-start" />
                Failed
              </Badge>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Form Elements</CardTitle>
          <CardDescription>
            Inputs, selection and range controls
          </CardDescription>
        </CardHeader>
        <CardContent>
          <FieldGroup className="grid gap-x-6 gap-y-5 sm:grid-cols-2">
            <Field>
              <FieldLabel htmlFor="showcase-email">Email</FieldLabel>
              <InputGroup>
                <InputGroupAddon>
                  <Mail />
                </InputGroupAddon>
                <InputGroupInput
                  id="showcase-email"
                  placeholder="you@example.com"
                />
              </InputGroup>
            </Field>

            <Field>
              <FieldLabel htmlFor="showcase-framework">Framework</FieldLabel>
              <Select defaultValue="next">
                <SelectTrigger id="showcase-framework" className="w-full">
                  <SelectValue placeholder="Select a framework" />
                </SelectTrigger>
                <SelectContent>
                  <SelectGroup>
                    <SelectLabel>Framework</SelectLabel>
                    <SelectItem value="next">Next.js</SelectItem>
                    <SelectItem value="remix">Remix</SelectItem>
                    <SelectItem value="astro">Astro</SelectItem>
                  </SelectGroup>
                </SelectContent>
              </Select>
            </Field>

            <Field className="sm:col-span-2">
              <FieldLabel htmlFor="showcase-message">Message</FieldLabel>
              <Textarea
                id="showcase-message"
                placeholder="Write something..."
              />
            </Field>

            <Field orientation="horizontal">
              <Checkbox id="showcase-marketing" defaultChecked />
              <FieldLabel htmlFor="showcase-marketing" className="font-normal">
                Email me about updates
              </FieldLabel>
            </Field>

            <Field orientation="horizontal">
              <Switch id="showcase-notifications" defaultChecked />
              <FieldLabel
                htmlFor="showcase-notifications"
                className="font-normal"
              >
                Push notifications
              </FieldLabel>
            </Field>

            <Field>
              <FieldLabel>Plan</FieldLabel>
              <RadioGroup defaultValue="pro">
                <Field orientation="horizontal">
                  <RadioGroupItem value="free" id="showcase-plan-free" />
                  <FieldLabel
                    htmlFor="showcase-plan-free"
                    className="font-normal"
                  >
                    Free
                  </FieldLabel>
                </Field>
                <Field orientation="horizontal">
                  <RadioGroupItem value="pro" id="showcase-plan-pro" />
                  <FieldLabel
                    htmlFor="showcase-plan-pro"
                    className="font-normal"
                  >
                    Pro
                  </FieldLabel>
                </Field>
              </RadioGroup>
            </Field>

            <Field>
              <FieldLabel>Layout</FieldLabel>
              <ToggleGroup
                variant="outline"
                defaultValue={["grid"]}
                className="w-fit"
              >
                <ToggleGroupItem value="list" aria-label="List view">
                  <List />
                </ToggleGroupItem>
                <ToggleGroupItem value="grid" aria-label="Grid view">
                  <Grid3x3 />
                </ToggleGroupItem>
                <ToggleGroupItem value="board" aria-label="Board view">
                  <Columns3 />
                </ToggleGroupItem>
              </ToggleGroup>
            </Field>

            <Field className="sm:col-span-2">
              <FieldLabel>Budget — ${sliderValue[0]}</FieldLabel>
              <Slider
                value={sliderValue}
                onValueChange={(value) =>
                  setSliderValue(Array.isArray(value) ? value : [value])
                }
                max={100}
              />
            </Field>
          </FieldGroup>
        </CardContent>
      </Card>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Feedback</CardTitle>
            <CardDescription>
              Alerts, progress and transient status
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <Alert>
              <Rocket />
              <AlertTitle>New feature available</AlertTitle>
              <AlertDescription>
                Take a look at what&apos;s new in this release.
              </AlertDescription>
            </Alert>
            <Alert variant="destructive">
              <AlertCircle />
              <AlertTitle>Something went wrong</AlertTitle>
              <AlertDescription>Please try again in a moment.</AlertDescription>
            </Alert>

            <Progress value={66}>
              <div className="flex justify-between text-sm">
                <span className="font-medium">Uploading</span>
                <span className="text-muted-foreground">66%</span>
              </div>
            </Progress>

            <div className="flex flex-wrap items-center gap-3">
              <Skeleton className="size-10 rounded-full" />
              <div className="flex flex-col gap-2">
                <Skeleton className="h-3 w-32" />
                <Skeleton className="h-3 w-20" />
              </div>
              <Spinner className="ml-auto" />
            </div>

            <div className="flex flex-wrap gap-2">
              <Tooltip>
                <TooltipTrigger render={<Button variant="outline" size="sm" />}>
                  Hover me
                </TooltipTrigger>
                <TooltipContent>A helpful tooltip</TooltipContent>
              </Tooltip>

              <Popover>
                <PopoverTrigger render={<Button variant="outline" size="sm" />}>
                  Open popover
                </PopoverTrigger>
                <PopoverContent>
                  <PopoverHeader>
                    <PopoverTitle>Quick settings</PopoverTitle>
                    <PopoverDescription>
                      Adjust preferences without leaving the page.
                    </PopoverDescription>
                  </PopoverHeader>
                </PopoverContent>
              </Popover>

              <Button
                variant="outline"
                size="sm"
                onClick={() => showSuccessToast("This is a demo notification")}
              >
                Success toast
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => showErrorToast("This is a demo notification")}
              >
                Error toast
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => toast("Event scheduled")}
              >
                Default toast
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Overlays</CardTitle>
            <CardDescription>Dialogs, panels and menus</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-2">
            <Dialog>
              <DialogTrigger render={<Button variant="outline" />}>
                Open dialog
              </DialogTrigger>
              <DialogContent className="sm:max-w-md">
                <DialogHeader>
                  <DialogTitle>Confirm action</DialogTitle>
                  <DialogDescription>
                    This is a demo dialog to preview the overlay styling.
                  </DialogDescription>
                </DialogHeader>
                <DialogFooter>
                  <DialogClose render={<Button variant="outline" />}>
                    Cancel
                  </DialogClose>
                  <Button>Confirm</Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>

            <Sheet>
              <SheetTrigger render={<Button variant="outline" />}>
                Open sheet
              </SheetTrigger>
              <SheetContent>
                <SheetHeader>
                  <SheetTitle>Edit preferences</SheetTitle>
                  <SheetDescription>
                    This is a demo side panel to preview the overlay styling.
                  </SheetDescription>
                </SheetHeader>
                <SheetFooter>
                  <SheetClose render={<Button variant="outline" />}>
                    Close
                  </SheetClose>
                </SheetFooter>
              </SheetContent>
            </Sheet>

            <DropdownMenu>
              <DropdownMenuTrigger render={<Button variant="outline" />}>
                Open menu
              </DropdownMenuTrigger>
              <DropdownMenuContent align="start">
                <DropdownMenuGroup>
                  <DropdownMenuLabel>Actions</DropdownMenuLabel>
                  <DropdownMenuItem>
                    <Settings />
                    Settings
                  </DropdownMenuItem>
                  <DropdownMenuItem>
                    <Bell />
                    Notifications
                  </DropdownMenuItem>
                </DropdownMenuGroup>
                <DropdownMenuSeparator />
                <DropdownMenuItem variant="destructive">
                  <Trash2 />
                  Delete
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Navigation</CardTitle>
            <CardDescription>Tabs and collapsible sections</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-6">
            <Tabs defaultValue="overview">
              <TabsList>
                <TabsTrigger value="overview">Overview</TabsTrigger>
                <TabsTrigger value="analytics">Analytics</TabsTrigger>
                <TabsTrigger value="settings">Settings</TabsTrigger>
              </TabsList>
              <TabsContent value="overview" className="text-muted-foreground">
                A summary view of the current workspace.
              </TabsContent>
              <TabsContent value="analytics" className="text-muted-foreground">
                Usage trends and key metrics over time.
              </TabsContent>
              <TabsContent value="settings" className="text-muted-foreground">
                Workspace preferences and integrations.
              </TabsContent>
            </Tabs>

            <Accordion defaultValue={["item-1"]}>
              <AccordionItem value="item-1">
                <AccordionTrigger>What is this page?</AccordionTrigger>
                <AccordionContent>
                  A reference of the UI components and theme tokens available in
                  this template.
                </AccordionContent>
              </AccordionItem>
              <AccordionItem value="item-2">
                <AccordionTrigger>Is it safe to remove?</AccordionTrigger>
                <AccordionContent>
                  Yes — this page is only a visual reference and isn&apos;t
                  linked from anywhere else in the app logic.
                </AccordionContent>
              </AccordionItem>
            </Accordion>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Data Display</CardTitle>
            <CardDescription>Avatars and tabular data</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-5">
            <AvatarGroup>
              <Avatar>
                <AvatarFallback>AR</AvatarFallback>
              </Avatar>
              <Avatar>
                <AvatarFallback>SC</AvatarFallback>
              </Avatar>
              <Avatar>
                <AvatarFallback>PN</AvatarFallback>
              </Avatar>
              <AvatarGroupCount>+3</AvatarGroupCount>
            </AvatarGroup>

            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {teamMembers.map((member) => (
                  <TableRow key={member.name}>
                    <TableCell className="font-medium">{member.name}</TableCell>
                    <TableCell className="text-muted-foreground">
                      {member.role}
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={
                          member.status === "Active" ? "secondary" : "outline"
                        }
                      >
                        {member.status}
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
