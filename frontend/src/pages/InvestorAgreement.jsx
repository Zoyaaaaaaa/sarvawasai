import React, { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Navbar from '@/components/Navbar.jsx'
import Footer from '@/components/Footer.jsx'
import { Card, CardContent } from '@/components/ui/card.jsx'
import { Button } from '@/components/ui/button.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Input } from '@/components/ui/input.jsx'
import { Label } from '@/components/ui/label.jsx'
import { Textarea } from '@/components/ui/textarea.jsx'
import PDFDialog from '@/components/PDFDialog.jsx'
import DocusealForm from '@/components/DocusealForm.jsx'
import { Toaster } from '@/components/ui/sonner.jsx'
import { toast } from 'sonner'
import { apiUrl } from '@/lib/api.js'
import { getDashboardPath, loadAuthSession } from '@/lib/auth.js'

const EMPTY_INVESTOR = {
  name: '',
  email: '',
  address: '',
  mobile: '',
  amount: '',
  downPayment: '',
  equityPercent: '',
}

const MAX_INVESTOR_SIGNERS = 6

export default function InvestorAgreement() {
  const navigate = useNavigate()

  const defaultHomebuyer = {
    name: '',
    address: '',
    mobile: '',
  }

  const [property, setProperty] = useState({
    propertyName: '',
    propertyLocationText: '',
    propertyValue: '',
    latitude: '',
    longitude: '',
  })

  const [investors, setInvestors] = useState([{ ...EMPTY_INVESTOR }])
  const [pdfUrl, setPdfUrl] = useState('')
  const [embedSrc, setEmbedSrc] = useState('')
  const [embedLinks, setEmbedLinks] = useState([])
  const [activeSignerEmail, setActiveSignerEmail] = useState('')
  const [submissionId, setSubmissionId] = useState('')
  const [ipfsStatus, setIpfsStatus] = useState('idle')
  const [ipfsResult, setIpfsResult] = useState(null)

  const totalAmount = useMemo(
    () => investors.reduce((sum, i) => sum + (parseFloat(i.amount || '0') || 0), 0),
    [investors]
  )

  const updateInvestor = (idx, field, value) => {
    setInvestors((list) => {
      const copy = [...list]
      copy[idx] = { ...copy[idx], [field]: value }
      return copy
    })
  }

  const addInvestor = () => {
    setInvestors((list) => {
      if (list.length >= MAX_INVESTOR_SIGNERS) {
        toast.info(`Investor Agreement supports up to ${MAX_INVESTOR_SIGNERS} signers.`)
        return list
      }
      return [...list, { ...EMPTY_INVESTOR }]
    })
  }

  const removeInvestor = (idx) => setInvestors((list) => list.filter((_, i) => i !== idx))

  const extractEmbedLinks = (payload) => {
    const collected = []

    const pushLink = (item) => {
      if (!item || typeof item !== 'object') return
      const embed =
        item.embed_src ||
        item.embed_url ||
        item.signing_url ||
        item.sign_url ||
        item.url ||
        item.link

      if (!embed) return

      collected.push({
        email: item.email || '',
        role: item.role || '',
        embed_src: embed,
      })
    }

    if (Array.isArray(payload)) {
      payload.forEach(pushLink)
    }

    if (payload && typeof payload === 'object') {
      pushLink(payload)

      if (Array.isArray(payload.embed_srcs)) payload.embed_srcs.forEach(pushLink)
      if (Array.isArray(payload.submitters)) payload.submitters.forEach(pushLink)

      if (payload.submission && typeof payload.submission === 'object') {
        pushLink(payload.submission)
        if (Array.isArray(payload.submission.submitters)) {
          payload.submission.submitters.forEach(pushLink)
        }
      }

      if (payload.data && typeof payload.data === 'object') {
        pushLink(payload.data)
        if (Array.isArray(payload.data.submitters)) {
          payload.data.submitters.forEach(pushLink)
        }
      }
    }

    const deduped = []
    const seen = new Set()
    for (const link of collected) {
      if (!link.embed_src || seen.has(link.embed_src)) continue
      seen.add(link.embed_src)
      deduped.push(link)
    }
    return deduped
  }

  useEffect(() => {
    const session = loadAuthSession()
    const userId = session?.userId || localStorage.getItem('userId')
    const hasValidUserId = Boolean(userId && userId !== 'null' && userId !== 'undefined')
    if (!hasValidUserId) return

    const hydrateInvestor = async () => {
      try {
        const res = await fetch(apiUrl(`/users/profile/${userId}`))
        if (!res.ok) return

        const data = await res.json()
        const address =
          data?.profile?.preferredLocations?.join(', ') ||
          data?.profile?.preferredCities?.join(', ') ||
          data?.profile?.preferredLocalities?.join(', ') ||
          ''

        const defaultAmount = data?.profile?.availableCapital || data?.profile?.investmentCapital || ''

        setInvestors((prev) => {
          const first = prev[0] || { ...EMPTY_INVESTOR }
          const hydratedFirst = {
            ...first,
            name: first.name || data?.user?.fullName || '',
            email: first.email || data?.user?.email || '',
            mobile: first.mobile || data?.user?.phone || '',
            address: first.address || address,
            amount: first.amount || String(defaultAmount || ''),
          }
          return [hydratedFirst, ...prev.slice(1)]
        })
      } catch (error) {
        console.warn('Investor prefill failed:', error)
      }
    }

    hydrateInvestor()
  }, [])

  const buildPayload = () => ({
    homebuyer: defaultHomebuyer,
    property,
    investors: investors.map((inv) => ({
      name: inv.name,
      email: inv.email,
      address: inv.address,
      mobile: inv.mobile,
      amount: inv.amount,
      downPayment: inv.downPayment,
      equityPercent: inv.equityPercent,
    })),
  })

  const onGeneratePdf = async () => {
    try {
      const payload = buildPayload()
      const res = await fetch(apiUrl('/api/investor-agreement/pdf-full'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      if (!res.ok) throw new Error(`Failed to generate PDF: ${res.status}`)

      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      setPdfUrl(url)
      window.open(url, '_blank', 'noopener,noreferrer')
    } catch (err) {
      console.error(err)
      alert('Failed to generate PDF. Please try again.')
    }
  }

  const onCreateDocuSealSubmission = async () => {
    const submitters = investors
      .filter((inv) => inv.email)
      .map((inv) => ({ email: inv.email.trim(), name: (inv.name || '').trim() }))

    if (!submitters.length) {
      alert('Add at least one investor email for DocuSeal signing')
      return
    }

    if (submitters.length > MAX_INVESTOR_SIGNERS) {
      alert(`Investor Agreement supports up to ${MAX_INVESTOR_SIGNERS} signers.`)
      return
    }

    try {
      const payload = buildPayload()
      const res = await fetch(apiUrl('/api/investor-agreement/pdf-sign'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      if (!res.ok) {
        const errPayload = await res.json().catch(() => ({}))
        throw new Error(errPayload.error || errPayload.detail || 'Failed to create DocuSeal submission')
      }

      const data = await res.json()
      const links = extractEmbedLinks(data)
      const initialEmbed = data.embed_src || data.embed_url || links[0]?.embed_src || ''
      const sid =
        data.submission_id ||
        data?.submission?.id ||
        (Array.isArray(data?.submission?.submitters) && data.submission.submitters[0]?.submission_id) ||
        ''

      setEmbedLinks(links)
      setEmbedSrc(initialEmbed)
      setActiveSignerEmail((links[0]?.email || submitters[0]?.email || '').trim())
      if (sid) setSubmissionId(String(sid))

      if (!initialEmbed) {
        console.warn('DocuSeal submission created without embed link. Raw response:', data)
        toast.info('Submission created, but embed link was not returned. Please check DocuSeal configuration/template settings.')
      }
    } catch (error) {
      console.error(error)
      alert(error?.message || 'Could not create DocuSeal submission')
    }
  }

  const finalizeNow = async (sid) => {
    if (!sid) return null

    setIpfsStatus('pending')
    setIpfsResult(null)

    try {
      const body = {
        submission_id: sid,
        filename: 'Investor_Agreement_Signed.pdf',
      }

      const attempt = async () =>
        fetch(apiUrl('/api/docuseal/finalize-now'), {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
        })

      let r = await attempt()
      if (r.status === 409) {
        await new Promise((res) => setTimeout(res, 2000))
        r = await attempt()
      }
      if (r.status === 409) {
        await new Promise((res) => setTimeout(res, 5000))
        r = await attempt()
      }

      if (!r.ok) {
        let detail = ''
        try {
          const ct = r.headers.get('content-type') || ''
          if (ct.includes('application/json')) {
            const j = await r.json()
            detail = j?.detail ? JSON.stringify(j.detail) : JSON.stringify(j)
          } else {
            detail = await r.text()
          }
        } catch {
          detail = ''
        }
        throw new Error(`Finalize-now failed${detail ? `: ${detail}` : ''}`)
      }

      const j = await r.json()

      if (j.status === 'completed') {
        setIpfsStatus('completed')
        setIpfsResult(j)
        toast.success('Signed PDF uploaded to IPFS.')

        const role = loadAuthSession()?.role || localStorage.getItem('userRole')
        setTimeout(() => {
          navigate(getDashboardPath(role), { replace: true })
        }, 1200)
      } else if (j.status === 'not-completed') {
        setIpfsStatus('pending')
        toast.info('Document not fully signed yet. Ask remaining investors to sign.')
      } else {
        setIpfsStatus('error')
        toast.error('Finalize returned unexpected status')
      }

      return j
    } catch (error) {
      console.error(error)
      setIpfsStatus('error')
      toast.error(error?.message || 'Finalize-now error')
      return null
    }
  }

  const onSubmitAndUpload = async () => {
    if (!submissionId) {
      toast.error('No submission to finalize')
      return
    }

    toast.info('Finalizing and uploading...')
    await finalizeNow(submissionId)

    try {
      const pdfRes = await fetch(apiUrl(`/api/docuseal/finalized-pdf/${encodeURIComponent(submissionId)}`))
      if (pdfRes.ok) {
        const blob = await pdfRes.blob()
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = 'investor_agreement_finalized_signed.pdf'
        document.body.appendChild(a)
        a.click()
        a.remove()
        URL.revokeObjectURL(url)
      }
    } catch (error) {
      console.warn('Could not download finalized PDF', error)
    }
  }

  const handleSelectSigner = (email) => {
    const normalized = (email || '').toLowerCase()
    const selected = embedLinks.find((l) => (l.email || '').toLowerCase() === normalized)
    if (selected?.embed_src) {
      setEmbedSrc(selected.embed_src)
      setActiveSignerEmail(selected.email || email)
    }
  }

  return (
    <div className="min-h-screen bg-white font-inter">
      <Toaster richColors position="top-right" />
      <Navbar />

      <section className="bg-gray-50/60 border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
          <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-6">
            <div>
              <Badge className="bg-[#1E3A8A] text-white">Investor Agreement</Badge>
              <h1 className="heading text-4xl md:text-5xl text-[#111827] mt-4">Define Multi-Investor Terms</h1>
              <p className="body text-gray-600 mt-3 max-w-2xl">
                Add all investor parties along with property details. Generate PDF, send for DocuSeal signing,
                and upload finalized agreement to blockchain/IPFS.
              </p>
            </div>
            <div className="flex gap-3 items-center">
              <PDFDialog
                title="Investor Agreement Preview"
                src={pdfUrl || '/investor_agreement.pdf'}
                triggerClassName="border-2 border-[#111827]/15 text-[#111827] hover:bg-gray-50"
              >
                Preview PDF
              </PDFDialog>
              <PDFDialog
                title="DocuSeal Signing"
                src={embedSrc || 'about:blank'}
                triggerClassName="border-2 border-[#1E3A8A]/15 text-[#1E3A8A] hover:bg-indigo-50"
              >
                Open Signing
              </PDFDialog>
            </div>
          </div>
        </div>
      </section>

      <section className="py-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <Card className="rounded-2xl shadow-lg border-0">
            <CardContent className="p-6 md:p-10">
              <form onSubmit={(e) => e.preventDefault()} className="space-y-10">
                <div>
                  <h2 className="heading text-2xl text-[#111827] mb-6">Property Details</h2>
                  <div className="grid md:grid-cols-2 gap-8">
                    <div className="space-y-4">
                      <div>
                        <Label htmlFor="propName">Property Name</Label>
                        <Input
                          id="propName"
                          value={property.propertyName}
                          onChange={(e) => setProperty((v) => ({ ...v, propertyName: e.target.value }))}
                          placeholder="e.g., Orchid Heights 2BHK"
                        />
                      </div>
                      <div>
                        <Label htmlFor="propLocText">Location (Text)</Label>
                        <Input
                          id="propLocText"
                          value={property.propertyLocationText}
                          onChange={(e) => setProperty((v) => ({ ...v, propertyLocationText: e.target.value }))}
                          placeholder="Kharghar, Navi Mumbai"
                        />
                      </div>
                      <div>
                        <Label htmlFor="propValue">Property Value (INR)</Label>
                        <Input
                          id="propValue"
                          value={property.propertyValue}
                          onChange={(e) => setProperty((v) => ({ ...v, propertyValue: e.target.value }))}
                          placeholder="e.g., 9000000"
                        />
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="lat">Latitude</Label>
                        <Input
                          id="lat"
                          value={property.latitude}
                          onChange={(e) => setProperty((v) => ({ ...v, latitude: e.target.value }))}
                          placeholder="19.033..."
                        />
                      </div>
                      <div>
                        <Label htmlFor="lng">Longitude</Label>
                        <Input
                          id="lng"
                          value={property.longitude}
                          onChange={(e) => setProperty((v) => ({ ...v, longitude: e.target.value }))}
                          placeholder="73.029..."
                        />
                      </div>
                    </div>
                  </div>
                </div>

                <div>
                  <div className="flex items-center justify-between mb-6">
                    <h2 className="heading text-2xl text-[#111827]">Investors</h2>
                    <div className="flex items-center gap-2">
                      <Badge className="bg-[#581C87] text-white">{investors.length} total</Badge>
                      <Badge className="bg-[#1E3A8A] text-white">INR {totalAmount.toLocaleString('en-IN')} total</Badge>
                    </div>
                  </div>

                  <div className="space-y-8">
                    {investors.map((inv, idx) => (
                      <Card key={idx} className="rounded-xl border border-gray-100 shadow-sm">
                        <CardContent className="p-6">
                          <div className="flex items-center justify-between mb-4">
                            <h3 className="heading text-lg text-[#111827]">Investor #{idx + 1}</h3>
                            {investors.length > 1 && (
                              <Button
                                type="button"
                                variant="outline"
                                className="border-gray-200 text-[#111827] hover:bg-gray-50"
                                onClick={() => removeInvestor(idx)}
                              >
                                Remove
                              </Button>
                            )}
                          </div>

                          <div className="grid md:grid-cols-3 gap-6">
                            <div>
                              <Label>Legal Name</Label>
                              <Input
                                value={inv.name}
                                onChange={(e) => updateInvestor(idx, 'name', e.target.value)}
                                placeholder="e.g., Rajesh Sharma"
                              />
                            </div>
                            <div>
                              <Label>Email (for DocuSeal)</Label>
                              <Input
                                type="email"
                                value={inv.email}
                                onChange={(e) => updateInvestor(idx, 'email', e.target.value)}
                                placeholder="investor@example.com"
                              />
                            </div>
                            <div>
                              <Label>Mobile Number</Label>
                              <Input
                                value={inv.mobile}
                                onChange={(e) => updateInvestor(idx, 'mobile', e.target.value)}
                                placeholder="+91-"
                              />
                            </div>
                            <div>
                              <Label>Amount (INR)</Label>
                              <Input
                                value={inv.amount}
                                onChange={(e) => updateInvestor(idx, 'amount', e.target.value)}
                                placeholder="e.g., 500000"
                              />
                            </div>
                            <div>
                              <Label htmlFor={`downPayment-${idx}`}>Down Payment (INR)</Label>
                              <Input
                                id={`downPayment-${idx}`}
                                value={inv.downPayment}
                                onChange={(e) => updateInvestor(idx, 'downPayment', e.target.value)}
                                placeholder="e.g., 1800000"
                              />
                            </div>
                            <div>
                              <Label htmlFor={`equityPercent-${idx}`}>Equity %</Label>
                              <Input
                                id={`equityPercent-${idx}`}
                                value={inv.equityPercent}
                                onChange={(e) => updateInvestor(idx, 'equityPercent', e.target.value)}
                                placeholder="e.g., 20"
                              />
                            </div>
                            <div className="md:col-span-3">
                              <Label htmlFor={`address-${idx}`}>Address</Label>
                              <Textarea
                                id={`address-${idx}`}
                                value={inv.address}
                                onChange={(e) => updateInvestor(idx, 'address', e.target.value)}
                                placeholder="Registered address"
                              />
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>

                  <div className="mt-6">
                    <Button
                      type="button"
                      className="bg-[#581C87] hover:bg-[#581C87]/90 text-white"
                      onClick={addInvestor}
                      disabled={investors.length >= MAX_INVESTOR_SIGNERS}
                    >
                      Add another investor
                    </Button>
                    <p className="text-xs text-gray-500 mt-2">Maximum {MAX_INVESTOR_SIGNERS} signers supported.</p>
                  </div>
                </div>

                <div className="flex items-center justify-between gap-4 flex-wrap">
                  <p className="body text-gray-600">Review all details before generating and signing the agreement.</p>
                  <div className="flex gap-3">
                    <Button type="button" onClick={onGeneratePdf} className="bg-[#1E3A8A] hover:bg-[#1E3A8A]/90 text-white">
                      Generate PDF
                    </Button>
                    <Button type="button" onClick={onCreateDocuSealSubmission} variant="outline">
                      Create DocuSeal Submission
                    </Button>
                  </div>
                </div>
              </form>

              {embedSrc ? (
                <div className="mt-10 space-y-3">
                  {embedLinks?.length > 1 && (
                    <div className="flex flex-wrap gap-2">
                      {embedLinks.map((link, idx) => (
                          <Button
                            key={`${link.email || link.role || 'signer'}-${idx}`}
                            type="button"
                            variant={(activeSignerEmail || '').toLowerCase() === (link.email || '').toLowerCase() ? 'default' : 'outline'}
                            onClick={() => handleSelectSigner(link.email)}
                          >
                            {link.role || link.email || `Signer ${idx + 1}`}
                          </Button>
                        ))}
                    </div>
                  )}

                  <DocusealForm
                    key={`${embedSrc}|${activeSignerEmail}`}
                    src={embedSrc}
                    email={activeSignerEmail}
                    onCompleted={() => toast.info('Signer completion received.')}
                  />

                  {submissionId ? (
                    <div className="mt-3 flex items-center gap-3 flex-wrap">
                      <Button type="button" onClick={onSubmitAndUpload} className="bg-[#1E3A8A] hover:bg-[#1E3A8A]/90 text-white">
                        Submit & Upload to IPFS
                      </Button>
                      <span className="text-sm text-gray-600">
                        Submission: <span className="font-mono">{submissionId}</span>
                      </span>
                    </div>
                  ) : null}

                  {ipfsStatus === 'completed' && ipfsResult?.cid ? (
                    <div className="text-sm text-gray-700">
                      IPFS CID: <span className="font-mono">{ipfsResult.cid}</span>
                      {ipfsResult.gateway_url ? (
                        <>
                          {' '}•{' '}
                          <a className="text-indigo-600 underline" href={ipfsResult.gateway_url} target="_blank" rel="noreferrer">
                            Open
                          </a>
                        </>
                      ) : null}
                    </div>
                  ) : null}
                </div>
              ) : null}
            </CardContent>
          </Card>
        </div>
      </section>

      <Footer />
    </div>
  )
}
