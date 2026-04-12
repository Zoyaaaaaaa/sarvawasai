import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import Navbar from '@/components/Navbar.jsx'
import Footer from '@/components/Footer.jsx'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Button } from '@/components/ui/button.jsx'
import {
  Users,
  Brain,
  Target,
  MapPin,
  DollarSign,
  Clock3,
  ShieldCheck,
  ArrowLeft,
  RefreshCw,
  ArrowUpRight
} from 'lucide-react'
import { apiUrl } from '@/lib/api.js'

const API_BASE = apiUrl('/api/ml-similarity')

const getMatchQuality = (score = 0) => {
  if (score >= 2) return { label: 'Excellent', tone: 'bg-emerald-100 text-emerald-800' }
  if (score >= 1) return { label: 'Great', tone: 'bg-blue-100 text-blue-800' }
  if (score >= 0.5) return { label: 'Fair', tone: 'bg-amber-100 text-amber-800' }
  return { label: 'Emerging', tone: 'bg-slate-100 text-slate-800' }
}

const scoreToPercent = (score) => {
  if (typeof score !== 'number') return null
  const normalized = 1 / (1 + Math.exp(-score))
  return Math.round(normalized * 100)
}

const formatCurrency = (value) => {
  if (!value && value !== 0) return '—'
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0
  }).format(value)
}

