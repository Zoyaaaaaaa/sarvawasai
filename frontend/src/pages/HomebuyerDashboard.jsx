import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Bell, User, Home, TrendingUp, DollarSign, MapPin, Brain, ShieldCheck, Users, FileSignature, Scale } from 'lucide-react'
import Navbar from '@/components/Navbar.jsx'
import Footer from '@/components/Footer.jsx'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import DashboardFeatureCard from '@/components/DashboardFeatureCard.jsx'
import { apiUrl } from '@/lib/api.js'

export default function HomebuyerDashboard() {
  const navigate = useNavigate()
  const [profile, setProfile] = useState(null)
  const [notifications, setNotifications] = useState([])
  const [loading, setLoading] = useState(true)
  const [showNotifications, setShowNotifications] = useState(false)
  const [matches, setMatches] = useState([])

  // Get userId from localStorage
  const userId = localStorage.getItem('userId')
  const hasValidUserId = Boolean(userId && userId !== 'null' && userId !== 'undefined')

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!hasValidUserId) {
      navigate('/login')
    }
  }, [hasValidUserId, navigate])

  const riskMap = {
    low: 0,
    medium: 1,
    moderate: 1,
    high: 2
  }

  useEffect(() => {
    if (!hasValidUserId) return
    fetchProfile()
    fetchNotifications()
  }, [hasValidUserId])

  const fetchProfile = async () => {
    try {

      const response = await fetch(apiUrl(`/users/profile/${userId}`))
      const data = await response.json()

      setProfile(data)

      const maxBudget = data?.profile?.budgetRange?.max
      const city =
        data?.profile?.preferredCities?.[0] ||
        data?.profile?.preferredLocalities?.[0] ||
        data?.profile?.preferredLocations?.[0]
      const riskLevel = data?.profile?.riskToleranceLevel?.toLowerCase()

      if (!maxBudget || !city) {
        console.log("Profile incomplete, skipping recommendations")
        return
      }

      const buyerInput = {
        buyerBudgetMax: maxBudget,
        buyerRisk: riskMap[riskLevel] ?? 1,
        location: city
      }

      const recResponse = await fetch(apiUrl('/api/recommend'), {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(buyerInput)
      })

      if (!recResponse.ok) {
        throw new Error('Failed to fetch investor recommendations')
      }

      const recData = await recResponse.json()

      setMatches(recData.recommendations || [])

    } catch (error) {
      console.error("Error fetching profile:", error)
    } finally {
      setLoading(false)
    }
  }

  const fetchNotifications = async () => {
    try {
      const response = await fetch(apiUrl(`/users/notifications/${userId}`))
      const data = await response.json()
      setNotifications(data.notifications || [])
    } catch (error) {
      console.error('Error fetching notifications:', error)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="body-lg">Loading...</div>
      </div>
    )
  }

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0
    }).format(amount)
  }

  const unreadCount = notifications.filter(n => !n.read).length
  const profileData = profile?.profile || {}
  const profession = profile?.user?.profession || profileData?.profession || 'Profession'
  const localities =
    profileData.preferredLocalities ||
    profileData.preferredCities ||
    profileData.preferredLocations ||
    []
  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,rgba(88,28,135,0.07),transparent_40%),linear-gradient(180deg,#F8FAFC_0%,#FFFFFF_45%,#F8FAFC_100%)]">
      <Navbar />

      {/* Header */}
      <header className="relative bg-white/70 backdrop-blur-sm border-b border-slate-200/70 shadow-sm">
        <div className="absolute -top-24 -right-16 h-64 w-64 rounded-full bg-[#581C87]/10 blur-3xl"></div>
        <div className="absolute -bottom-24 -left-16 h-64 w-64 rounded-full bg-[#1E3A8A]/10 blur-3xl"></div>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="relative flex justify-between items-center">
            <div className="flex items-center gap-4">
              <div className="h-14 w-14 bg-gradient-to-br from-[#581C87] to-[#1E3A8A] rounded-full flex items-center justify-center flex-shrink-0">
                <User className="h-7 w-7 text-white" />
              </div>
              <div>
                <p className="inline-flex items-center rounded-full border border-[#581C87]/20 bg-[#581C87]/5 px-3 py-1 text-xs font-semibold tracking-wide text-[#581C87] mb-2">
                  Homebuyer Console
                </p>
                <h1 className="text-2xl font-bold text-gray-900 mb-0">
                  {profile?.user?.fullName || 'Homebuyer'}
                </h1>
                <p className="text-sm text-gray-500 mt-1">
                  {profession}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="relative">
                <button
                  onClick={() => setShowNotifications(!showNotifications)}
                  className="relative p-2 text-gray-600 hover:text-[#581C87] rounded-lg focus-visible transition-all duration-200"
                  aria-label="Notifications"
                >
                  <Bell className="h-6 w-6" />
                  {unreadCount > 0 && (
                    <span className="absolute top-0 right-0 inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none text-white transform translate-x-1/2 -translate-y-1/2 bg-[#581C87] rounded-full">
                      {unreadCount}
                    </span>
                  )}
                </button>

              </div>
            </div>
          </div>

          {showNotifications && (
            <div className="absolute right-4 top-20 z-50 w-80 rounded-2xl border border-gray-200 bg-white shadow-xl">
              <div className="p-4 border-b border-gray-100">
                <h3 className="font-semibold text-gray-900">Notifications</h3>
              </div>
              <div className="max-h-96 overflow-y-auto">
                {notifications.length === 0 ? (
                  <div className="p-4 text-center text-gray-500">
                    No notifications
                  </div>
                ) : (
                  notifications.map((notif) => (
                    <div
                      key={notif.id}
                      className={`p-4 border-b border-gray-100 transition-colors hover:bg-gray-50 ${!notif.read ? 'bg-purple-50' : ''}`}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex-1">
                          <p className="text-sm font-semibold text-gray-900">{notif.title}</p>
                          <p className="mt-1 text-xs text-gray-600">{notif.message}</p>
                        </div>
                        {!notif.read && (
                          <span className="mt-2 h-2 w-2 flex-shrink-0 rounded-full bg-[#581C87]"></span>
                        )}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>
      </header>

      {/* Main Content */}
      <section className="py-8 md:py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Profile Stats */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-12">
            <Card className="rounded-2xl border border-slate-200/80 bg-white/90 shadow-sm hover:shadow-lg transition-all">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Monthly Income</p>
                    <p className="text-3xl font-bold text-[#581C87]">
                      {formatCurrency(profile?.profile?.monthlyIncome || 0)}
                    </p>
                  </div>
                  <div className="h-14 w-14 bg-purple-100 rounded-xl flex items-center justify-center">
                    <DollarSign className="h-7 w-7 text-[#581C87]" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="rounded-2xl border border-slate-200/80 bg-white/90 shadow-sm hover:shadow-lg transition-all">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Budget Range</p>
                    <p className="text-2xl font-bold text-[#1E3A8A]">
                      {formatCurrency(profile?.profile?.budgetRange?.min || 0)} - {formatCurrency(profile?.profile?.budgetRange?.max || 0)}
                    </p>
                  </div>
                  <div className="h-14 w-14 bg-blue-100 rounded-xl flex items-center justify-center">
                    <Home className="h-7 w-7 text-[#1E3A8A]" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <div className="bg-white/90 rounded-2xl shadow-sm border border-slate-200/80 p-6 hover:shadow-md transition-all md:col-span-2">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Property Type</p>
                  <p className="text-2xl font-bold text-gray-900 capitalize">
                    {profile?.profile?.propertyType || 'Apartment'}
                  </p>
                </div>
                <div className="h-12 w-12 bg-amber-100 rounded-full flex items-center justify-center">
                  <MapPin className="h-6 w-6 text-amber-600" />
                </div>
              </div>
            </div>
          </div>

          {/* Smart Investor Matches */}
          <div className="bg-white/90 rounded-2xl border border-slate-200/80 p-6 shadow-sm hover:shadow-md transition-all mb-10">

            <h2 className="text-xl font-bold text-gray-900 mb-6">
              AI Investor Matches
            </h2>

            {matches.length === 0 ? (
              <p className="text-gray-600">
                Complete your profile to see investor matches.
              </p>
            ) : (

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">

                {matches.map((inv, i) => (

                  <div key={i} className="border border-gray-200 rounded-lg p-5 hover:shadow-md hover:border-[#581C87]/20 transition-all cursor-pointer">

                    <h3 className="font-bold text-lg text-[#581C87] mb-3">
                      {inv.label}
                    </h3>

                    <p className="text-sm text-gray-600 mb-2">
                      <b className="text-gray-700">Investor ID:</b> {inv.investorId}
                    </p>

                    <p className="text-sm text-gray-600">
                      Profession: {inv.profession}
                    </p>

                    <p className="text-sm text-gray-600">
                      Risk Appetite: {inv.riskAppetite}
                    </p>

                    <p className="text-sm text-gray-600">
                      Investment Capacity: {formatCurrency(inv.budget)}
                    </p>

                    <p className="text-sm font-semibold mt-2">
                      Match Score: {(inv.score * 100).toFixed(1)}%
                    </p>

                  </div>

                ))}

              </div>

            )}

          </div>

          {/* Feature Cards */}
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-slate-900">Buyer Tools</h2>
            <p className="text-sm text-slate-600 mt-1">Everything you need from investor support to legal and compliance workflows.</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-12">
            {/* Investor Marketplace - Step-Up Feature */}
            {/* <DashboardFeatureCard
            title="Investor Marketplace"
            description="Access the Step-Up feature to connect with investors and unlock down-payment support"
            actionLabel="Open Step-Up"
            icon={Users}
            onClick={() => navigate('/stepup')}
            variant="indigo"
          />
           */}
            <DashboardFeatureCard
              title="Step-Up"
              description="Take your first step to homeownership with guided assistance and buyer-ready planning"
              actionLabel="Start Journey"
              icon={TrendingUp}
              onClick={() => navigate('/stepup2')}
              variant="plum"
            />
            
            {/* House Scheme Finder */}
            <DashboardFeatureCard
              title="House Scheme Finder"
              description="Discover government housing schemes and subsidies tailored for first-time buyers"
              actionLabel="Find Schemes"
              icon={Home}
              onClick={() => navigate('/housing-schemes')}
              variant="indigo"
            />

            {/* RERA Verification */}
            <DashboardFeatureCard
              title="RERA Verification"
              description="Verify RERA registration and ensure legal compliance for your property"
              actionLabel="Verify Property"
              icon={ShieldCheck}
              onClick={() => navigate('/rera-verification')}
              variant="slate"
            />

            {/* House Prediction */}
            <DashboardFeatureCard
              title="Price Prediction"
              description="Get AI-powered price predictions and find the perfect property within your budget"
              actionLabel="Predict Prices"
              icon={Brain}
              onClick={() => navigate('/house-prediction')}
              variant="amber"
            />

            {/* Buyer Agreement */}
            <DashboardFeatureCard
              title="Buyer Agreement"
              description="Generate and sign your buyer agreement with investor and property details"
              actionLabel="Open Agreement"
              icon={FileSignature}
              onClick={() => navigate('/buyer-agreement')}
              variant="slate"
            />

            {/* Legal Document Analysis */}
            <DashboardFeatureCard
              title="Legal Document Analysis"
              description="Analyze property-related documents with AI and get insights on Indian real estate laws"
              actionLabel="Analyze Documents"
              icon={Scale}
              onClick={() => navigate('/legal-analysis')}
              variant="emerald"
            />
          </div>

          {/* Profile Information */}
          <Card className="rounded-2xl border border-slate-200/80 bg-white/90 shadow-sm hover:shadow-md transition-shadow mt-10">
            <CardHeader className="border-b border-gray-100 px-6 py-5">
              <CardTitle className="text-xl font-bold text-gray-900">Profile Information</CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div className="space-y-1">
                  <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Email</p>
                  <p className="text-sm font-medium text-gray-900">{profile?.user?.email}</p>
                </div>
                <div className="space-y-1">
                  <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Phone</p>
                  <p className="text-sm font-medium text-gray-900">{profile?.user?.phone}</p>
                </div>
                <div className="space-y-1">
                  <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Preferred Locality</p>
                  <p className="text-sm font-medium text-gray-900">
                    {localities.join(', ') || 'Not specified'}
                  </p>
                </div>
                <div className="space-y-1">
                  <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Risk Tolerance</p>
                  <p className="text-sm font-medium text-gray-900 capitalize">
                    {profile?.profile?.riskToleranceLevel || 'Moderate'}
                  </p>
                </div>
                <div className="space-y-1">
                  <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Experience</p>
                  <p className="text-sm font-medium text-gray-900">
                    {profile?.profile?.investmentExperienceYears || 0} years
                  </p>
                </div>
                <div className="space-y-1">
                  <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Trust Score</p>
                  <p className="text-sm font-medium text-[#581C87] font-bold">
                    {profile?.profile?.trustScore || 0}/100
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </section>

      <Footer />
    </div>
  )
}
