import { Navigate } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext.jsx'

export default function ProtectedRoute({ children, requiredRole = null, requirePhoneVerified = false }) {
  const { isAuthenticated, role, phoneVerified, getDashboardPath } = useAuth()

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (requiredRole && role !== requiredRole) {
    return <Navigate to={getDashboardPath(role)} replace />
  }

  if (requirePhoneVerified && !phoneVerified) {
    return <Navigate to="/phone-verification" replace />
  }

  return children
}