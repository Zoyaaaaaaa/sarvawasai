import React, { useEffect, useMemo, useState } from 'react'
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
import { useNavigate } from 'react-router-dom'

export default function BuyerAgreement() {
  const navigate = useNavigate()
  const STATIC_DOCUSEAL_EMBED = 'https://docuseal.com/d/74oaCZnsUqhMWA'
  const [form, setForm] = useState({
    buyerName: '',
    buyerAddress: '',
    buyerMobile: '',
    buyerParent: '',
    investorName: '',
    investorAddress: '',
    investorMobile: '',
    investorParent: '',
    propertyName: '',
    propertyLocationText: '',
    propertyValue: '',
    latitude: '',
    longitude: '',
    buyerAmount: '',
    investorAmount: '',
    downPayment: '',
    equityPercent: '',
    
    // DocuSeal helpers
    buyerEmail: '',
    investorEmail: ''
  })

  const [embedSrc, setEmbedSrc] = useState('')
  const [pdfSrc, setPdfSrc] = useState('')
  const [embedLinks, setEmbedLinks] = useState([]) // [{email, role, embed_src}]
  const [activeSigner, setActiveSigner] = useState('buyer') // 'buyer' | 'investor'
  const [submissionId, setSubmissionId] = useState('')
  const [ipfsStatus, setIpfsStatus] = useState('idle') // idle | pending | completed | error
  const [ipfsResult, setIpfsResult] = useState(null)

  useEffect(() => {
    const session = loadAuthSession()
    const userId = session?.userId || localStorage.getItem('userId')
    const hasValidUserId = Boolean(userId && userId !== 'null' && userId !== 'undefined')
    if (!hasValidUserId) return

    const riskMap = { low: 0, medium: 1, moderate: 1, high: 2 }

    const hydrateDefaults = async () => {
      try {
        const buyerRes = await fetch(apiUrl(`/users/profile/${userId}`))
        if (!buyerRes.ok) return
        const buyerData = await buyerRes.json()

        const preferredLocation =
          buyerData?.profile?.preferredLocalities?.[0] ||
          buyerData?.profile?.preferredCities?.[0] ||
          buyerData?.profile?.preferredLocations?.[0] ||
          ''

        setForm((prev) => ({
          ...prev,
          buyerName: prev.buyerName || buyerData?.user?.fullName || '',
          buyerMobile: prev.buyerMobile || buyerData?.user?.phone || '',
          buyerEmail: prev.buyerEmail || buyerData?.user?.email || '',
          propertyLocationText: prev.propertyLocationText || preferredLocation,
          propertyValue: prev.propertyValue || String(buyerData?.profile?.budgetRange?.max || ''),
          buyerAmount: prev.buyerAmount || String(buyerData?.profile?.budgetRange?.min || ''),
          downPayment: prev.downPayment || String(buyerData?.profile?.downPaymentCapability || ''),
        }))

        const maxBudget = buyerData?.profile?.budgetRange?.max
        const riskLevel = buyerData?.profile?.riskToleranceLevel?.toLowerCase()
        if (!maxBudget || !preferredLocation) return

        const recRes = await fetch(apiUrl('/api/recommend'), {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            buyerBudgetMax: maxBudget,
            buyerRisk: riskMap[riskLevel] ?? 1,
            location: preferredLocation,
          }),
        })

        if (!recRes.ok) return
        const recData = await recRes.json()
        const firstInvestor = recData?.recommendations?.[0]
        if (!firstInvestor?.investorId) return

        const investorRes = await fetch(apiUrl(`/users/profile/${firstInvestor.investorId}`))
        if (!investorRes.ok) return
        const investorData = await investorRes.json()
        const investorAddress =
          investorData?.profile?.preferredLocations?.join(', ') ||
          investorData?.profile?.preferredCities?.join(', ') ||
          investorData?.profile?.preferredLocalities?.join(', ') ||
          ''

        setForm((prev) => ({
          ...prev,
          investorName: prev.investorName || investorData?.user?.fullName || '',
          investorMobile: prev.investorMobile || investorData?.user?.phone || '',
          investorEmail: prev.investorEmail || investorData?.user?.email || '',
          investorAddress: prev.investorAddress || investorAddress,
          investorAmount: prev.investorAmount || String(investorData?.profile?.availableCapital || investorData?.profile?.investmentCapital || firstInvestor?.budget || ''),
        }))
      } catch (error) {
        console.warn('Agreement prefill failed:', error)
      }
    }

    hydrateDefaults()
  }, [])

  const onOpenStaticEmbed = () => {
    setEmbedSrc(STATIC_DOCUSEAL_EMBED)
  }

  const onChange = (e) => {
    const { name, value } = e.target
    setForm((f) => ({ ...f, [name]: value }))
  }

  const onSubmit = (e) => {
    e.preventDefault()
    // handle submit
    console.log('Buyer Agreement:', form)
  }

  const onGeneratePdf = async () => {
    try {
      const resp = await fetch(apiUrl('/api/buyer-agreement/pdf-full'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      })
      if (!resp.ok) throw new Error('Failed to generate PDF')
      const blob = await resp.blob()
      const url = URL.createObjectURL(blob)
      setPdfSrc(url)
      // Also open a new tab immediately per request
      window.open(url, '_blank', 'noopener,noreferrer')
    } catch (err) {
      console.error(err)
      alert('Could not generate PDF. Please try again.')
    }
  }

  const onCreateDocuSealSubmission = async () => {
    try {
      if (!form.buyerEmail) {
        alert('Please provide the Buyer Email for DocuSeal signing')
        return
      }
      const resp = await fetch(apiUrl('/api/buyer-agreement/initiate'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          buyerEmail: form.buyerEmail,
          buyerName: form.buyerName,
          investorEmail: form.investorEmail,
          investorName: form.investorName,
        })
      })
      if (!resp.ok) throw new Error('Failed to create DocuSeal submission')
      const data = await resp.json()
      const url = data.embed_src || ''
      const links = Array.isArray(data.embed_srcs) ? data.embed_srcs : []
      setEmbedLinks(links)
      if (!url) {
        console.warn('DocuSeal response did not include embed_src. Response:', data)
        alert('Submission created, but no embed link was returned. Check backend response in console.')
      }
      setEmbedSrc(url)
      setActiveSigner('buyer')
    } catch (err) {
      console.error(err)
      alert('Could not create DocuSeal submission. Please try again.')
    }
  }

  const onSignGeneratedPdf = async () => {
    try {
      if (!form.buyerEmail) {
        alert('Please provide the Buyer Email for DocuSeal signing')
        return
      }
      const resp = await fetch(apiUrl('/api/buyer-agreement/pdf-sign'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form)
      })
      if (!resp.ok) {
        // Surface backend error details (e.g., DocuSeal error 4xx/5xx wrapped in 502)
        let detail = ''
        try {
          const ct = resp.headers.get('content-type') || ''
          if (ct.includes('application/json')) {
            const j = await resp.json()
            detail = j?.error || j?.detail || JSON.stringify(j)
          } else {
            detail = await resp.text()
          }
        } catch {}
        console.error('pdf-sign error', resp.status, detail)
        throw new Error(`Failed to create signing submission for the generated PDF${detail ? `: ${detail}` : ''}`)
      }
      const data = await resp.json()
      const url = data.embed_src || ''
      const links = Array.isArray(data.embed_srcs) ? data.embed_srcs : []
  // Robustly extract submission id
  const sid = data.submission_id || data?.submission?.id || (Array.isArray(data?.submission?.submitters) && data.submission.submitters[0]?.submission_id) || ''
      setEmbedLinks(links)
      if (!url) {
        console.warn('DocuSeal response did not include embed_src. Response:', data)
        alert('Submission created, but no embed link was returned. Check backend response in console.')
      }
      setEmbedSrc(url)
      setActiveSigner('buyer')
      if (sid) {
        console.log('DocuSeal submission ID:', sid)
        setSubmissionId(String(sid))
      }
    } catch (err) {
      console.error(err)
      alert(err?.message || 'Could not create signing submission. Please try again.')
    }
  }

  const finalizeNow = async (sid) => {
    if (!sid) return null
    setIpfsStatus('pending')
    setIpfsResult(null)
    try {
      const body = { submission_id: sid, filename: 'Buyer_Agreement_Signed.pdf' }
      console.log('finalize-now request body:', body)
      const attempt = async () => fetch(apiUrl('/api/docuseal/finalize-now'), { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
      let r = await attempt()
      if (r.status === 409) {
        // Grace period retry #1
        await new Promise(res => setTimeout(res, 2000))
        r = await attempt()
      }
      if (r.status === 409) {
        // Grace period retry #2
        await new Promise(res => setTimeout(res, 5000))
        r = await attempt()
      }
      if (!r.ok) {
        // Surface server validation/processing errors (e.g., 422 from FastAPI with details)
        let detail = ''
        try {
          const ct = r.headers.get('content-type') || ''
          if (ct.includes('application/json')) {
            const j = await r.json()
            // FastAPI 422 typically has { detail: [...] }
            if (j && j.detail) detail = JSON.stringify(j.detail)
            else detail = JSON.stringify(j)
          } else {
            detail = await r.text()
          }
        } catch {}
        console.error('finalize-now error', r.status, detail)
        throw new Error(`Finalize-now failed${detail ? `: ${detail}` : ''}`)
      }
      const j = await r.json()
      if (j.status === 'completed') {
        setIpfsStatus('completed')
        setIpfsResult(j)
        toast.success('Signed PDF uploaded to IPFS.')
        if (j.cid && j.gateway_url) {
          toast.message('IPFS CID', { description: `${j.cid}` })
        }
        const role = loadAuthSession()?.role || localStorage.getItem('userRole')
        setTimeout(() => {
          navigate(getDashboardPath(role), { replace: true })
        }, 1200)
      } else if (j.status === 'not-completed') {
        setIpfsStatus('pending')
        toast.info('Doc not finalized yet. Try again in a moment.')
      } else {
        setIpfsStatus('error')
        toast.error('Finalize returned unexpected status')
      }
      return j
    } catch (e) {
      console.error(e)
      setIpfsStatus('error')
      toast.error('Finalize-now error')
      return null
    }
  }

  const onSubmitAndUpload = async () => {
    try {
      if (!submissionId) {
        toast.error('No submission to finalize')
        return
      }
      toast.info('Finalizing and uploading...')
      const res = await finalizeNow(submissionId)
      // Even if finalize completes, still offer user the signed PDF download
      try {
        const pdfRes = await fetch(apiUrl(`/api/docuseal/finalized-pdf/${encodeURIComponent(submissionId)}`))
        if (pdfRes.ok) {
          const blob = await pdfRes.blob()
          const url = URL.createObjectURL(blob)
          const a = document.createElement('a')
          a.href = url
          a.download = 'finalized_signed.pdf'
          document.body.appendChild(a)
          a.click()
          a.remove()
          URL.revokeObjectURL(url)
        }
      } catch (e) {
        console.warn('Could not download finalized PDF', e)
      }
    } catch (e) {
      console.error(e)
      toast.error('Submit & Upload failed')
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
              <Badge className="bg-[#581C87] text-white">Buyer Agreement</Badge>
              <h1 className="heading text-4xl md:text-5xl text-[#111827] mt-4">
                Formalize the Buyer–Investor Agreement
              </h1>
              <p className="body text-gray-600 mt-3 max-w-2xl">
                Provide legal details for both parties and property specifics. Make sure the information matches your official documents.
              </p>
            </div>
            <div className="flex gap-3 items-center">
              <PDFDialog
                title="Buyer Agreement Preview"
                src={pdfSrc || '/buyer_agreement.pdf'}
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
              <form onSubmit={onSubmit} className="space-y-10">
                <div>
                  <h2 className="heading text-2xl text-[#111827] mb-6">Party Details</h2>
                  <div className="grid md:grid-cols-2 gap-8">
                    <div className="space-y-4">
                      <h3 className="heading text-lg text-[#581C87]">Buyer</h3>
                      <div>
                        <Label htmlFor="buyerName">Legal Name</Label>
                        <Input id="buyerName" name="buyerName" value={form.buyerName} onChange={onChange} placeholder="e.g., Priya Patel" />
                      </div>
                      <div>
                        <Label htmlFor="buyerAddress">Address</Label>
                        <Textarea id="buyerAddress" name="buyerAddress" value={form.buyerAddress} onChange={onChange} placeholder="Residential address" />
                      </div>
                      <div>
                        <Label htmlFor="buyerMobile">Mobile</Label>
                        <Input id="buyerMobile" name="buyerMobile" value={form.buyerMobile} onChange={onChange} placeholder="e.g., 9000000000" />
                      </div>
                      <div>
                        <Label htmlFor="buyerEmail">Email (for DocuSeal)</Label>
                        <Input id="buyerEmail" name="buyerEmail" type="email" value={form.buyerEmail} onChange={onChange} placeholder="buyer@example.com" />
                      </div>
                      <div>
                        <Label htmlFor="buyerParent">Parent Name</Label>
                        <Input id="buyerParent" name="buyerParent" value={form.buyerParent} onChange={onChange} placeholder="e.g., John Doe" />
                      </div>
                    </div>

                    <div className="space-y-4">
                      <h3 className="heading text-lg text-[#1E3A8A]">Investor</h3>
                      <div>
                        <Label htmlFor="investorName">Legal Name</Label>
                        <Input id="investorName" name="investorName" value={form.investorName} onChange={onChange} placeholder="e.g., Rajesh Sharma" />
                      </div>
                      <div>
                        <Label htmlFor="investorAddress">Address</Label>
                        <Textarea id="investorAddress" name="investorAddress" value={form.investorAddress} onChange={onChange} placeholder="Registered address" />
                      </div>
                      <div>
                        <Label htmlFor="investorMobile">Mobile</Label>
                        <Input id="investorMobile" name="investorMobile" value={form.investorMobile} onChange={onChange} placeholder="e.g., 9000000000" />
                      </div>
                      <div>
                        <Label htmlFor="investorEmail">Email (optional)</Label>
                        <Input id="investorEmail" name="investorEmail" type="email" value={form.investorEmail} onChange={onChange} placeholder="investor@example.com" />
                      </div>
                      <div>
                        <Label htmlFor="investorParent">Parent Name</Label>
                        <Input id="investorParent" name="investorParent" value={form.investorParent} onChange={onChange} placeholder="e.g., Suresh Sharma" />
                      </div>
                      
                    </div>
                  </div>
                </div>

                <div>
                  <h2 className="heading text-2xl text-[#111827] mb-6">Property Details</h2>
                  <div className="grid md:grid-cols-2 gap-8">
                    <div className="space-y-4">
                      <div>
                        <Label htmlFor="propertyName">Property Name</Label>
                        <Input id="propertyName" name="propertyName" value={form.propertyName} onChange={onChange} placeholder="e.g., Orchid Heights 2BHK" />
                      </div>
                      <div>
                        <Label htmlFor="propertyLocationText">Location (Text)</Label>
                        <Input id="propertyLocationText" name="propertyLocationText" value={form.propertyLocationText} onChange={onChange} placeholder="Kharghar, Navi Mumbai" />
                      </div>
                      <div>
                        <Label htmlFor="propertyValue">Property Value (₹)</Label>
                        <Input id="propertyValue" name="propertyValue" value={form.propertyValue} onChange={onChange} placeholder="e.g., 9000000" />
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="latitude">Latitude</Label>
                        <Input id="latitude" name="latitude" value={form.latitude} onChange={onChange} placeholder="19.033..." />
                      </div>
                      <div>
                        <Label htmlFor="longitude">Longitude</Label>
                        <Input id="longitude" name="longitude" value={form.longitude} onChange={onChange} placeholder="73.029..." />
                      </div>
                    </div>
                  </div>
                </div>

                <div>
                  <h2 className="heading text-2xl text-[#111827] mb-6">Investment Details</h2>
                  <div className="grid md:grid-cols-2 gap-8">
                    <div>
                      <Label htmlFor="buyerAmount">Buyer Contribution (₹)</Label>
                      <Input id="buyerAmount" name="buyerAmount" value={form.buyerAmount} onChange={onChange} placeholder="e.g., 200000" />
                    </div>
                    <div>
                      <Label htmlFor="investorAmount">Investor Contribution (₹)</Label>
                      <Input id="investorAmount" name="investorAmount" value={form.investorAmount} onChange={onChange} placeholder="e.g., 1800000" />
                    </div>
                  </div>
                  <div className="grid md:grid-cols-2 gap-8 mt-6">
                    <div>
                      <Label htmlFor="downPayment">Down Payment (₹)</Label>
                      <Input id="downPayment" name="downPayment" value={form.downPayment} onChange={onChange} placeholder="e.g., 1800000" />
                    </div>
                    <div>
                      <Label htmlFor="equityPercent">Equity %</Label>
                      <Input id="equityPercent" name="equityPercent" value={form.equityPercent} onChange={onChange} placeholder="e.g., 20" />
                    </div>
                  </div>
                </div>

                

               

                <div className="flex items-center justify-between gap-4 flex-wrap">
                  <p className="body text-gray-600">
                    By submitting, you confirm all details are accurate and consent to agreement drafting.
                  </p>
                  <div className="flex gap-3">
                    <Button type="button" onClick={onGeneratePdf} className="bg-[#1E3A8A] hover:bg-[#1E3A8A]/90 text-white px-6">
                      Generate PDF
                    </Button>
                    <div className="flex gap-2">
                      <Button type="button" onClick={onSignGeneratedPdf} variant="outline" className="px-6">
                        Sign This PDF (API)
                      </Button>
                     
                    </div>
                  </div>
                </div>
              </form>
              {embedSrc ? (
                <div className="mt-10 space-y-3">
                  {/* Switch between Buyer/Investor links if both present */}
                  {embedLinks?.length > 1 && (
                    <div className="flex gap-2">
                      <Button
                        type="button"
                        variant={activeSigner === 'buyer' ? 'default' : 'outline'}
                        onClick={() => {
                          const buyer = embedLinks.find(l => (l.role || '').toLowerCase() === 'buyer' || (l.email || '') === form.buyerEmail)
                          if (buyer?.embed_src) setEmbedSrc(buyer.embed_src)
                          setActiveSigner('buyer')
                        }}
                      >
                        Buyer View
                      </Button>
                      <Button
                        type="button"
                        variant={activeSigner === 'investor' ? 'default' : 'outline'}
                        onClick={() => {
                          const inv = embedLinks.find(l => (l.role || '').toLowerCase() === 'investor' || (l.email || '') === form.investorEmail)
                          if (inv?.embed_src) setEmbedSrc(inv.embed_src)
                          setActiveSigner('investor')
                        }}
                      >
                        Investor View
                      </Button>
                    </div>
                  )}
                  <DocusealForm
                    src={embedSrc}
                    email={activeSigner === 'buyer' ? form.buyerEmail : form.investorEmail}
                    onCompleted={(detail) => {
                      // Heuristic: trust the active view to determine who completed, as some events may not include email
                      const completedEmail = (detail?.email || '').toLowerCase()
                      const buyerEmailLc = (form.buyerEmail || '').toLowerCase()
                      const investorEmailLc = (form.investorEmail || '').toLowerCase()
                      const isBuyer = activeSigner === 'buyer' || (completedEmail && completedEmail === buyerEmailLc)
                      const isInvestor = (activeSigner === 'investor') || (completedEmail && completedEmail === investorEmailLc)
                      if (isBuyer) {
                        const inv = embedLinks.find(l => (l.role || '').toLowerCase() === 'investor' || (l.email || '') === form.investorEmail)
                        toast.success('Buyer has completed signing.')
                        if (inv?.embed_src) {
                          toast.info('Sent to Investor for signing.')
                          // Optionally auto-switch view after a short delay
                          setTimeout(() => {
                            setEmbedSrc(inv.embed_src)
                            setActiveSigner('investor')
                          }, 1200)
                        }
                      }
                      // Investor completed -> single-shot finalize and IPFS upload (no polling)
                      if (isInvestor) {
                        toast.info('Finalizing document and uploading to IPFS...')
                        if (submissionId) {
                          finalizeNow(submissionId)
                        } else {
                          console.warn('No submissionId to finalize')
                        }
                      }
                    }}
                  />
                  {activeSigner === 'investor' && submissionId ? (
                    <div className="mt-3">
                      <Button type="button" onClick={onSubmitAndUpload} className="bg-[#1E3A8A] hover:bg-[#1E3A8A]/90 text-white">
                        Submit & Upload to IPFS
                      </Button>
                    </div>
                  ) : null}
                  {submissionId ? (
                    <div className="text-sm text-gray-600">
                      Submission: <span className="font-mono">{submissionId}</span>
                      {ipfsStatus === 'completed' && ipfsResult?.cid ? (
                        <div className="mt-2">
                          IPFS CID: <span className="font-mono">{ipfsResult.cid}</span>
                          {ipfsResult.gateway_url ? (
                            <>
                              {' '}•{' '}
                              <a className="text-indigo-600 underline" href={ipfsResult.gateway_url} target="_blank" rel="noreferrer">Open</a>
                            </>
                          ) : null}
                        </div>
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