export default function CoVestMatches() {
  const { userId } = useParams()
  const navigate = useNavigate()
  const [topK, setTopK] = useState(20)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [data, setData] = useState(null)

  const matches = data?.matches || []
  const queryInvestor = data?.queryInvestor
  const querySummary = data?.queryProfileSummary

  const handleOpenMatch = (match) => {
    if (!match?.userId) return
    navigate(`/investors/${match.userId}`, {
      state: {
        match,
        queryInvestor,
        querySummary
      }
    })
  }

  const fetchMatches = useCallback(async () => {
    if (!userId) {
      setError('Missing investor identifier')
      setLoading(false)
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response = await fetch(`${API_BASE}/matches/${userId}?top_k=${topK}`)
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}))
        throw new Error(payload.detail || 'Unable to load matches')
      }
      const payload = await response.json()
      setData(payload)
    } catch (err) {
      setError(err.message)
      setData(null)
    } finally {
      setLoading(false)
    }
  }, [topK, userId])

  useEffect(() => {
    fetchMatches()
  }, [fetchMatches])

  const profileStats = useMemo(() => [
    {
      label: 'Capital Band',
      value: querySummary?.capital_band ?? '—'
    },
    {
      label: 'Expected ROI',
      value: querySummary?.expected_roi_band ? querySummary.expected_roi_band.toUpperCase() : '—'
    },
    {
      label: 'Holding Period',
      value: querySummary?.holding_period_band ? querySummary.holding_period_band.toUpperCase() : '—'
    },
    {
      label: 'Risk Orientation',
      value: querySummary?.risk_orientation?.toFixed?.(1) ?? '—'
    },
    {
      label: 'Collaboration Comfort',
      value: querySummary?.collaboration_comfort?.toFixed?.(1) ?? '—'
    },
    {
      label: 'Control Preference',
      value: querySummary?.control_preference?.toFixed?.(1) ?? '—'
    }
  ], [querySummary])

  return (
    <div className="min-h-screen bg-[#F9FAFB] font-inter">
      <Navbar />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-sm text-slate-500">Personalized Co-Vesting</p>
            <h1 className="text-3xl font-bold text-slate-900">Curated Matches</h1>
          </div>
          <div className="flex items-center gap-3">
            <input
              type="number"
              min="1"
              max="20"
              value={topK}
              onChange={(event) => setTopK(Number(event.target.value) || 1)}
              className="w-28 rounded-xl border border-slate-200 px-4 py-2 text-sm focus:border-indigo-500 focus:outline-none"
            />
            <Button onClick={fetchMatches} disabled={loading} className="rounded-xl bg-indigo-600 px-4 py-2 text-sm font-semibold shadow">
              {loading ? 'Syncing...' : 'Refresh'}
              <RefreshCw className="ml-2 h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              onClick={() => navigate('/investor-dashboard')}
              className="rounded-xl border-slate-300 px-4 py-2 text-sm font-semibold"
            >
              <ArrowLeft className="mr-2 h-4 w-4" />
              Dashboard
            </Button>
          </div>
        </div>

        {error && (
          <Card className="border-red-200 bg-red-50">
            <CardContent className="p-4 text-sm text-red-700">{error}</CardContent>
          </Card>
        )}

        {loading ? (
          <Card className="border-slate-200">
            <CardContent className="p-10 text-center text-slate-500">Loading personalized matches…</CardContent>
          </Card>
        ) : (
          <>
            <Card className="border-slate-200">
              <CardHeader className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                <div className="flex items-center gap-3">
                  <div className="h-12 w-12 rounded-2xl bg-gradient-to-br from-[#1E3A8A] to-[#4F46E5] text-white flex items-center justify-center">
                    <Brain className="h-6 w-6" />
                  </div>
                  <div>
                    <CardTitle className="text-2xl text-slate-900">
                      {queryInvestor?.fullName || 'Investor'}
                    </CardTitle>
                    <p className="text-sm text-slate-500">{queryInvestor?.profession || 'Investor'}</p>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4 text-sm text-slate-600">
                  <div>
                    <p className="text-xs uppercase tracking-wide text-slate-400">Available Capital</p>
                    <p className="font-semibold text-slate-900">{formatCurrency(queryInvestor?.availableCapital)}</p>
                  </div>
                  <div>
                    <p className="text-xs uppercase tracking-wide text-slate-400">Expected ROI</p>
                    <p className="font-semibold text-slate-900">{queryInvestor?.expectedROI ? `${queryInvestor.expectedROI}%` : '—'}</p>
                  </div>
                  <div>
                    <p className="text-xs uppercase tracking-wide text-slate-400">Risk Appetite</p>
                    <p className="font-semibold text-slate-900 capitalize">{queryInvestor?.riskAppetite || '—'}</p>
                  </div>
                  <div>
                    <p className="text-xs uppercase tracking-wide text-slate-400">Locations</p>
                    <p className="font-semibold text-slate-900">
                      {queryInvestor?.preferredLocations?.length ? queryInvestor.preferredLocations.join(', ') : 'Not shared'}
                    </p>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  {profileStats.map((stat) => (
                    <div key={stat.label} className="rounded-2xl border border-slate-100 bg-white p-3">
                      <p className="text-xs text-slate-500">{stat.label}</p>
                      <p className="text-base font-semibold text-slate-900">{stat.value}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <section className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500">Similarity engine output</p>
                  <h2 className="text-2xl font-bold text-slate-900">
                    {matches.length ? `Top ${matches.length} Co-Investor Matches` : 'No matches yet'}
                  </h2>
                </div>
                <Badge className="rounded-full bg-slate-900 text-white">
                  {data?.totalCandidates || 0} candidates scanned
                </Badge>
              </div>

              {!matches.length ? (
                <Card className="border-dashed border-slate-300">
                  <CardContent className="flex flex-col items-center justify-center gap-4 py-12 text-center text-slate-500">
                    <Users className="h-12 w-12 text-slate-400" />
                    <p>No compatible investors were found. Update your profile or try again later.</p>
                  </CardContent>
                </Card>
              ) : (
                <div className="grid gap-4 lg:grid-cols-2">
                  {matches.map((match, index) => {
                    const quality = getMatchQuality(match.similarityScore)
                    const blockA = match.block_a || {}
                    const blockB = match.block_b || {}
                    const matchPercent = scoreToPercent(match.similarityScore)

                    return (
                      <Card
                        key={match.userId || index}
                        role="button"
                        tabIndex={0}
                        onClick={() => handleOpenMatch(match)}
                        className="border border-transparent bg-white/95 shadow-sm ring-1 ring-slate-100 transition-all hover:-translate-y-1 hover:shadow-xl focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500"
                      >
                        <CardContent className="p-6 space-y-5">
                          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-100 pb-4">
                            <div className="flex items-center gap-4">
                              <div className="h-14 w-14 rounded-2xl bg-gradient-to-br from-[#4F46E5] to-[#7C3AED] text-white flex items-center justify-center shadow-inner">
                                <div className="text-left">
                                  <p className="text-xs uppercase tracking-wide opacity-70">Rank</p>
                                  <p className="text-xl font-black leading-5">{index + 1}</p>
                                </div>
                              </div>
                              <div>
                                <p className="text-xs uppercase tracking-wide text-slate-400">Co-Investor</p>
                                <h3 className="text-lg font-semibold text-slate-900">{match.fullName || 'Investor'}</h3>
                                <p className="text-sm text-slate-500">{match.profession || 'Private Investor'}</p>
                              </div>
                            </div>
                            <div className="text-right">
                              <Badge className={`rounded-full px-4 py-1 text-sm font-semibold ${quality.tone}`}>
                                {quality.label} Match
                              </Badge>
                              <p className="text-xs text-slate-500">
                                {matchPercent !== null ? `${matchPercent}% alignment` : 'Score pending'}
                              </p>
                            </div>
                          </div>

                          <div className="grid gap-4 md:grid-cols-4">
                            <div className="rounded-2xl border border-slate-100 p-3">
                              <p className="text-xs text-slate-500 flex items-center gap-1">
                                <DollarSign className="h-3.5 w-3.5" /> Capital Band
                              </p>
                              <p className="text-base font-semibold text-slate-900">{blockB.capital_band ?? '—'}</p>
                            </div>
                            <div className="rounded-2xl border border-slate-100 p-3">
                              <p className="text-xs text-slate-500 flex items-center gap-1">
                                <Target className="h-3.5 w-3.5" /> Expected ROI
                              </p>
                              <p className="text-base font-semibold text-slate-900 capitalize">{blockB.expected_roi_band || '—'}</p>
                            </div>
                            <div className="rounded-2xl border border-slate-100 p-3">
                              <p className="text-xs text-slate-500 flex items-center gap-1">
                                <Clock3 className="h-3.5 w-3.5" /> Holding Period
                              </p>
                              <p className="text-base font-semibold text-slate-900 capitalize">{blockB.holding_period_band || '—'}</p>
                            </div>
                            <div className="rounded-2xl border border-slate-100 p-3">
                              <p className="text-xs text-slate-500 flex items-center gap-1">
                                <ShieldCheck className="h-3.5 w-3.5" /> Risk Appetite
                              </p>
                              <p className="text-base font-semibold text-slate-900 capitalize">{match.riskAppetite || '—'}</p>
                            </div>
                          </div>

                          <div className="mt-4 grid gap-4 md:grid-cols-3">
                            <div className="rounded-2xl border border-slate-100 p-3">
                              <p className="text-xs text-slate-500 flex items-center gap-1">
                                <Users className="h-3.5 w-3.5" /> Collaboration
                              </p>
                              <p className="text-base font-semibold text-slate-900">{blockA.collaboration_comfort_score?.toFixed?.(1) ?? '—'}</p>
                            </div>
                            <div className="rounded-2xl border border-slate-100 p-3">
                              <p className="text-xs text-slate-500 flex items-center gap-1">
                                <Brain className="h-3.5 w-3.5" /> Conviction
                              </p>
                              <p className="text-base font-semibold text-slate-900">{blockA.real_estate_conviction_score?.toFixed?.(1) ?? '—'}</p>
                            </div>
                            <div className="rounded-2xl border border-slate-100 p-3">
                              <p className="text-xs text-slate-500 flex items-center gap-1">
                                <MapPin className="h-3.5 w-3.5" /> Preferred Cities
                              </p>
                              <p className="text-base font-semibold text-slate-900">
                                {match.preferredLocations?.length ? match.preferredLocations.join(', ') : 'Open to explore'}
                              </p>
                            </div>
                          </div>

                          <div className="flex items-center justify-between pt-2 text-sm text-slate-500">
                            <p>
                              Score {match.similarityScore?.toFixed?.(3) ?? '0.000'} • {match.experienceYears ?? 0} yrs experience
                            </p>
                            <Button
                              variant="ghost"
                              className="text-indigo-600 hover:bg-indigo-50 hover:text-indigo-700"
                              onClick={(event) => {
                                event.stopPropagation()
                                handleOpenMatch(match)
                              }}
                            >
                              View Investor <ArrowUpRight className="ml-2 h-4 w-4" />
                            </Button>
                          </div>
                        </CardContent>
                      </Card>
                    )
                  })}
                </div>
              )}
            </section>
          </>
        )}
      </div>

      <Footer />
    </div>
  )
}
