import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Loader2, Building2 } from 'lucide-react'
import Navbar from '@/components/Navbar.jsx'
import Footer from '@/components/Footer.jsx'
import { apiUrl } from '@/lib/api.js'

export default function ProfileCompletion() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [profile, setProfile] = useState(null)
  const [fetchError, setFetchError] = useState(null)
  const userId = localStorage.getItem('userId')
  const hasValidUserId = Boolean(userId && userId !== 'null' && userId !== 'undefined')
  const userRole = localStorage.getItem('userRole')

  const [formData, setFormData] = useState({
    fullName: '',
    email: '',
    phone: '',
    age: '',
    profession: '',
    casteCategory: 'Prefer not to say',
    preferredLocalities: [],
    monthlyIncome: '',
    budgetRange: { min: '', max: '' },
    propertyType: 'Apartment',
    // Add other optional fields that were skipped during signup
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

      // Pre-fill form with existing data
      setFormData({
        fullName: data.user?.fullName || '',
        email: data.user?.email || '',
        phone: data.user?.phone || '',
        age: data.user?.age || '',
        profession: data.user?.profession || '',
        casteCategory: data.user?.casteCategory || 'Prefer not to say',
        preferredLocalities: data.profile?.preferredLocalities || [],
        monthlyIncome: data.profile?.monthlyIncome || '',
        budgetRange: data.profile?.budgetRange || { min: '', max: '' },
        propertyType: data.profile?.propertyType || 'Apartment',
      })
    } catch (error) {
      console.error('Error fetching profile:', error)
      setFetchError('Unable to load profile. Please login again or try later.')
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)

    try {
      const updateData = {
        fullName: formData.fullName,
        email: formData.email,
        phone: formData.phone,
        age: formData.age,
        profession: formData.profession,
        casteCategory: formData.casteCategory,
        preferredLocalities: formData.preferredLocalities,
        monthlyIncome: parseInt(formData.monthlyIncome) || 0,
        budgetRange: {
          min: parseInt(formData.budgetRange.min) || 0,
          max: parseInt(formData.budgetRange.max) || 0,
        },
        propertyType: formData.propertyType,
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
        await fetch(apiUrl(`/users/notifications/${userId}/dismiss/1`), {
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

  const handleLocalityChange = (e) => {
    const value = e.target.value
    if (value && !formData.preferredLocalities.includes(value)) {
      setFormData({
        ...formData,
        preferredLocalities: [...formData.preferredLocalities, value]
      })
      e.target.value = '' // Clear input
    }
  }

  const removeLocality = (locality) => {
    setFormData({
      ...formData,
      preferredLocalities: formData.preferredLocalities.filter(l => l !== locality)
    })
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
        <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-white rounded-2xl shadow-lg p-8">
            <div className="text-center mb-8">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                Complete Your Profile
              </h1>
              <p className="text-gray-600">
                Add more details to get better property recommendations
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Basic and Signup Optional Fields */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Full Name</label>
                  <input
                    type="text"
                    value={formData.fullName}
                    onChange={(e) => setFormData({...formData, fullName: e.target.value})}
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Email Address</label>
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({...formData, email: e.target.value})}
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Phone Number</label>
                  <input
                    type="tel"
                    value={formData.phone}
                    onChange={(e) => setFormData({...formData, phone: e.target.value})}
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Age</label>
                  <input
                    type="number"
                    min="18"
                    value={formData.age}
                    onChange={(e) => setFormData({...formData, age: e.target.value})}
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Profession</label>
                  <input
                    type="text"
                    value={formData.profession}
                    onChange={(e) => setFormData({...formData, profession: e.target.value})}
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Caste Category</label>
                  <select
                    value={formData.casteCategory}
                    onChange={(e) => setFormData({...formData, casteCategory: e.target.value})}
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500"
                  >
                    <option value="SC">SC</option>
                    <option value="ST">ST</option>
                    <option value="OBC">OBC</option>
                    <option value="General">General</option>
                    <option value="Other">Other</option>
                    <option value="Prefer not to say">Prefer not to say</option>
                  </select>
                </div>
              </div>

              {/* Preferred Localities */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Preferred Localities
                </label>
                <input
                  type="text"
                  placeholder="Enter locality (e.g., Andheri West)"
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault()
                      handleLocalityChange(e)
                    }
                  }}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500 mb-3"
                />
                <div className="flex flex-wrap gap-2">
                  {formData.preferredLocalities.map((locality, index) => (
                    <span
                      key={index}
                      className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-purple-100 text-purple-800"
                    >
                      {locality}
                      <button
                        type="button"
                        onClick={() => removeLocality(locality)}
                        className="ml-2 text-purple-600 hover:text-purple-800"
                      >
                        ×
                      </button>
                    </span>
                  ))}
                </div>
              </div>

              {/* Monthly Income */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Monthly Income (₹)
                </label>
                <input
                  type="number"
                  value={formData.monthlyIncome}
                  onChange={(e) => setFormData({...formData, monthlyIncome: e.target.value})}
                  placeholder="Enter your monthly income"
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              </div>

              {/* Budget Range */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Min Budget (₹)
                  </label>
                  <input
                    type="number"
                    value={formData.budgetRange.min}
                    onChange={(e) => setFormData({
                      ...formData,
                      budgetRange: {...formData.budgetRange, min: e.target.value}
                    })}
                    placeholder="Minimum budget"
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Max Budget (₹)
                  </label>
                  <input
                    type="number"
                    value={formData.budgetRange.max}
                    onChange={(e) => setFormData({
                      ...formData,
                      budgetRange: {...formData.budgetRange, max: e.target.value}
                    })}
                    placeholder="Maximum budget"
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                </div>
              </div>

              {/* Property Type */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Preferred Property Type
                </label>
                <select
                  value={formData.propertyType}
                  onChange={(e) => setFormData({...formData, propertyType: e.target.value})}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  <option value="Apartment">Apartment</option>
                  <option value="Villa">Villa</option>
                  <option value="Independent House">Independent House</option>
                  <option value="Plot">Plot</option>
                </select>
              </div>

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
                    Complete Profile
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