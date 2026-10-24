import type { Control } from "react-hook-form"
import { FormField } from "@/components/common/FormField"
import { Input } from "@/components/ui/input"
import type { ItemFormData } from "@/lib/schemas"

// The title and description fields of an item form.
export function ItemFields({ control }: { control: Control<ItemFormData> }) {
  return (
    <>
      <FormField
        control={control}
        name="title"
        label={
          <>
            Title <span className="text-destructive">*</span>
          </>
        }
      >
        {(field) => <Input {...field} placeholder="Title" type="text" />}
      </FormField>

      <FormField control={control} name="description" label="Description">
        {(field) => (
          <Input
            {...field}
            value={field.value ?? ""}
            placeholder="Description"
            type="text"
          />
        )}
      </FormField>
    </>
  )
}
