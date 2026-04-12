import React from 'react'
import { cn } from '@/lib/utils.js'

export const Input = React.forwardRef(({ className, ...props }, ref) => {
  return (
    <input
      ref={ref}
      className={cn(
        'w-full h-11 rounded-lg border border-gray-200 bg-white px-3 text-sm body text-[#111827] placeholder:text-gray-400',
        'focus:outline-none focus:ring-2 focus:ring-[#581C87]/40 focus:border-[#581C87]',
        'disabled:opacity-50 disabled:cursor-not-allowed',
        className
      )}
      {...props}
    />
  )
})
Input.displayName = 'Input'
