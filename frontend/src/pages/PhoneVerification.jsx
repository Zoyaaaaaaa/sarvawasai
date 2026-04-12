import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import Navbar from "@/components/Navbar.jsx";
import Footer from "@/components/Footer.jsx";
import { Button } from "@/components/ui/button.jsx";
import { Card, CardContent } from "@/components/ui/card.jsx";
import { Badge } from "@/components/ui/badge.jsx";
import { Input } from "@/components/ui/input.jsx";
import { Loader2, ArrowLeft, CheckCircle2 } from "lucide-react";
import { useAuth } from "@/context/AuthContext.jsx";
import {
  clearAuthFlow,
  clearPendingSignupAuth,
  getAuthFlow,
  getDashboardPath,
  getPendingSignupAuth,
  loadAuthSession,
  setPhoneVerified,
} from "@/lib/auth.js";
import { apiUrl } from '@/lib/api.js';

function PhoneVerification() {
  const navigate = useNavigate();
  const { completePhoneVerification, role } = useAuth();
  const [userData, setUserData] = useState(null);
  const [otp, setOtp] = useState(["", "", "", "", "", ""]);
  const [loading, setLoading] = useState(false);
  const [otpSent, setOtpSent] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [resendTimer, setResendTimer] = useState(0);
  const inputRefs = useRef([]);

  const normalizePhone = (rawPhone) => {
    if (!rawPhone) return rawPhone;
    const cleaned = rawPhone.trim().replace(/\s|-/g, "");
    if (cleaned.startsWith("+")) return cleaned;
    if (/^\d{10}$/.test(cleaned)) return "+91" + cleaned;
    if (/^0\d{10}$/.test(cleaned)) return "+91" + cleaned.slice(1);
    return "+" + cleaned;
  };

  useEffect(() => {
    const signupDataRaw = sessionStorage.getItem("userData");
    const signupData = signupDataRaw ? JSON.parse(signupDataRaw) : null;
    const authFlow = getAuthFlow();
    const authSession = loadAuthSession();
    const pendingSignup = getPendingSignupAuth();

    if (signupData?.phone) {
      setUserData(signupData);
      return;
    }

    if (authFlow === "login" && authSession?.userId) {
      if (authSession.fullName && authSession.email && authSession.phone) {
        setUserData({
          userId: authSession.userId,
          fullName: authSession.fullName,
          email: authSession.email,
          phone: authSession.phone,
        });
        return;
      }
      navigate("/login");
      return;
    }

    if (pendingSignup?.userId && pendingSignup.phone) {
      const hydrated = {
        userId: pendingSignup.userId,
        fullName: pendingSignup.fullName,
        email: pendingSignup.email,
        phone: pendingSignup.phone,
        userType: pendingSignup.role,
      };
      setUserData(hydrated);
      sessionStorage.setItem("userData", JSON.stringify(hydrated));
      return;
    }

    navigate("/login");
  }, [navigate]);

  useEffect(() => {
    if (resendTimer > 0) {
      const timer = setTimeout(() => setResendTimer((v) => v - 1), 1000);
      return () => clearTimeout(timer);
    }
    return undefined;
  }, [resendTimer]);

  const handleSendOtp = async () => {
    setLoading(true);
    setError("");

    try {
      if (import.meta.env.MODE === "development") {
        sessionStorage.setItem("verificationSid", "dev_test_sid");
        setOtpSent(true);
        setResendTimer(30);
        return;
      }

      const response = await fetch(apiUrl('/api/auth/send-otp'), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phone: normalizePhone(userData.phone) }),
      });

      if (!response.ok) {
        throw new Error("Failed to send OTP");
      }

      const data = await response.json();
      sessionStorage.setItem("verificationSid", data.verification_sid);
      setOtpSent(true);
      setResendTimer(30);
    } catch (err) {
      setError("Failed to send OTP. Please try again.");
      console.error("OTP send error:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleOtpChange = (index, value) => {
    if (value && !/^\d$/.test(value)) return;

    const newOtp = [...otp];
    newOtp[index] = value;
    setOtp(newOtp);

    if (value && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }

    if (index === 5 && value && newOtp.every((digit) => digit)) {
      handleVerifyOtp(newOtp.join(""));
    }
  };

  const handleKeyDown = (index, e) => {
    if (e.key === "Backspace" && !otp[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  const handlePaste = (e) => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData("text").slice(0, 6);

    if (/^\d+$/.test(pastedData)) {
      const newOtp = pastedData.split("").concat(Array(6).fill("")).slice(0, 6);
      setOtp(newOtp);

      if (pastedData.length === 6) {
        handleVerifyOtp(pastedData);
      } else {
        inputRefs.current[pastedData.length]?.focus();
      }
    }
  };

  const handleVerifyOtp = async (otpCode = otp.join("")) => {
    if (otpCode.length !== 6) {
      setError("Please enter complete 6-digit OTP");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await fetch(apiUrl('/api/auth/verify-otp'), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          phone: normalizePhone(userData.phone),
          otp_code: otpCode,
        }),
      });

      if (!response.ok) {
        throw new Error("Invalid OTP");
      }

      const data = await response.json();

      if (data.status === "approved") {
        setPhoneVerified(true);
        completePhoneVerification();
        setSuccess(true);

        const currentFlow = getAuthFlow();
        const dashboardPath = getDashboardPath(role || loadAuthSession()?.role);

        setTimeout(() => {
          if (currentFlow === "login") {
            clearAuthFlow();
            navigate(dashboardPath);
            return;
          }

          clearAuthFlow();
          clearPendingSignupAuth();
          navigate("/profile-completion");
        }, 1500);
      } else {
        setError("Invalid OTP. Please try again.");
        setOtp(["", "", "", "", "", ""]);
        inputRefs.current[0]?.focus();
      }
    } catch (err) {
      setError("Verification failed. Please try again.");
      console.error("OTP verification error:", err);
    } finally {
      setLoading(false);
    }
  };

  if (!userData) {
    return null;
  }

  return (
    <div className="min-h-screen bg-[#F9FAFB] font-inter flex flex-col">
      <Navbar />

      <section className="flex-1 py-20 px-4">
        <div className="max-w-2xl mx-auto">
          <div className="text-center mb-10">
            <Badge className="bg-[#581C87] text-white px-4 py-2 text-sm font-medium mb-6">
              Step 2 of 3
            </Badge>
            <h1 className="text-4xl md:text-5xl heading text-[#111827] mb-4">
              Verify Phone Number
            </h1>
            <p className="text-gray-600 text-lg max-w-xl mx-auto">
              We will send a 6-digit code to ******
              <span className="font-medium text-[#111827]">{userData.phone.slice(-4)}</span>
            </p>
          </div>

          <Card className="rounded-3xl shadow-xl border-0 bg-white">
            <CardContent className="p-10">
              {!otpSent ? (
                <div className="text-center space-y-6">
                  <p className="text-gray-600">Click the button below to receive your verification code</p>
                  <Button
                    onClick={handleSendOtp}
                    disabled={loading}
                    className="bg-[#581C87] hover:bg-[#581C87]/90 text-white px-10 py-6 text-lg font-medium shadow-lg hover:shadow-xl transition-all"
                  >
                    {loading ? (
                      <>
                        <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                        Sending OTP...
                      </>
                    ) : (
                      "Send OTP"
                    )}
                  </Button>
                </div>
              ) : (
                <div className="space-y-8">
                  <div>
                    <label className="block text-center text-sm font-medium text-gray-700 mb-4">
                      Enter 6-Digit Code
                    </label>
                    <div className="flex gap-3 justify-center" onPaste={handlePaste}>
                      {otp.map((digit, index) => (
                        <Input
                          key={index}
                          ref={(el) => {
                            inputRefs.current[index] = el;
                          }}
                          type="text"
                          inputMode="numeric"
                          maxLength={1}
                          value={digit}
                          onChange={(e) => handleOtpChange(index, e.target.value)}
                          onKeyDown={(e) => handleKeyDown(index, e)}
                          className="w-14 h-14 text-center text-2xl font-bold border-2 border-gray-300 focus:border-[#581C87] focus:ring-[#581C87] rounded-lg"
                          disabled={loading || success}
                        />
                      ))}
                    </div>
                  </div>

                  {error && (
                    <div className="bg-red-50 border-2 border-red-200 rounded-lg p-4">
                      <p className="text-red-800 text-center font-medium">{error}</p>
                    </div>
                  )}

                  {success && (
                    <div className="bg-green-50 border-2 border-green-200 rounded-lg p-4">
                      <div className="flex items-center justify-center gap-2">
                        <CheckCircle2 className="w-5 h-5 text-green-600" />
                        <p className="text-green-800 text-lg font-medium">
                          Phone verified successfully! Redirecting...
                        </p>
                      </div>
                    </div>
                  )}

                  {!success && (
                    <Button
                      onClick={() => handleVerifyOtp()}
                      disabled={loading || otp.some((digit) => !digit)}
                      className="w-full bg-[#581C87] hover:bg-[#581C87]/90 text-white py-6 text-lg font-medium shadow-lg hover:shadow-xl transition-all"
                    >
                      {loading ? (
                        <>
                          <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                          Verifying...
                        </>
                      ) : (
                        "Verify OTP"
                      )}
                    </Button>
                  )}

                  <div className="text-center">
                    <p className="text-sm text-gray-600 mb-2">Didn't receive the code?</p>
                    {resendTimer > 0 ? (
                      <p className="text-sm text-gray-500">
                        Resend available in <span className="font-medium text-[#581C87]">{resendTimer}s</span>
                      </p>
                    ) : (
                      <Button
                        variant="link"
                        onClick={handleSendOtp}
                        disabled={loading}
                        className="text-[#581C87] hover:text-[#581C87]/80 font-medium"
                      >
                        Resend OTP
                      </Button>
                    )}
                  </div>
                </div>
              )}

              <div className="mt-8 text-center">
                <Button
                  variant="ghost"
                  onClick={() => navigate(getAuthFlow() === "login" ? "/login" : "/sign-up")}
                  className="text-gray-600 hover:text-[#111827]"
                  disabled={loading}
                >
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Back
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </section>

      <Footer />
    </div>
  );
}

export default PhoneVerification;
