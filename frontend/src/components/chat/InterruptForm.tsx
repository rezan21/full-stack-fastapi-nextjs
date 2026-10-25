"use client"

import {
  type AgUiInterrupt,
  useAgUiSubmitInterruptResponses,
} from "@assistant-ui/react-ag-ui"
import { useState } from "react"
import {
  ElicitationForm,
  type ElicitationState,
} from "@/components/assistant-ui/elements/elicitation-form"
import {
  type FormValues,
  formDefaults,
  formFields,
  formPayload,
} from "./interrupt-form"

// Form for the input the assistant asks for, built from the interrupt's schema.
export function InterruptForm({
  interrupt,
  problem,
}: {
  interrupt: AgUiInterrupt
  problem?: (answer: Record<string, string | boolean>) => string | undefined
}) {
  const submitInterruptResponses = useAgUiSubmitInterruptResponses()
  const [values, setValues] = useState<FormValues>(() =>
    formDefaults(interrupt.responseSchema),
  )
  const [state, setState] = useState<ElicitationState>("request")
  const [error, setError] = useState<string>()

  const respond = async (
    next: ElicitationState,
    status: "resolved" | "cancelled",
    payload?: Record<string, string | boolean>,
  ) => {
    setError(undefined)
    setState(next)
    try {
      await submitInterruptResponses([
        { interruptId: interrupt.id, status, payload },
      ])
    } catch {
      setState("request")
      setError("Your answer could not be recorded. Try again.")
    }
  }

  const accept = () => {
    const answer = formPayload(interrupt.responseSchema, values)
    const invalid = problem?.(answer)
    if (invalid) setError(invalid)
    else void respond("accepted", "resolved", answer)
  }

  return (
    <div className="flex flex-col gap-2">
      <ElicitationForm
        server="Assistant"
        message={interrupt.message ?? "More details are needed."}
        fields={formFields(interrupt.responseSchema, values)}
        state={state}
        onFieldChange={(name, value) =>
          setValues((current) => ({ ...current, [name]: value }))
        }
        onAccept={accept}
        onDecline={() => void respond("declined", "cancelled")}
      />
      {error && (
        <p role="alert" className="text-sm text-destructive">
          {error}
        </p>
      )}
    </div>
  )
}
