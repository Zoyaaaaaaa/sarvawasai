import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Loader2, Building2 } from 'lucide-react'
import Navbar from '@/components/Navbar.jsx'
import Footer from '@/components/Footer.jsx'
import { apiUrl } from '@/lib/api.js'

export default function ProfileManagement() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [profile, setProfile] = useState(null)
  const [fetchError, setFetchError] = useState(null)
  const userId = localStorage.getItem('userId')
  const hasValidUserId = Boolean(userId && userId !== 'null' && userId !== 'undefined')
  const userRole = localStorage.getItem('userRole')

  const [formData, setFormData] = useState({
    // Common fields
    phone: '',
    email: '',
    // Role-specific fields will be added based on userRole
  })

  useEffect(() => {
    if (!hasValidUserId) {
      navigate('/login')
      return
    }
    fetchProfile()
  }, [hasValidUserId, navigate])

  const fetchProfile = async () => {
    try {
      const response = await fetch(apiUrl(`/users/profile/${userId}`))
      const data = await response.json()
      setProfile(data)

      // Initialize form data based on role
      const baseData = {
        phone: data.user?.phone || '',
        email: data.user?.email || '',
      }

      if (userRole === 'investor') {
        setFormData({
          ...baseData,
          annualIncome: data.profile?.annualIncome || '',
          investmentCapital: data.profile?.investmentCapital || '',
          riskAppetite: data.profile?.riskAppetite || 'moderate',
          expectedROI: data.profile?.expectedROI || '',
          maxHoldingPeriodMonths: data.profile?.maxHoldingPeriodMonths || '',
          diversificationPreference: data.profile?.diversificationPreference || 'medium',
          investorAccreditationLevel: data.profile?.investorAccreditationLevel || 'basic',
          // ML features
          risk_orientation_score: data.profile?.risk_orientation_score || '',
          collaboration_comfort_score: data.profile?.collaboration_comfort_score || '',
          control_preference_score: data.profile?.control_preference_score || '',
          real_estate_conviction_score: data.profile?.real_estate_conviction_score || '',
          capital_band: data.profile?.capital_band || '',
          expected_roi_band: data.profile?.expected_roi_band || 'medium',
          holding_period_band: data.profile?.holding_period_band || 'medium',
          ticket_size_stability: data.profile?.ticket_size_stability || '',
          behavioral_consistency_score: data.profile?.behavioral_consistency_score || '',
          capital_coverage_ratio: data.profile?.capital_coverage_ratio || '',
          city_tier: data.profile?.city_tier || 2,
          deal_success_ratio: data.profile?.deal_success_ratio || '',
          avg_holding_duration: data.profile?.avg_holding_duration || '',
        })
      } else {
        // Homebuyer profile
        setFormData({
          ...baseData,
          employmentType: data.profile?.employmentType || '',
          creditScore: data.profile?.creditScore || '',
          downPaymentCapability: data.profile?.downPaymentCapability || '',
          loanRequired: data.profile?.loanRequired || false,
          preferredTenure: data.profile?.preferredTenure || '',
          coApplicant: data.profile?.coApplicant || false,
        })
      }
    } catch (error) {
      console.error('Error fetching profile:', error)
      setFetchError('Unable to load profile. Please login again or try later.')
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)

    try {
      const updateData = { ...formData }

      // Convert numeric fields
      if (userRole === 'investor') {
        updateData.annualIncome = parseFloat(formData.annualIncome) || 0
        updateData.investmentCapital = parseFloat(formData.investmentCapital) || 0
        updateData.expectedROI = parseFloat(formData.expectedROI) || 0
        updateData.maxHoldingPeriodMonths = parseInt(formData.maxHoldingPeriodMonths) || 0
        updateData.risk_orientation_score = parseFloat(formData.risk_orientation_score) || 0
        updateData.collaboration_comfort_score = parseFloat(formData.collaboration_comfort_score) || 0
        updateData.control_preference_score = parseFloat(formData.control_preference_score) || 0
        updateData.real_estate_conviction_score = parseFloat(formData.real_estate_conviction_score) || 0
        updateData.ticket_size_stability = parseFloat(formData.ticket_size_stability) || 0
        updateData.behavioral_consistency_score = parseFloat(formData.behavioral_consistency_score) || 0
        updateData.capital_coverage_ratio = parseFloat(formData.capital_coverage_ratio) || 0
        updateData.city_tier = parseInt(formData.city_tier) || 2
        updateData.deal_success_ratio = parseFloat(formData.deal_success_ratio) || 0
        updateData.avg_holding_duration = parseFloat(formData.avg_holding_duration) || 0
      } else {
        updateData.creditScore = parseInt(formData.creditScore) || 0
        updateData.downPaymentCapability = parseFloat(formData.downPaymentCapability) || 0
        updateData.preferredTenure = parseInt(formData.preferredTenure) || 0
      }

      const response = await fetch(apiUrl(`/users/profile/${userId}`), {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updateData),
      })

      if (response.ok) {
        // Mark notification as read
        await fetch(apiUrl(`/users/notifications/${userId}/dismiss/2`), {
          method: 'POST',
        })
        // Navigate to role-specific dashboard
        if (userRole === 'investor') {
          navigate('/investor-dashboard')
        } else {
          navigate('/homebuyer-dashboard')
        }
      } else {
        alert('Failed to update profile')
      }
    } catch (error) {
      console.error('Error updating profile:', error)
      alert('Error updating profile')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-[#F9FAFB] font-inter flex flex-col">
        <Navbar />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-xl text-gray-600">Loading...</div>
        </div>
        <Footer />
      </div>
    )
  }

  if (fetchError) {
    return (
      <div className="min-h-screen bg-[#F9FAFB] font-inter flex flex-col">
        <Navbar />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <p className="text-xl text-red-600 mb-4">{fetchError}</p>
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-[#581C87] hover:bg-[#581C87]/90 text-white rounded-lg"
            >
              Retry
            </button>
          </div>
        </div>
        <Footer />
      </div>
    )
  }

  if (!profile) {
    return (
      <div className="min-h-screen bg-[#F9FAFB] font-inter flex flex-col">
        <Navbar />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-xl text-gray-600">No profile data found.</div>
        </div>
        <Footer />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-[#F9FAFB] font-inter flex flex-col">
      <Navbar />

      <main className="flex-1 py-12">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-white rounded-2xl shadow-lg p-8">
            <div className="text-center mb-8">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                {userRole === 'investor' ? 'Your Investment Profile' : 'Your Buyer Profile'}
              </h1>
              <p className="text-gray-600">
                Complete your detailed profile for better recommendations
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Basic Info */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Phone Number
                  </label>
                  <input
                    type="tel"
                    value={formData.phone}
                    onChange={(e) => setFormData({...formData, phone: e.target.value})}
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Email Address
                  </label>
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({...formData, email: e.target.value})}
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                </div>
              </div>

              {userRole === 'investor' ? (
                <>
                  {/* Investment Details */}
                  <div className="border-t pt-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Investment Details</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Annual Income (₹)
                        </label>
                        <input
                          type="number"
                          value={formData.annualIncome}
                          onChange={(e) => setFormData({...formData, annualIncome: e.target.value})}
                          placeholder="Your annual income"
                          className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Investment Capital (₹)
                        </label>
                        <input
                          type="number"
                          value={formData.investmentCapital}
                          onChange={(e) => setFormData({...formData, investmentCapital: e.target.value})}
                          placeholder="Available investment capital"
                          className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Risk Appetite
                        </label>
                        <select
                          value={formData.riskAppetite}
                          onChange={(e) => setFormData({...formData, riskAppetite: e.target.value})}
                          className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500"
                        >
                          <option value="conservative">Conservative</option>
                          <option value="moderate">Moderate</option>
                          <option value="aggressive">Aggressive</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Expected ROI (%)
                        </label>
                        <input
                          type="number"
                          step="0.1"
                          value={formData.expectedROI}
                          onChange={(e) => setFormData({...formData, expectedROI: e.target.value})}
                          placeholder="Expected return on investment"
                          className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500"
                        />
                      </div>
                    </div>
                  </div>

                  {/* Advanced ML Features */}
                  <div className="border-t pt-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Advanced Preferences (Optional)</h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Risk Orientation (0-1)
                        </label>
                        <input
                          type="number"
                          step="0.01"
                          min="0"
                          max="1"
                          value={formData.risk_orientation_score}
                          onChange={(e) => setFormData({...formData, risk_orientation_score: e.target.value})}
                          className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Collaboration Comfort (0-1)
                        </label>
                        <input
                          type="number"
                          step="0.01"
                          min="0"
                          max="1"
                          value={formData.collaboration_comfort_score}
                          onChange={(e) => setFormData({...formData, collaboration_comfort_score: e.target.value})}
                          className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Control Preference (0-1)
                        </label>
                        <input
                          type="number"
                          step="0.01"
                          min="0"
                          max="1"
                          value={formData.control_preference_score}
                          onChange={(e) => setFormData({...formData, control_preference_score: e.target.value})}
                          className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500"
                        />
                      </div>
                    </div>
                  </div>
                </>
              ) : (
                <>
                  {/* Buyer Details */}
                  <div className="border-t pt-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Financial Details</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Employment Type
                        </label>
                        <select
                          value={formData.employmentType}
                          onChange={(e) => setFormData({...formData, employmentType: e.target.value})}
                          className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500"
                        >
                          <option value="">Select employment type</option>
                          <option value="salaried">Salaried</option>
                          <option value="self-employed">Self-employed</option>
                          <option value="business-owner">Business Owner</option>
                          <option value="freelancer">Freelancer</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Credit Score
                        </label>
                        <input
                          type="number"
                          value={formData.creditScore}
                          onChange={(e) => setFormData({...formData, creditScore: e.target.value})}
                          placeholder="Your credit score"
                          className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Down Payment Capability (₹)
                        </label>
                        <input
                          type="number"
                          value={formData.downPaymentCapability}
                          onChange={(e) => setFormData({...formData, downPaymentCapability: e.target.value})}
                          placeholder="Amount you can pay as down payment"
                          className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Loan Required
                        </label>
                        <select
                          value={formData.loanRequired}
                          onChange={(e) => setFormData({...formData, loanRequired: e.target.value === 'true'})}
                          className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500"
                        >
                          <option value={false}>No</option>
                          <option value={true}>Yes</option>
                        </select>
                      </div>
                    </div>
                  </div>
                </>
              )}

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-[#581C87] hover:bg-[#581C87]/90 text-white font-semibold py-3 px-4 rounded-lg transition-all duration-200 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg"
              >
                {loading ? (
                  <>
                    <Loader2 className="h-5 w-5 animate-spin" />
                    Updating Profile...
                  </>
                ) : (
                  <>
                    <Building2 className="h-5 w-5" />
                    Update Profile
                  </>
                )}
              </button>
            </form>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  )
}