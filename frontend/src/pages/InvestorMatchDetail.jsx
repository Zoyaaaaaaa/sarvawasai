import { useEffect, useMemo, useState } from 'react'
import { useLocation, useNavigate, useParams } from 'react-router-dom'
import Navbar from '@/components/Navbar.jsx'
import Footer from '@/components/Footer.jsx'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Button } from '@/components/ui/button.jsx'
import {
  ArrowLeft,
  Mail,
  Phone,
  MapPin,
  Target,
  DollarSign,
  Clock3,
  ShieldCheck,
  Users,
  Brain,
  Sparkles
} from 'lucide-react'
import { apiUrl } from '@/lib/api.js'

const PROFILE_API_BASE = apiUrl('')

const formatCurrency = (value) => {
  if (value === null || value === undefined) return '—'
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0
  }).format(value)
}

const scoreToPercent = (score) => {
  if (typeof score !== 'number') return null
  const normalized = 1 / (1 + Math.exp(-score))
  return Math.round(normalized * 100)
}

const normalizeMatchPayload = (raw) => {
  if (!raw) return null
  return {
    ...raw,
    block_a: raw.block_a || raw.profile?.block_a || {},
    block_b: raw.block_b || raw.profile?.block_b || {},
    block_c: raw.block_c || raw.profile?.block_c || {},
    preferredLocations: raw.preferredLocations || raw.profile?.preferredLocations || [],
    preferredInvestmentType: raw.preferredInvestmentType || raw.profile?.preferredInvestmentType || [],
    availableCapital: raw.availableCapital ?? raw.profile?.availableCapital ?? null,
    expectedROI: raw.expectedROI ?? raw.profile?.expectedROI ?? null,
    maxHoldingPeriodMonths: raw.maxHoldingPeriodMonths ?? raw.profile?.maxHoldingPeriodMonths ?? null,
    experienceYears: raw.experienceYears ?? raw.profile?.experienceYears ?? null,
    riskAppetite: raw.riskAppetite ?? raw.profile?.riskAppetite ?? null,
    investorAccreditationLevel: raw.investorAccreditationLevel ?? raw.profile?.investorAccreditationLevel ?? null
  }
}

