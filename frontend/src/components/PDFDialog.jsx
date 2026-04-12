import React from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog.jsx'
import { Button } from '@/components/ui/button.jsx'

export default function PDFDialog({ title = 'Preview PDF', src = '/sample.pdf', triggerClassName = '', children }) {
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="outline" className={triggerClassName}>
          {children || 'View PDF'}
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-[90vw] w-[1000px] h-[85vh] p-0 overflow-hidden gap-0 flex flex-col">
        <DialogHeader className="px-6 py-3 border-b">
          <DialogTitle className="heading text-[#111827]">{title}</DialogTitle>
        </DialogHeader>
        <div className="w-full flex-1 min-h-0">
          <iframe
            title={title}
            src={src}
            className="w-full h-full"
          />
        </div>
      </DialogContent>
    </Dialog>
  )
}