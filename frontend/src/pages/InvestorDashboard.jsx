import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { TrendingUp, Users, DollarSign, Home, ShieldCheck, Brain, FileSignature, Scale } from 'lucide-react'
import Navbar from '@/components/Navbar.jsx'
import Footer from '@/components/Footer.jsx'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import DashboardFeatureCard from '@/components/DashboardFeatureCard.jsx'
import { apiUrl } from '@/lib/api.js'

export default function InvestorDashboard() {
  const navigate = useNavigate()
  const [profile, setProfile] = useState(null)
  const [notifications, setNotifications] = useState([])
  const [loading, setLoading] = useState(true)
  const [showNotifications, setShowNotifications] = useState(false)

  // Get userId from localStorage
  const userId = localStorage.getItem('userId')
  const hasValidUserId = Boolean(userId && userId !== 'null' && userId !== 'undefined')
  
  // Redirect to login if not authenticated
  useEffect(() => {
    if (!hasValidUserId) {
      navigate('/login')
    }
  }, [hasValidUserId, navigate])

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
    } catch (error) {
      console.error('Error fetching profile:', error)
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
  const isProfileComplete = Boolean(
    profileData.availableCapital &&
    profileData.expectedROI !== undefined &&
    profileData.experienceYears !== undefined &&
    Array.isArray(profileData.preferredLocations) &&
    profileData.preferredLocations.length > 0
  )
  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,rgba(30,58,138,0.06),transparent_45%),linear-gradient(180deg,#F8FAFC_0%,#FFFFFF_45%,#F8FAFC_100%)] font-inter">
      <Navbar />

      {/* Hero Section */}
      <section className="relative overflow-hidden bg-white/70 backdrop-blur-sm border-b border-slate-200/70">
        <div className="absolute -top-24 -right-20 h-64 w-64 rounded-full bg-[#1E3A8A]/10 blur-3xl"></div>
        <div className="absolute -bottom-24 -left-12 h-64 w-64 rounded-full bg-[#581C87]/10 blur-3xl"></div>
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 md:py-12">
          <div className="flex flex-col gap-6 md:flex-row md:justify-between md:items-start">
            <div className="flex-1">
              <p className="inline-flex items-center rounded-full border border-[#581C87]/20 bg-[#581C87]/5 px-3 py-1 text-xs font-semibold tracking-wide text-[#581C87] mb-4">
                Investor Console
              </p>
              <h1 className="text-3xl md:text-4xl lg:text-5xl font-bold text-gray-900 mb-3 leading-tight">
                Welcome Back, <span className="bg-gradient-to-r from-[#581C87] to-[#1E3A8A] bg-clip-text text-transparent">{profile?.user?.fullName || 'Investor'}</span>
              </h1>
              <p className="text-base text-gray-600 mb-1">
                Professional Investor • {profile?.profile?.experienceYears || 0} years experience
              </p>
              <p className="text-sm text-slate-500 mt-2">Unread notifications: {unreadCount}</p>
            </div>
          </div>
        </div>
      </section>

      {/* Main Content */}
      <section className="py-8 md:py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Profile Stats */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-12">
            <Card className="rounded-2xl border border-slate-200/80 bg-white/90 shadow-sm hover:shadow-lg transition-all">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Available Capital</p>
                    <p className="text-3xl font-bold text-[#581C87]">
                      {formatCurrency(profile?.profile?.availableCapital || 0)}
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
                    <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Expected ROI</p>
                    <p className="text-3xl font-bold text-[#1E3A8A]">
                      {profile?.profile?.expectedROI || 0}%
                    </p>
                  </div>
                  <div className="h-14 w-14 bg-blue-100 rounded-xl flex items-center justify-center">
                    <TrendingUp className="h-7 w-7 text-[#1E3A8A]" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="rounded-2xl border border-slate-200/80 bg-white/90 shadow-sm hover:shadow-lg transition-all md:col-span-2">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Risk Appetite</p>
                    <p className="text-2xl font-bold text-gray-900 capitalize">
                      {profile?.profile?.riskAppetite || 'Moderate'}
                    </p>
                  </div>
                  <div className="h-14 w-14 bg-amber-100 rounded-xl flex items-center justify-center">
                    <Brain className="h-7 w-7 text-amber-600" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Feature Cards */}
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-slate-900">Tools & Opportunities</h2>
            <p className="text-sm text-slate-600 mt-1">Explore AI insights, legal tools, and investment pathways.</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-12">
            {/* Co-Vest */}
            <DashboardFeatureCard
              title="Co-Vest"
              description="Find matching investors and co-invest in properties using ML-powered similarity matching"
              actionLabel="Explore Co-Investments"
              icon={Users}
              onClick={() => userId && navigate(`/matches/${userId}`)}
              variant="indigo"
            />

            {/* Step-Up */}
            <DashboardFeatureCard
              title="Step-Up"
              description="Support homebuyers with down payment assistance and earn attractive returns"
              actionLabel="View Opportunities"
              icon={TrendingUp}
              onClick={() => navigate('/stepup2')}
              variant="plum"
            />

            {/* Housing Schemes */}
            <DashboardFeatureCard
              title="Housing Schemes"
              description="Explore government housing schemes and understand their benefits for your investments"
              actionLabel="Explore Schemes"
              icon={Home}
              onClick={() => navigate('/housing-schemes')}
              variant="indigo"
            />

            {/* RERA Verification */}
            <DashboardFeatureCard
              title="RERA Verification"
              description="Verify RERA registration and ensure legal compliance for your property investments"
              actionLabel="Verify Property"
              icon={ShieldCheck}
              onClick={() => navigate('/rera-verification')}
              variant="slate"
            />

            {/* House Prediction */}
            <DashboardFeatureCard
              title="Price Prediction"
              description="Get AI-powered price predictions and investment insights for properties"
              actionLabel="Predict Prices"
              icon={Brain}
              onClick={() => navigate('/house-prediction')}
              variant="amber"
            />

            <DashboardFeatureCard
              title="Investor Agreement"
              description="Create and review multi-investor legal agreements for partnered deals"
              actionLabel="Open Agreement"
              icon={FileSignature}
              onClick={() => navigate('/investor-agreement')}
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
              {!isProfileComplete && (
                <div className="mb-6 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
                  Complete your profile to unlock better investor matching and personalized recommendations.
                </div>
              )}
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
                  <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Experience</p>
                  <p className="text-sm font-medium text-gray-900">{profile?.profile?.experienceYears || 0} years</p>
                </div>
                <div className="space-y-1">
                  <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Preferred Locations</p>
                  <p className="text-sm font-medium text-gray-900">
                    {profile?.profile?.preferredLocations?.join(', ') || 'Not specified'}
                  </p>
                </div>
                <div className="space-y-1">
                  <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Holding Period</p>
                  <p className="text-sm font-medium text-gray-900">{profile?.profile?.maxHoldingPeriodMonths || 0} months</p>
                </div>
                <div className="space-y-1">
                  <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Accreditation Level</p>
                  <p className="text-sm font-medium text-[#581C87] font-bold capitalize">
                    {profile?.profile?.investorAccreditationLevel || 'Basic'}
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
