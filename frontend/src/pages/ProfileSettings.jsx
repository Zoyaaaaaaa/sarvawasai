import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import Navbar from '@/components/Navbar.jsx'
import Footer from '@/components/Footer.jsx'
import { User, Mail, Phone, Lock, Trash2, AlertTriangle } from 'lucide-react'
import { clearAuthSession } from '@/lib/auth.js'
import { apiUrl } from '@/lib/api.js'

export default function ProfileSettings() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [profile, setProfile] = useState(null)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [otp, setOtp] = useState('')
  const [showOtpInput, setShowOtpInput] = useState(false)
  const userId = localStorage.getItem('userId')
  const userRole = localStorage.getItem('userRole')
  const hasValidUserId = Boolean(userId && userId !== 'null' && userId !== 'undefined')

  const [formData, setFormData] = useState({
    fullName: '',
    phone: '',
    email: '',
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
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
      setFormData({
        fullName: data.user?.fullName || '',
        phone: data.user?.phone || '',
        email: data.user?.email || '',
        currentPassword: '',
        newPassword: '',
        confirmPassword: '',
      })
    } catch (error) {
      console.error('Error fetching profile:', error)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)

    try {
      const updateData = {
        fullName: formData.fullName,
        phone: formData.phone,
        email: formData.email,
      }

      // Only include password if it's being changed
      if (formData.newPassword) {
        if (formData.newPassword !== formData.confirmPassword) {
          alert('New passwords do not match')
          return
        }
        updateData.currentPassword = formData.currentPassword
        updateData.newPassword = formData.newPassword
      }

      const response = await fetch(apiUrl(`/users/profile/${userId}`), {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updateData),
      })

      if (response.ok) {
        alert('Profile updated successfully')
        fetchProfile() // Refresh data
      } else {
        const error = await response.json()
        alert(error.detail || 'Failed to update profile')
      }
    } catch (error) {
      console.error('Error updating profile:', error)
      alert('Error updating profile')
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteAccount = async () => {
    if (!otp) {
      alert('Please enter the OTP sent to your phone')
      return
    }

    try {
      const response = await fetch(apiUrl(`/users/delete/${userId}`), {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ otp }),
      })

      if (response.ok) {
        clearAuthSession()

        // Redirect to landing page
        navigate('/')
      } else {
        alert('Failed to delete account. Please check the OTP.')
      }
    } catch (error) {
      console.error('Error deleting account:', error)
      alert('Error deleting account')
    }
  }

  const requestDeleteOtp = async () => {
    try {
      const response = await fetch(apiUrl(`/users/request-delete-otp/${userId}`), {
        method: 'POST',
      })

      if (response.ok) {
        setShowOtpInput(true)
        alert('OTP sent to your registered phone number')
      } else {
        alert('Failed to send OTP')
      }
    } catch (error) {
      console.error('Error requesting delete OTP:', error)
      alert('Error sending OTP')
    }
  }

  if (!profile) {
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

  return (
    <div className="min-h-screen bg-[#F9FAFB] font-inter flex flex-col">
      <Navbar />

      <main className="flex-1 py-12">
        <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-white rounded-2xl shadow-lg p-8">
            <div className="text-center mb-8">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                Profile Settings
              </h1>
              <p className="text-gray-600">
                Manage your account information and preferences
              </p>
            </div>

            <div className="mb-8 rounded-xl border border-indigo-100 bg-indigo-50/70 p-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <div>
                <p className="text-sm font-semibold text-indigo-900">Need to edit full profile details?</p>
                <p className="text-sm text-indigo-800">Update your {userRole === 'investor' ? 'investment' : 'homebuyer'} profile fields in the detailed form.</p>
              </div>
              <button
                type="button"
                onClick={() => navigate('/profile-management')}
                className="bg-indigo-600 text-white px-4 py-2 rounded-lg font-semibold hover:bg-indigo-700 transition-colors"
              >
                Complete/Update Details
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Profile Picture Section */}
              <div className="flex items-center space-x-4 p-4 bg-gray-50 rounded-xl">
                <div className="h-16 w-16 bg-gradient-to-br from-[#581C87] to-[#A855F7] rounded-full flex items-center justify-center">
                  <User className="h-8 w-8 text-white" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">{profile.user?.fullName}</h3>
                  <p className="text-gray-600">{profile.user?.email}</p>
                </div>
              </div>

              {/* Basic Information */}
              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                  <User className="h-5 w-5 mr-2" />
                  Basic Information
                </h3>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Full Name
                  </label>
                  <input
                    type="text"
                    value={formData.fullName}
                    onChange={(e) => setFormData({...formData, fullName: e.target.value})}
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                </div>

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

              {/* Password Change */}
              <div className="space-y-4 border-t pt-6">
                <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                  <Lock className="h-5 w-5 mr-2" />
                  Change Password
                </h3>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Current Password
                  </label>
                  <input
                    type="password"
                    value={formData.currentPassword}
                    onChange={(e) => setFormData({...formData, currentPassword: e.target.value})}
                    placeholder="Enter current password"
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      New Password
                    </label>
                    <input
                      type="password"
                      value={formData.newPassword}
                      onChange={(e) => setFormData({...formData, newPassword: e.target.value})}
                      placeholder="Enter new password"
                      className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Confirm New Password
                    </label>
                    <input
                      type="password"
                      value={formData.confirmPassword}
                      onChange={(e) => setFormData({...formData, confirmPassword: e.target.value})}
                      placeholder="Confirm new password"
                      className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500"
                    />
                  </div>
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-gradient-to-r from-[#581C87] to-[#1E3A8A] text-white py-3 px-6 rounded-xl font-semibold hover:opacity-90 transition-opacity disabled:opacity-50"
              >
                {loading ? 'Updating...' : 'Update Profile'}
              </button>
            </form>

            {/* Delete Account Section */}
            <div className="border-t pt-6 mt-8">
              <h3 className="text-lg font-semibold text-red-600 flex items-center mb-4">
                <Trash2 className="h-5 w-5 mr-2" />
                Danger Zone
              </h3>

              {!showDeleteConfirm ? (
                <div>
                  <p className="text-gray-600 mb-4">
                    Once you delete your account, there is no going back. Please be certain.
                  </p>
                  <button
                    onClick={() => setShowDeleteConfirm(true)}
                    className="bg-red-600 text-white px-6 py-2 rounded-xl font-semibold hover:bg-red-700 transition-colors"
                  >
                    Delete Account
                  </button>
                </div>
              ) : (
                <div className="bg-red-50 border border-red-200 rounded-xl p-4">
                  <div className="flex items-start mb-4">
                    <AlertTriangle className="h-5 w-5 text-red-600 mr-2 mt-0.5" />
                    <div>
                      <h4 className="font-semibold text-red-800">Confirm Account Deletion</h4>
                      <p className="text-red-700 text-sm mt-1">
                        This action cannot be undone. All your data will be permanently deleted.
                      </p>
                    </div>
                  </div>

                  {!showOtpInput ? (
                    <button
                      onClick={requestDeleteOtp}
                      className="bg-red-600 text-white px-4 py-2 rounded-lg font-semibold hover:bg-red-700 transition-colors mr-2"
                    >
                      Send OTP to Delete
                    </button>
                  ) : (
                    <div className="space-y-3">
                      <input
                        type="text"
                        value={otp}
                        onChange={(e) => setOtp(e.target.value)}
                        placeholder="Enter OTP"
                        className="w-full px-4 py-2 border border-red-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500"
                      />
                      <div className="flex space-x-2">
                        <button
                          onClick={handleDeleteAccount}
                          className="bg-red-600 text-white px-4 py-2 rounded-lg font-semibold hover:bg-red-700 transition-colors"
                        >
                          Confirm Delete
                        </button>
                        <button
                          onClick={() => {
                            setShowDeleteConfirm(false)
                            setShowOtpInput(false)
                            setOtp('')
                          }}
                          className="bg-gray-500 text-white px-4 py-2 rounded-lg font-semibold hover:bg-gray-600 transition-colors"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  )
}