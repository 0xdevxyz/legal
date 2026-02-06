"use client"

import * as React from "react"
import { cn } from "@/lib/utils"

interface SliderProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'value' | 'onChange'> {
  onValueChange?: (value: number[]) => void;
  value?: number[];
  min?: number;
  max?: number;
  step?: number;
}

const Slider = React.forwardRef<HTMLInputElement, SliderProps>(
  ({ className, onValueChange, value, min = 0, max = 100, step = 1, ...props }, ref) => {
    const currentValue = value?.[0] ?? 50;

    return (
      <input
        type="range"
        ref={ref}
        min={min}
        max={max}
        step={step}
        value={currentValue}
        onChange={(e) => {
          onValueChange?.([Number(e.target.value)]);
        }}
        className={cn(
          "w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-500",
          className
        )}
        {...props}
      />
    );
  }
);
Slider.displayName = "Slider";

export { Slider };