export default function InvestorMatchDetail() {
  const { state } = useLocation()
  const navigate = useNavigate()
  const { matchId } = useParams()

  const [matchData, setMatchData] = useState(() => normalizeMatchPayload(state?.match))
  const [queryInvestor] = useState(() => state?.queryInvestor || null)
  const [querySummary] = useState(() => state?.querySummary || null)
  const [loading, setLoading] = useState(!state?.match)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!matchData && matchId) {
      const fetchProfile = async () => {
        try {
          setLoading(true)
          setError(null)
          const response = await fetch(`${PROFILE_API_BASE}/users/profile/${matchId}`)
          if (!response.ok) {
            const payload = await response.json().catch(() => ({}))
            throw new Error(payload.detail || 'Unable to load investor profile')
          }
          const payload = await response.json()
          const normalized = normalizeMatchPayload({
            userId: payload.user?._id,
            fullName: payload.user?.fullName,
            profession: payload.user?.profession,
            email: payload.user?.email,
            phone: payload.user?.phone,
            profile: payload.profile
          })
          setMatchData(normalized)
        } catch (err) {
          setError(err.message)
        } finally {
          setLoading(false)
        }
      }

      fetchProfile()
    }
  }, [matchData, matchId])

  const blockA = matchData?.block_a || {}
  const blockB = matchData?.block_b || {}
  const blockC = matchData?.block_c || {}
  const compatibilityPercent = scoreToPercent(matchData?.similarityScore)

  const behavioralTraits = useMemo(() => ([
    { label: 'Risk Orientation', value: blockA.risk_orientation_score },
    { label: 'Collaboration Comfort', value: blockA.collaboration_comfort_score },
    { label: 'Control Preference', value: blockA.control_preference_score },
    { label: 'RE Conviction', value: blockA.real_estate_conviction_score }
  ]), [blockA])

  const compatibilityRows = useMemo(() => {
    if (!querySummary) return []
    return [
      { label: 'Capital Band', mine: querySummary.capital_band, theirs: blockB.capital_band },
      { label: 'Expected ROI', mine: querySummary.expected_roi_band, theirs: blockB.expected_roi_band },
      { label: 'Holding Period', mine: querySummary.holding_period_band, theirs: blockB.holding_period_band },
      { label: 'City Tier', mine: querySummary.city_tier, theirs: blockB.city_tier }
    ]
  }, [blockB, querySummary])

  const handleBack = () => {
    navigate(-1)
  }

  return (
    <div className="min-h-screen bg-[#F9FAFB] font-inter">
      <Navbar />

      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
        <div className="flex items-center gap-3">
          <Button variant="ghost" onClick={handleBack} className="text-slate-600 hover:text-slate-900">
            <ArrowLeft className="mr-2 h-4 w-4" /> Back to matches
          </Button>
          {matchData?.investorAccreditationLevel && (
            <Badge className="bg-indigo-100 text-indigo-700">
              {matchData.investorAccreditationLevel} investor
            </Badge>
          )}
        </div>

        {error && (
          <Card className="border-red-200 bg-red-50">
            <CardContent className="p-4 text-sm text-red-700">{error}</CardContent>
          </Card>
        )}

        {loading ? (
          <Card className="border-slate-200">
            <CardContent className="p-10 text-center text-slate-500">Loading investor profile…</CardContent>
          </Card>
        ) : matchData ? (
          <>
            <Card className="overflow-hidden border-none shadow-xl">
              <div className="bg-gradient-to-r from-[#581C87] via-[#1E3A8A] to-[#4F46E5] p-8 text-white">
                <div className="flex flex-wrap items-start justify-between gap-6">
                  <div>
                    <p className="text-sm uppercase tracking-[0.3em] text-white/70">Co-Vest Partner</p>
                    <h1 className="text-4xl font-bold mt-2">{matchData.fullName || 'Investor'}</h1>
                    <p className="text-lg text-indigo-100">{matchData.profession || 'Private investor'}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-white/70">Similarity Index</p>
                    <p className="text-5xl font-black leading-tight">{compatibilityPercent ?? '—'}<span className="text-2xl font-medium">%</span></p>
                    <p className="text-xs text-white/60">Raw score {matchData.similarityScore?.toFixed?.(3) ?? '—'}</p>
                  </div>
                </div>
                <div className="mt-8 grid gap-4 md:grid-cols-3 text-sm text-indigo-100">
                  <div className="flex items-center gap-3">
                    <Mail className="h-4 w-4" /> {matchData.email || 'Email on request'}
                  </div>
                  <div className="flex items-center gap-3">
                    <Phone className="h-4 w-4" /> {matchData.phone || 'Phone on request'}
                  </div>
                  <div className="flex items-center gap-3">
                    <MapPin className="h-4 w-4" />
                    {matchData.preferredLocations?.length ? matchData.preferredLocations.slice(0, 3).join(', ') : 'Open to explore'}
                  </div>
                </div>
              </div>
            </Card>

            <div className="grid gap-6 md:grid-cols-3">
              <Card className="md:col-span-2">
                <CardHeader>
                  <CardTitle className="text-slate-900">Investment Snapshot</CardTitle>
                </CardHeader>
                <CardContent className="grid gap-4 sm:grid-cols-2">
                  <div className="rounded-2xl border border-slate-100 p-4">
                    <p className="text-xs uppercase tracking-wide text-slate-400">Capital Ready</p>
                    <p className="text-2xl font-semibold text-slate-900">{formatCurrency(matchData.availableCapital)}</p>
                  </div>
                  <div className="rounded-2xl border border-slate-100 p-4">
                    <p className="text-xs uppercase tracking-wide text-slate-400">Expected ROI</p>
                    <p className="text-2xl font-semibold text-slate-900">{matchData.expectedROI ? `${matchData.expectedROI}%` : '—'}</p>
                  </div>
                  <div className="rounded-2xl border border-slate-100 p-4">
                    <p className="text-xs uppercase tracking-wide text-slate-400">Holding Horizon</p>
                    <p className="text-2xl font-semibold text-slate-900">{blockB.holding_period_band || '—'}</p>
                  </div>
                  <div className="rounded-2xl border border-slate-100 p-4">
                    <p className="text-xs uppercase tracking-wide text-slate-400">Experience</p>
                    <p className="text-2xl font-semibold text-slate-900">{matchData.experienceYears ?? 0} yrs</p>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-slate-900 flex items-center gap-2">
                    <ShieldCheck className="h-5 w-5 text-indigo-500" /> Trust Signals
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3 text-sm text-slate-600">
                  <p>Risk Appetite: <span className="font-semibold capitalize text-slate-900">{matchData.riskAppetite || '—'}</span></p>
                  <p>City Tier Focus: <span className="font-semibold text-slate-900">{blockB.city_tier || '—'}</span></p>
                  <p>Ticket Size Stability: <span className="font-semibold text-slate-900">{blockB.ticket_size_stability?.toFixed?.(2) ?? '—'}</span></p>
                  <p>Behavioral Consistency: <span className="font-semibold text-slate-900">{blockC.behavioral_consistency_score?.toFixed?.(2) ?? '—'}</span></p>
                </CardContent>
              </Card>
            </div>

            <div className="grid gap-6 md:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle className="text-slate-900 flex items-center gap-2">
                    <Users className="h-5 w-5 text-indigo-500" /> Behavioral Profile
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {behavioralTraits.map((trait) => (
                    <div key={trait.label}>
                      <div className="flex items-center justify-between text-xs text-slate-500">
                        <span>{trait.label}</span>
                        <span>{trait.value !== undefined ? trait.value.toFixed(2) : '—'}</span>
                      </div>
                      <div className="h-2 rounded-full bg-slate-200">
                        <div
                          className="h-2 rounded-full bg-gradient-to-r from-[#1E3A8A] to-[#4F46E5]"
                          style={{ width: `${Math.min(1, Math.max(0, trait.value || 0)) * 100}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-slate-900 flex items-center gap-2">
                    <Brain className="h-5 w-5 text-indigo-500" /> Economic Alignment
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3 text-sm text-slate-600">
                  <p>Capital Band: <span className="font-semibold text-slate-900">{blockB.capital_band ?? '—'}</span></p>
                  <p>Capital Depth Index: <span className="font-semibold text-slate-900">{blockB.capital_depth_index?.toFixed?.(2) ?? '—'}</span></p>
                  <p>Capital Coverage Ratio: <span className="font-semibold text-slate-900">{blockB.capital_coverage_ratio?.toFixed?.(2) ?? '—'}</span></p>
                  <p>Preferred Vehicles: <span className="font-semibold text-slate-900">{matchData.preferredInvestmentType?.length ? matchData.preferredInvestmentType.join(', ') : 'Not specified'}</span></p>
                </CardContent>
              </Card>
            </div>

            {compatibilityRows.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-slate-900 flex items-center gap-2">
                    <Target className="h-5 w-5 text-indigo-500" /> Fit Versus Your Profile
                  </CardTitle>
                </CardHeader>
                <CardContent className="overflow-x-auto">
                  <table className="w-full text-sm text-slate-600">
                    <thead>
                      <tr className="text-left text-xs uppercase tracking-wide text-slate-400">
                        <th className="py-2">Dimension</th>
                        <th className="py-2">You</th>
                        <th className="py-2">Investor</th>
                      </tr>
                    </thead>
                    <tbody>
                      {compatibilityRows.map((row) => (
                        <tr key={row.label} className="border-t border-slate-100">
                          <td className="py-3 font-medium text-slate-900">{row.label}</td>
                          <td className="py-3 capitalize">{row.mine ?? '—'}</td>
                          <td className="py-3 capitalize">{row.theirs ?? '—'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </CardContent>
              </Card>
            )}

            <Card className="bg-white border-dashed">
              <CardContent className="flex flex-wrap items-center justify-between gap-4 py-6">
                <div>
                  <p className="text-sm text-slate-500">Next step</p>
                  <h3 className="text-xl font-semibold text-slate-900">Schedule a diligence call</h3>
                  <p className="text-sm text-slate-500">Share opportunity decks or invite the investor to your workspace.</p>
                </div>
                <Button className="bg-indigo-600 hover:bg-indigo-700">
                  <Sparkles className="mr-2 h-4 w-4" /> Express Interest
                </Button>
              </CardContent>
            </Card>
          </>
        ) : null}
      </div>

      <Footer />
    </div>
  )
}
