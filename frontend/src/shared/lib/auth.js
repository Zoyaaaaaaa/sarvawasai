const AUTH_KEY = 'sarvawas_auth'
const FLOW_KEY = 'sarvawas_auth_flow'
const PHONE_VERIFIED_KEY = 'phoneVerified'
const PENDING_SIGNUP_KEY = 'sarvawas_pending_signup_auth'

export function normalizeRole(role) {
  if (!role) return null
  const value = String(role).toLowerCase()
  if (value === 'investor') return 'investor'
  if (value === 'buyer' || value === 'homebuyer') return 'homebuyer'
  return null
}

export function getDashboardPath(role) {
  return normalizeRole(role) === 'investor' ? '/investor-dashboard' : '/homebuyer-dashboard'
}

function toSessionPayload(raw = {}) {
  const normalizeScalar = (value) => {
    if (value === null || value === undefined) return null
    const trimmed = String(value).trim()
    if (!trimmed || trimmed === 'null' || trimmed === 'undefined') return null
    return trimmed
  }

  const userId = normalizeScalar(raw.userId)
  const fullName = normalizeScalar(raw.fullName || raw.userName)
  const email = normalizeScalar(raw.email || raw.userEmail)
  const phone = normalizeScalar(raw.phone || raw.userPhone)
  const role = normalizeRole(raw.role || raw.userRole)

  return {
    userId,
    role,
    fullName: fullName || '',
    email: email || '',
    phone: phone || '',
  }
}

export function saveAuthSession(rawSession) {
  const session = toSessionPayload(rawSession)
  if (!session.userId || !session.role) return null

  localStorage.setItem(AUTH_KEY, JSON.stringify(session))
  localStorage.setItem('userId', session.userId)
  localStorage.setItem('userRole', session.role)
  localStorage.setItem('userName', session.fullName || '')
  localStorage.setItem('userEmail', session.email || '')
  localStorage.setItem('userPhone', session.phone || '')

  return session
}

export function loadAuthSession() {
  try {
    const stored = localStorage.getItem(AUTH_KEY)
    if (stored) {
      const parsed = JSON.parse(stored)
      const normalized = toSessionPayload(parsed)
      if (normalized.userId && normalized.role) return normalized
    }
  } catch (error) {
    console.error('Failed to parse auth session:', error)
  }

  const legacy = toSessionPayload({
    userId: localStorage.getItem('userId'),
    role: localStorage.getItem('userRole'),
    fullName: localStorage.getItem('userName'),
    email: localStorage.getItem('userEmail'),
    phone: localStorage.getItem('userPhone'),
  })

  if (legacy.userId && legacy.role) {
    saveAuthSession(legacy)
    return legacy
  }

  localStorage.removeItem('userId')
  localStorage.removeItem('userRole')
  localStorage.removeItem('userName')
  localStorage.removeItem('userEmail')
  localStorage.removeItem('userPhone')

  return null
}

export function clearAuthSession() {
  localStorage.removeItem(AUTH_KEY)
  localStorage.removeItem('userId')
  localStorage.removeItem('userRole')
  localStorage.removeItem('userName')
  localStorage.removeItem('userEmail')
  localStorage.removeItem('userPhone')

  sessionStorage.removeItem('userData')
  sessionStorage.removeItem('userId')
  sessionStorage.removeItem('userRole')
  sessionStorage.removeItem('fromLogin')
  sessionStorage.removeItem('loginPhone')
  sessionStorage.removeItem(PHONE_VERIFIED_KEY)
  sessionStorage.removeItem('verificationSid')
  sessionStorage.removeItem(FLOW_KEY)
  sessionStorage.removeItem(PENDING_SIGNUP_KEY)
}

export function setAuthFlow(flow) {
  if (!flow) return
  sessionStorage.setItem(FLOW_KEY, flow)
}

export function getAuthFlow() {
  return sessionStorage.getItem(FLOW_KEY)
}

export function clearAuthFlow() {
  sessionStorage.removeItem(FLOW_KEY)
}

export function setPhoneVerified(value = true) {
  sessionStorage.setItem(PHONE_VERIFIED_KEY, value ? 'true' : 'false')
}

export function isPhoneVerified() {
  return sessionStorage.getItem(PHONE_VERIFIED_KEY) === 'true'
}

export function savePendingSignupAuth(rawSession) {
  const session = toSessionPayload(rawSession)
  sessionStorage.setItem(PENDING_SIGNUP_KEY, JSON.stringify(session))
}

export function getPendingSignupAuth() {
  try {
    const raw = sessionStorage.getItem(PENDING_SIGNUP_KEY)
    return raw ? toSessionPayload(JSON.parse(raw)) : null
  } catch {
    return null
  }
}

export function clearPendingSignupAuth() {
  sessionStorage.removeItem(PENDING_SIGNUP_KEY)
}
