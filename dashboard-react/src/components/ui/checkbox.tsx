"use client"

import * as React from "react"
import { Check } from "lucide-react"

interface CheckboxProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'onChange'> {
  checked?: boolean
  onCheckedChange?: (checked: boolean) => void
}

const Checkbox = React.forwardRef<HTMLInputElement, CheckboxProps>(
  ({ className = "", checked = false, onCheckedChange, ...props }, ref) => {
    return (
      <button
        type="button"
        role="checkbox"
        aria-checked={checked}
        className={`
          peer h-4 w-4 shrink-0 rounded-sm border border-gray-600 
          ring-offset-background focus-visible:outline-none 
          focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 
          disabled:cursor-not-allowed disabled:opacity-50 
          ${checked ? 'bg-orange-500 border-orange-500 text-white' : 'bg-gray-800'}
          ${className}
        `}
        onClick={() => onCheckedChange?.(!checked)}
        {...(props as any)}
      >
        {checked && (
          <Check className="h-3 w-3 text-white mx-auto" />
        )}
      </button>
    )
  }
)
Checkbox.displayName = "Checkbox"

export { Checkbox }
