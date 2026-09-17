import { toast } from "sonner"

export default function useCustomToast() {
  const showSuccessToast = (description: string) => {
    toast.success("Success!", { description })
  }

  const showErrorToast = (description: string) => {
    toast.error("Something went wrong!", { description })
  }

  return { showSuccessToast, showErrorToast }
}
