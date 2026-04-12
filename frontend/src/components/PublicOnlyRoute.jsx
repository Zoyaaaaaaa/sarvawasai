import { Navigate } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext.jsx'

export default function PublicOnlyRoute({ children }) {
  const { isAuthenticated, role, getDashboardPath } = useAuth()

  if (isAuthenticated) {
    return <Navigate to={getDashboardPath(role)} replace />
  }

  return children
}