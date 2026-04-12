import { Navigate, Routes, Route } from 'react-router-dom'
import Landing from '@/pages/Landing.jsx'
import Login from '@/pages/Login.jsx'
import BuyerAgreement from '@/pages/BuyerAgreement.jsx'
import InvestorAgreement from '@/pages/InvestorAgreement.jsx'
import StepUp from '@/pages/StepUp.jsx'
import StepUp2 from '@/pages/StepUp2.jsx'
import HousingSchemes from '@/pages/HousingSchemes.jsx'
import ReraVerification from '@/pages/ReraVerification.jsx'
import PanVerification from '@/pages/PanVerification.jsx'
import SignUp from '@/pages/SignUp.jsx'
import PhoneVerification from '@/pages/PhoneVerification.jsx'
import MLInvestorSimilarity from '@/components/MLInvestorSimilarity.jsx'
import InvestorDashboard from '@/pages/InvestorDashboard.jsx'
import HomebuyerDashboard from '@/pages/HomebuyerDashboard.jsx'
import CoVestMatches from '@/pages/CoVestMatches.jsx'
import InvestorMatchDetail from '@/pages/InvestorMatchDetail.jsx'
import HousePredictionPage from '@/pages/HousePredictionPage.jsx'
import LegalAnalysisPage from '@/pages/LegalAnalysisPage.jsx'
import ProfileCompletion from '@/pages/ProfileCompletion.jsx'
import ProfileManagement from '@/pages/ProfileManagement.jsx'
import ProfileSettings from '@/pages/ProfileSettings.jsx'
import ProtectedRoute from '@/components/ProtectedRoute.jsx'
import PublicOnlyRoute from '@/components/PublicOnlyRoute.jsx'

export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<PublicOnlyRoute><Login /></PublicOnlyRoute>} />
      <Route path="/sign-up" element={<PublicOnlyRoute><SignUp /></PublicOnlyRoute>} />
      <Route path="/log-in" element={<Navigate to="/login" replace />} />
      <Route path="/phone-verification" element={<PhoneVerification />} />
      <Route path="/pan-verification" element={<ProtectedRoute requirePhoneVerified><PanVerification /></ProtectedRoute>} />
      <Route path="/investor-dashboard" element={<ProtectedRoute requiredRole="investor" requirePhoneVerified><InvestorDashboard /></ProtectedRoute>} />
      <Route path="/homebuyer-dashboard" element={<ProtectedRoute requiredRole="homebuyer" requirePhoneVerified><HomebuyerDashboard /></ProtectedRoute>} />
      <Route path="/stepup" element={<ProtectedRoute requiredRole="homebuyer" requirePhoneVerified><StepUp /></ProtectedRoute>} />
      <Route path="/stepup2" element={<ProtectedRoute requirePhoneVerified><StepUp2 /></ProtectedRoute>} />
      <Route path="/buyer-agreement" element={<ProtectedRoute requiredRole="homebuyer" requirePhoneVerified><BuyerAgreement /></ProtectedRoute>} />
      <Route path="/investor-agreement" element={<ProtectedRoute requiredRole="investor" requirePhoneVerified><InvestorAgreement /></ProtectedRoute>} />
      <Route path="/housing-schemes" element={<ProtectedRoute requirePhoneVerified><HousingSchemes /></ProtectedRoute>} />
      <Route path="/rera-verification" element={<ProtectedRoute requirePhoneVerified><ReraVerification /></ProtectedRoute>} />
      <Route path="/co-vest" element={<ProtectedRoute requiredRole="investor" requirePhoneVerified><MLInvestorSimilarity /></ProtectedRoute>} />
      <Route path="/matches/:userId" element={<ProtectedRoute requiredRole="investor" requirePhoneVerified><CoVestMatches /></ProtectedRoute>} />
      <Route path="/investors/:matchId" element={<ProtectedRoute requiredRole="investor" requirePhoneVerified><InvestorMatchDetail /></ProtectedRoute>} />
      <Route path="/legal-analysis" element={<ProtectedRoute requirePhoneVerified><LegalAnalysisPage /></ProtectedRoute>} />
      <Route path="/house-prediction" element={<ProtectedRoute requirePhoneVerified><HousePredictionPage /></ProtectedRoute>} />
      <Route path="/profile-completion" element={<ProtectedRoute requirePhoneVerified><ProfileCompletion /></ProtectedRoute>} />
      <Route path="/profile-management" element={<ProtectedRoute requirePhoneVerified><ProfileManagement /></ProtectedRoute>} />
      <Route path="/profile-settings" element={<ProtectedRoute requirePhoneVerified><ProfileSettings /></ProtectedRoute>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
