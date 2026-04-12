import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Navbar from "@/components/Navbar.jsx";
import Footer from "@/components/Footer.jsx";
import { Button } from "@/components/ui/button.jsx";
import { Card, CardContent } from "@/components/ui/card.jsx";
import { CheckCircle2, ArrowRight } from "lucide-react";
import { getDashboardPath, loadAuthSession } from '@/lib/auth.js'
import { apiUrl } from '@/lib/api.js'

function Welcome() {
    const navigate = useNavigate();
    const [userData, setUserData] = useState(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        const stored = JSON.parse(sessionStorage.getItem("userData") || "{}");
        setUserData(stored);
    }, []);

    const handleDashboardRedirect = async () => {
        setLoading(true);
        try {
            // Mark user as verified in backend
            const userId = sessionStorage.getItem("userId");
            const email = userData?.email;

            if (userId && email) {
                await fetch(apiUrl('/api/auth/mark-verified'), {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({
                        user_id: userId,
                        email: email,
                    }),
                });
            }

            // Determine dashboard based on role
            const role = userData?.userType || loadAuthSession()?.role || sessionStorage.getItem("userRole")
            navigate(getDashboardPath(role));
        } catch (err) {
            console.error("Error redirecting to dashboard:", err);
        } finally {
            setLoading(false);
        }
    };

    if (!userData) {
        return null;
    }

    return (
    <div className="min-h-screen bg-white font-inter flex flex-col">
            <Navbar />

            <section className="flex-1 py-20 px-4 flex items-center justify-center">
                <div className="max-w-2xl w-full">
                    <Card className="rounded-3xl shadow-2xl border-0 bg-white overflow-hidden">
                        <CardContent className="p-12">
                            {/* Success Icon */}
                            <div className="flex justify-center mb-8">
                                <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center">
                                    <CheckCircle2 className="w-12 h-12 text-green-600" />
                                </div>
                            </div>

                            {/* Welcome Message */}
                            <div className="text-center space-y-6 mb-10">
                                <h1 className="text-5xl font-bold text-gray-900">
                                    Welcome, <span className="text-[#581C87]">{userData.fullName}</span>!
                                </h1>
                                <p className="text-xl text-gray-600 max-w-xl mx-auto">
                                    Your phone number has been verified successfully. You're all set to explore exciting opportunities.
                                </p>
                            </div>

                            {/* User Info Cards */}
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-12">
                                <div className="bg-gradient-to-br from-[#581C87]/10 to-transparent rounded-xl p-6 border border-[#581C87]/20">
                                    <p className="text-sm text-gray-600 mb-2">Account Type</p>
                                    <p className="text-2xl font-bold text-[#581C87] capitalize">
                                        {userData.userType === "investor" ? "Investor" : "Homebuyer"}
                                    </p>
                                </div>
                                <div className="bg-gradient-to-br from-[#581C87]/10 to-transparent rounded-xl p-6 border border-[#581C87]/20">
                                    <p className="text-sm text-gray-600 mb-2">Email</p>
                                    <p className="text-lg font-semibold text-gray-800 truncate">{userData.email}</p>
                                </div>
                            </div>

                            {/* Next Steps */}
                            <div className="bg-blue-50 rounded-xl p-6 border border-blue-200 mb-12">
                                <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                                    <span className="w-6 h-6 flex items-center justify-center bg-[#581C87] text-white text-sm rounded-full font-bold">✓</span>
                                    What's Next?
                                </h3>
                                <ul className="space-y-3 text-gray-700">
                                    <li className="flex gap-3">
                                        <span className="text-[#581C87] font-bold">•</span>
                                        <span>Complete your profile with additional details</span>
                                    </li>
                                    <li className="flex gap-3">
                                        <span className="text-[#581C87] font-bold">•</span>
                                        <span>Explore {userData.userType === "investor" ? "investment opportunities" : "available properties"}</span>
                                    </li>
                                    <li className="flex gap-3">
                                        <span className="text-[#581C87] font-bold">•</span>
                                        <span>Connect with {userData.userType === "investor" ? "homebuyers" : "investors"} through our platform</span>
                                    </li>
                                </ul>
                            </div>

                            {/* CTA Button */}
                            <Button
                                onClick={handleDashboardRedirect}
                                disabled={loading}
                                className="w-full bg-[#581C87] hover:bg-[#581C87]/90 text-white py-6 text-lg font-semibold shadow-lg hover:shadow-xl transition-all flex items-center justify-center gap-2"
                            >
                                {loading ? "Loading..." : "Go to Dashboard"}
                                <ArrowRight className="w-5 h-5" />
                            </Button>

                            {/* Security Note */}
                            <div className="mt-8 pt-6 border-t border-gray-200 text-center">
                                <p className="text-xs text-gray-500">
                                    Your account is secure and verified. You can now access all features of the platform.
                                </p>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            </section>

            <Footer />
        </div>
    );
}

export default Welcome;
