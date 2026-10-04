import { toast } from "sonner"

// Provides toast helpers.
export default function useCustomToast() {
  const showSuccessToast = (description: string) => {
    toast.success("Success!", { description })
  }

  const showErrorToast = (description: string) => {
    toast.error("Something went wrong!", { description })
  }

  return { showSuccessToast, showErrorToast }
}
