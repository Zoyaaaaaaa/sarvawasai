import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Navbar from "@/components/Navbar.jsx";
import Footer from "@/components/Footer.jsx";
import { Button } from "@/components/ui/button.jsx";
import { Card, CardContent } from "@/components/ui/card.jsx";
import { Badge } from "@/components/ui/badge.jsx";
import { Loader2, Upload, CheckCircle, XCircle } from "lucide-react";
import { apiUrl } from '@/lib/api.js';

function PanVerification() {
    const navigate = useNavigate();
    
    useEffect(() => {
        window.scrollTo({
            top: 0,
            behavior: "smooth",
        });
        
        // Check if user came from the form
        const userData = sessionStorage.getItem("userData");
        const phoneVerified = sessionStorage.getItem("phoneVerified");
        
        if (!userData) {
            // Redirect to sign up form if no data found
            navigate("/sign-up");
            return;
        }
        
        if (!phoneVerified) {
            // Redirect to phone verification if not verified
            navigate("/phone-verification");
            return;
        }
    }, [navigate]);

    const [selectedFile, setSelectedFile] = useState(null);
    const [preview, setPreview] = useState(null);
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [verified, setVerified] = useState(false);

    const handleFileChange = (e) => {
        const file = e.target.files[0];
        if (file && (file.type === "image/jpeg" || file.type === "image/png")) {
            setSelectedFile(file);
            const reader = new FileReader();
            reader.onloadend = () => setPreview(reader.result);
            reader.readAsDataURL(file);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!selectedFile) return;

        setLoading(true);
        setResult(null);

        const formData = new FormData();
        formData.append("file", selectedFile);

        try {
            console.log("Sending request to verify PAN...");
            const response = await fetch(apiUrl('/api/verify-pan'), {
                method: "POST",
                body: formData,
            });

            console.log("Response status:", response.status);
            const responseText = await response.text();
            console.log("Response text:", responseText);

            if (!response.ok) {
                throw new Error(`Error ${response.status}: ${responseText}`);
            }

            const data = JSON.parse(responseText);
            console.log("Parsed data:", data);
            setResult(data);
            
            // If PAN is verified successfully, redirect after 3 seconds
            if (data.is_genuine) {
                setVerified(true);
                setTimeout(() => {
                    navigate("/#journey");
                    // Scroll to the "Choose Your Path" section
                    setTimeout(() => {
                        const element = document.getElementById("journey");
                        if (element) {
                            element.scrollIntoView({ behavior: "smooth" });
                        }
                    }, 100);
                }, 3000);
            }
        } catch (err) {
            console.error("Detailed error:", err);
            alert(`Error verifying PAN card: ${err.message}`);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-[#F9FAFB] font-inter flex flex-col">
            <Navbar />

            <section className="flex-1 py-20 px-4">
                <div className="max-w-4xl mx-auto">
                    <div className="text-center mb-10">
                        <Badge className="bg-[#581C87] text-white px-4 py-2 text-sm font-medium mb-6">
                            Step 3 of 3
                        </Badge>
                        <h1 className="text-4xl md:text-5xl heading text-[#111827] mb-4">
                            Verify Your PAN Card
                        </h1>
                        <p className="text-gray-600 text-lg max-w-2xl mx-auto">
                            Upload your PAN card image to verify its authenticity. Once verified, you'll be redirected to choose your path.
                        </p>
                    </div>

                    <Card className="rounded-3xl shadow-lg border-0 bg-white/90">
                        <CardContent className="p-10">
                            <form onSubmit={handleSubmit} className="space-y-8">
                                {/* File Upload Area */}
                                <div className="flex flex-col items-center justify-center">
                                    <label
                                        htmlFor="pan-upload"
                                        className="w-full max-w-md h-64 flex flex-col items-center justify-center border-2 border-dashed border-gray-300 rounded-lg cursor-pointer hover:border-purple-400 transition-colors"
                                    >
                                        {preview ? (
                                            <img
                                                src={preview}
                                                alt="Preview"
                                                className="max-h-60 object-contain"
                                            />
                                        ) : (
                                            <div className="text-center p-6">
                                                <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                                                <p className="text-gray-600">
                                                    Click to upload your PAN Card
                                                </p>
                                                <p className="text-sm text-gray-500 mt-1">
                                                    JPG or PNG only
                                                </p>
                                            </div>
                                        )}
                                        <input
                                            id="pan-upload"
                                            type="file"
                                            className="hidden"
                                            accept="image/jpeg,image/png"
                                            onChange={handleFileChange}
                                        />
                                    </label>
                                </div>

                                {/* Submit Button */}
                                <div className="flex justify-center">
                                    <Button
                                        type="submit"
                                        className="bg-[#581C87] hover:bg-[#581C87]/90 text-white px-10 py-6 text-lg font-medium shadow-lg hover:shadow-xl transition-all"
                                        disabled={!selectedFile || loading}
                                    >
                                        {loading ? (
                                            <Loader2 className="w-6 h-6 animate-spin" />
                                        ) : (
                                            "Verify PAN Card"
                                        )}
                                    </Button>
                                </div>
                            </form>

                            {/* Results */}
                            {result && (
                                <div className="mt-8 space-y-4">
                                    <div className={`rounded-lg p-4 border-2 ${
                                        result.is_genuine
                                            ? "bg-green-50 border-green-200"
                                            : "bg-red-50 border-red-200"
                                    }`}>
                                        <div className="flex items-center justify-center gap-3">
                                            {result.is_genuine ? (
                                                <CheckCircle className="w-6 h-6 text-green-600" />
                                            ) : (
                                                <XCircle className="w-6 h-6 text-red-600" />
                                            )}
                                            <div className={`text-lg ${result.is_genuine ? "text-green-800" : "text-red-800"}`}>
                                                <p className="font-medium">
                                                    {result.message}
                                                </p>
                                                <p className="text-sm mt-1">
                                                    Similarity Score: {(result.ssim_value * 100).toFixed(2)}%
                                                </p>
                                            </div>
                                        </div>
                                    </div>
                                    
                                    {verified && (
                                        <div className="text-center p-6 bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg border border-purple-100">
                                            <p className="text-lg font-medium text-[#111827] mb-2">
                                                ✓ Verification Successful!
                                            </p>
                                            <p className="text-gray-600">
                                                Redirecting you to choose your path...
                                            </p>
                                        </div>
                                    )}
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </div>
            </section>

            <Footer />
        </div>
    );
}

export default PanVerification;