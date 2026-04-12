import React, { useEffect, useId, useRef } from 'react'

export default function DocusealForm({ src, email, className = '', onCompleted, onLoad }) {
  const id = useId()
  const formRef = useRef(null)

  useEffect(() => {
    if (!src) return
    // Load DocuSeal web component script once
    const existing = document.querySelector('script[src="https://cdn.docuseal.com/js/form.js"]')
    if (!existing) {
      const script = document.createElement('script')
      script.src = 'https://cdn.docuseal.com/js/form.js'
      script.async = true
      document.head.appendChild(script)
    }
  }, [src])

  useEffect(() => {
    const el = formRef.current
    if (!el || !src) return
    const completedHandler = (e) => {
      // eslint-disable-next-line no-console
      console.log('DocuSeal completed:', e?.detail)
      if (typeof onCompleted === 'function') onCompleted(e?.detail)
    }
    const loadHandler = (e) => {
      // eslint-disable-next-line no-console
      console.log('DocuSeal loaded:', e?.detail)
      if (typeof onLoad === 'function') onLoad(e?.detail)
    }
    el.addEventListener('completed', completedHandler)
    el.addEventListener('load', loadHandler)
    return () => {
      el.removeEventListener('completed', completedHandler)
      el.removeEventListener('load', loadHandler)
    }
  }, [src, onCompleted, onLoad])

  if (!src) return null

  return (
    <div className={`w-full rounded-xl border border-gray-200 overflow-hidden ${className}`}>
      {/* Use official DocuSeal web component to avoid iframe X-Frame-Options blocking */}
      <docuseal-form
        id={id}
        ref={formRef}
        data-src={src}
        {...(email ? { 'data-email': email } : {})}
        data-expand="true"
        data-with-download-button="true"
        style={{ display: 'block', width: '100%', minHeight: '80vh' }}
      />
    </div>
  )
}
