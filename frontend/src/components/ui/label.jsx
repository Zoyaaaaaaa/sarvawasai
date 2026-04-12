"use client"

import React from "react"
import { cn } from "@/lib/utils.js"

export function Label({
  className,
  children,
  ...props
}) {
  return (
    <label
      className={cn(
        "text-sm heading text-[#111827] mb-1 block",
        className
      )}
      {...props}
    >
      {children}
    </label>
  )
}
