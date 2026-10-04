"use client"

import type { ReactNode } from "react"
import {
  type Control,
  Controller,
  type ControllerRenderProps,
  type FieldPath,
  type FieldValues,
} from "react-hook-form"
import {
  Field,
  FieldDescription,
  FieldError,
  FieldLabel,
} from "@/components/ui/field"

type FormFieldProps<
  Values extends FieldValues,
  Name extends FieldPath<Values>,
> = {
  control: Control<Values>
  name: Name
  label: ReactNode
  labelAside?: ReactNode
  description?: ReactNode
  children: (
    props: ControllerRenderProps<Values, Name> & {
      id: string
      "aria-invalid": boolean
    },
  ) => ReactNode
}

// Form field with a label, a control, an optional description and its error.
export function FormField<
  Values extends FieldValues,
  Name extends FieldPath<Values>,
>({
  control,
  name,
  label,
  labelAside,
  description,
  children,
}: FormFieldProps<Values, Name>) {
  return (
    <Controller
      control={control}
      name={name}
      render={({ field, fieldState }) => {
        const labelNode = <FieldLabel htmlFor={field.name}>{label}</FieldLabel>
        return (
          <Field data-invalid={fieldState.invalid}>
            {labelAside ? (
              <div className="flex items-center">
                {labelNode}
                {labelAside}
              </div>
            ) : (
              labelNode
            )}
            {children({
              ...field,
              id: field.name,
              "aria-invalid": fieldState.invalid,
            })}
            {description && <FieldDescription>{description}</FieldDescription>}
            {fieldState.error && <FieldError errors={[fieldState.error]} />}
          </Field>
        )
      }}
    />
  )
}
