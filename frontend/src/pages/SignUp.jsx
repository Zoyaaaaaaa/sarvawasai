import { useState } from "react";
import { useNavigate } from "react-router-dom";
import Navbar from "@/components/Navbar.jsx";
import Footer from "@/components/Footer.jsx";
import { Button } from "@/components/ui/button.jsx";
import { Card, CardContent } from "@/components/ui/card.jsx";
import { Badge } from "@/components/ui/badge.jsx";
import { Input } from "@/components/ui/input.jsx";
import { Label } from "@/components/ui/label.jsx";
import { Textarea } from "@/components/ui/textarea.jsx";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group.jsx";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select.jsx";
import { User, Mail, Phone, ArrowRight, Building2, Briefcase, IndianRupee, MapPin, Home, Info } from "lucide-react";
import { clearPendingSignupAuth, savePendingSignupAuth, setAuthFlow, setPhoneVerified } from '@/lib/auth.js';
import { apiUrl } from '@/lib/api.js';

const MUMBAI_LOCATIONS = [
    "Andheri East",
    "Andheri West",
    "Bandra East",
    "Bandra West",
    "Borivali East",
    "Borivali West",
    "Chembur",
    "Colaba",
    "Dadar",
    "Fort",
    "Ghatkopar",
    "Goregaon East",
    "Goregaon West",
    "Juhu",
    "Khar West",
    "Kurla",
    "Lower Parel",
    "Malad West",
    "Mira Road",
    "Mulund",
    "Powai",
    "Santacruz East",
    "Santacruz West",
    "Thane East",
    "Thane West",
    "Vile Parle",
    "Worli"
];

const PROPERTY_TYPES = [
    "1 BHK Apartment", "2 BHK Flat", "3 BHK Apartment", "Villa", "Penthouse"
];

function SignUp() {
    const navigate = useNavigate();
    const [formData, setFormData] = useState({
        fullName: "",
        email: "",
        phone: "",
        userType: "", // "homebuyer" or "investor"
        password: "",
        confirmPassword: "",
        age: "",
        profession: "",
        monthlyIncome: "",
        preferredLocations: [],
        propertyType: "",
        budgetMin: "",
        budgetMax: "",
        riskToleranceLevel: "",
        investmentCapital: "",
        experienceYears: "",
        additionalInfo: "",
        casteCategory: "",
    });

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData((prev) => ({
            ...prev,
            [name]: value,
        }));
    };

    const handleLocationToggle = (location) => {
        setFormData((prev) => {
            const currentLocations = prev.preferredLocations || [];
            if (currentLocations.includes(location)) {
                return {
                    ...prev,
                    preferredLocations: currentLocations.filter(loc => loc !== location)
                };
            } else {
                return {
                    ...prev,
                    preferredLocations: [...currentLocations, location]
                };
            }
        });
    };

    const buildSignUpPayload = () => {
        return {
            fullName: formData.fullName,
            email: formData.email,
            phone: formData.phone,
            password: formData.password,  // ADD THIS
            userType: formData.userType,  // CHANGE: Remove ternary - use "buyer" or "investor" directly

            // Flat structure - no metadata wrapper
            age: formData.age ? Number(formData.age) : null,
            profession: formData.profession || null,
            casteCategory: formData.casteCategory || null,  // CHANGE: null instead of "prefer not to say"
            additionalInfo: formData.additionalInfo || null,
            experienceYears: formData.experienceYears ? Number(formData.experienceYears) : null,

            // Buyer-specific fields
            ...(formData.userType === "buyer" && {
                monthlyIncome: formData.monthlyIncome ? Number(formData.monthlyIncome) : null,
                propertyType: formData.propertyType || null,
                budgetMin: formData.budgetMin ? Number(formData.budgetMin) : null,
                budgetMax: formData.budgetMax ? Number(formData.budgetMax) : null,
                riskToleranceLevel: formData.riskToleranceLevel
            }),

            // Investor-specific fields
            ...(formData.userType === "investor" && {
                investmentCapital: formData.investmentCapital ? Number(formData.investmentCapital) : null,
            }),

            // Both roles
            preferredLocations: formData.preferredLocations || [],
        };
    };


    const handleSubmit = async (e) => {
        e.preventDefault();

        // Validate required fields
        if (!formData.fullName || !formData.email || !formData.phone || !formData.userType) {
            alert("Please fill in all required fields (Name, Email, Phone, User Type)");
            return;
        }

        if (!formData.password || formData.password.length < 6) {
            alert("Password must be at least 6 characters long")
            return
        }

        if (formData.password !== formData.confirmPassword) {
            alert("Password and confirm password do not match")
            return
        }

        if (formData.userType === "buyer") {

            if (!formData.budgetMax) {
                alert("Please enter your maximum budget")
                return
            }

            if (formData.preferredLocations.length === 0) {
                alert("Please select at least one preferred location")
                return
            }

            if (!formData.riskToleranceLevel) {
                alert("Please select your risk tolerance level")
                return
            }

        }

        const payload = buildSignUpPayload(formData);

        try {
            const res = await fetch(apiUrl('/users/signup'), {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(payload)
            });

            const data = await res.json();
            const createdUserId = data?.userId || data?.user_id || data?.id || null
            const createdRole = data?.role || formData.userType

            if (res.ok) {
                console.log("User created:", data);
                if (!createdUserId) {
                    throw new Error('Signup succeeded but user id was not returned')
                }
                sessionStorage.setItem("userData", JSON.stringify(payload));
                savePendingSignupAuth({
                    userId: createdUserId,
                    role: createdRole,
                    fullName: payload.fullName,
                    email: payload.email,
                    phone: payload.phone,
                })
                setAuthFlow('signup')
                setPhoneVerified(false)
                navigate("/phone-verification");
            } else {
                clearPendingSignupAuth()
                alert("Signup failed: " + (data.detail || "Unknown error"));
            }
        } catch (err) {
            console.error(err);
            alert("Signup failed due to network error");
        }
    };



    return (
        <div className="min-h-screen bg-[#F9FAFB] font-inter flex flex-col">
            <Navbar />

            <section className="flex-1 py-20 px-4">
                <div className="max-w-3xl mx-auto">
                    <div className="text-center mb-10">
                        <Badge className="bg-[#581C87] text-white px-4 py-2 text-sm font-medium mb-6">
                            Step 1 of 3
                        </Badge>
                        <h1 className="text-4xl md:text-5xl heading text-[#111827] mb-4">
                            Start Your Journey
                        </h1>
                        <p className="text-gray-600 text-lg max-w-2xl mx-auto">
                            Tell us a bit about yourself to get started with your homeownership journey
                        </p>
                    </div>

                    <Card className="rounded-3xl shadow-xl border-0 bg-white">
                        <CardContent className="p-10">
                            <form onSubmit={handleSubmit} className="space-y-8">
                                {/* User Type Selection */}
                                <div className="space-y-4">
                                    <Label className="text-base font-medium text-[#111827] flex items-center gap-2">
                                        <Building2 className="w-4 h-4 text-[#581C87]" />
                                        I am a <span className="text-red-500">*</span>
                                    </Label>
                                    <RadioGroup
                                        value={formData.userType}
                                        onValueChange={(value) => setFormData(prev => ({ ...prev, userType: value }))}
                                        className="grid grid-cols-1 md:grid-cols-2 gap-4"
                                    >
                                        <div className={`relative flex items-start space-x-3 rounded-xl border-2 p-6 cursor-pointer transition-all ${formData.userType === 'buyer' ? 'border-[#581C87] bg-purple-50' : 'border-gray-200 hover:border-gray-300'}`}>
                                            <RadioGroupItem value="buyer" id="buyer" className="mt-1" />
                                            <Label htmlFor="buyer" className="flex-1 cursor-pointer">
                                                <div className="font-semibold text-[#111827] mb-1">Buyer</div>
                                                <p className="text-sm text-gray-600">
                                                    Looking to purchase a home through smart savings and investor partnerships
                                                </p>
                                            </Label>
                                        </div>
                                        <div className={`relative flex items-start space-x-3 rounded-xl border-2 p-6 cursor-pointer transition-all ${formData.userType === 'investor' ? 'border-[#1E3A8A] bg-blue-50' : 'border-gray-200 hover:border-gray-300'}`}>
                                            <RadioGroupItem value="investor" id="investor" className="mt-1" />
                                            <Label htmlFor="investor" className="flex-1 cursor-pointer">
                                                <div className="font-semibold text-[#111827] mb-1">Investor</div>
                                                <p className="text-sm text-gray-600">
                                                    Looking for passive real estate returns through property investments
                                                </p>
                                            </Label>
                                        </div>
                                    </RadioGroup>
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                    {/* Full Name */}
                                    <div className="space-y-2">
                                        <Label htmlFor="fullName" className="text-base font-medium text-[#111827] flex items-center gap-2">
                                            <User className="w-4 h-4 text-[#581C87]" />
                                            Full Name <span className="text-red-500">*</span>
                                        </Label>
                                        <Input
                                            id="fullName"
                                            name="fullName"
                                            type="text"
                                            placeholder="Enter your full name"
                                            value={formData.fullName}
                                            onChange={handleChange}
                                            className="h-12 text-base border-gray-300 focus:border-[#581C87] focus:ring-[#581C87]"
                                            required
                                        />
                                    </div>

                                    {/* Age */}
                                    <div className="space-y-2">
                                        <Label htmlFor="age" className="text-base font-medium text-[#111827] flex items-center gap-2">
                                            <User className="w-4 h-4 text-[#581C87]" />
                                            Age
                                        </Label>
                                        <Input
                                            id="age"
                                            name="age"
                                            type="number"
                                            placeholder="Enter your age"
                                            value={formData.age}
                                            onChange={handleChange}
                                            className="h-12 text-base border-gray-300 focus:border-[#581C87] focus:ring-[#581C87]"
                                            min="18"
                                            max="100"
                                        />
                                    </div>
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                    {/* Email */}
                                    <div className="space-y-2">
                                        <Label htmlFor="email" className="text-base font-medium text-[#111827] flex items-center gap-2">
                                            <Mail className="w-4 h-4 text-[#581C87]" />
                                            Email Address <span className="text-red-500">*</span>
                                        </Label>
                                        <Input
                                            id="email"
                                            name="email"
                                            type="email"
                                            placeholder="your.email@example.com"
                                            value={formData.email}
                                            onChange={handleChange}
                                            className="h-12 text-base border-gray-300 focus:border-[#581C87] focus:ring-[#581C87]"
                                            required
                                        />
                                    </div>

                                    {/* Phone */}
                                    <div className="space-y-2">
                                        <Label htmlFor="phone" className="text-base font-medium text-[#111827] flex items-center gap-2">
                                            <Phone className="w-4 h-4 text-[#581C87]" />
                                            Phone Number <span className="text-red-500">*</span>
                                        </Label>
                                        <Input
                                            id="phone"
                                            name="phone"
                                            type="tel"
                                            placeholder="+91 98765 43210"
                                            value={formData.phone}
                                            onChange={handleChange}
                                            className="h-12 text-base border-gray-300 focus:border-[#581C87] focus:ring-[#581C87]"
                                            required
                                        />
                                    </div>
                                </div>
                                <div className="space-y-2">
                                    <div className="space-y-2">
                                        <Label htmlFor="password" className="text-base font-medium text-[#111827] flex items-center gap-2">
                                            Password <span className="text-red-500">*</span>
                                        </Label>
                                        <Input
                                            id="password"
                                            name="password"
                                            type="password"
                                            placeholder="Enter your password"
                                            value={formData.password}
                                            onChange={handleChange}
                                            className="h-12 text-base border-gray-300 focus:border-[#581C87] focus:ring-[#581C87]"
                                            required
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="confirmPassword" className="text-base font-medium text-[#111827] flex items-center gap-2">
                                            Confirm Password <span className="text-red-500">*</span>
                                        </Label>
                                        <Input
                                            id="confirmPassword"
                                            name="confirmPassword"
                                            type="password"
                                            placeholder="Confirm your password"
                                            value={formData.confirmPassword}
                                            onChange={handleChange}
                                            className="h-12 text-base border-gray-300 focus:border-[#581C87] focus:ring-[#581C87]"
                                            required
                                        />
                                    </div>
                                    <Label htmlFor="casteCategory" className="text-base font-medium text-[#111827] flex items-center gap-2">
                                        Caste Category
                                    </Label>
                                    <Select
                                        value={formData.casteCategory}
                                        onValueChange={(value) => setFormData(prev => ({ ...prev, casteCategory: value }))}
                                    >
                                        <SelectTrigger className="h-12 border-gray-300 focus:border-[#581C87] focus:ring-[#581C87]">
                                            <SelectValue placeholder="Select your caste category" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            {["SC", "ST", "OBC", "General", "Other", "Prefer not to say"].map(cat => (
                                                <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                                            ))}
                                        </SelectContent>
                                    </Select>
                                </div>


                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                    {/* Profession */}
                                    <div className="space-y-2">
                                        <Label htmlFor="profession" className="text-base font-medium text-[#111827] flex items-center gap-2">
                                            <Briefcase className="w-4 h-4 text-[#581C87]" />
                                            Profession
                                        </Label>
                                        <Input
                                            id="profession"
                                            name="profession"
                                            type="text"
                                            placeholder="e.g., Software Engineer, Doctor"
                                            value={formData.profession}
                                            onChange={handleChange}
                                            className="h-12 text-base border-gray-300 focus:border-[#581C87] focus:ring-[#581C87]"
                                        />
                                    </div>

                                    {/* Experience Years */}
                                    <div className="space-y-2">
                                        <Label htmlFor="experienceYears" className="text-base font-medium text-[#111827] flex items-center gap-2">
                                            <Briefcase className="w-4 h-4 text-[#581C87]" />
                                            Years of Experience
                                        </Label>
                                        <Input
                                            id="experienceYears"
                                            name="experienceYears"
                                            type="number"
                                            placeholder="e.g., 5"
                                            value={formData.experienceYears}
                                            onChange={handleChange}
                                            className="h-12 text-base border-gray-300 focus:border-[#581C87] focus:ring-[#581C87]"
                                            min="0"
                                            max="50"
                                        />
                                    </div>
                                </div>

                                {/* Conditional Fields for Buyers */}
                                {formData.userType === 'buyer' && (
                                    <>
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                            {/* Monthly Income */}
                                            <div className="space-y-2">
                                                <Label htmlFor="monthlyIncome" className="text-base font-medium text-[#111827] flex items-center gap-2">
                                                    <IndianRupee className="w-4 h-4 text-[#581C87]" />
                                                    Monthly Income
                                                </Label>
                                                <Input
                                                    id="monthlyIncome"
                                                    name="monthlyIncome"
                                                    type="number"
                                                    placeholder="e.g., 150000"
                                                    value={formData.monthlyIncome}
                                                    onChange={handleChange}
                                                    className="h-12 text-base border-gray-300 focus:border-[#581C87] focus:ring-[#581C87]"
                                                />
                                            </div>

                                            {/* Property Type */}
                                            <div className="space-y-2">
                                                <Label htmlFor="propertyType" className="text-base font-medium text-[#111827] flex items-center gap-2">
                                                    <Home className="w-4 h-4 text-[#581C87]" />
                                                    Property Type
                                                </Label>
                                                <Select
                                                    value={formData.propertyType}
                                                    onValueChange={(value) => setFormData(prev => ({ ...prev, propertyType: value }))}
                                                >
                                                    <SelectTrigger className="h-12 border-gray-300 focus:border-[#581C87] focus:ring-[#581C87]">
                                                        <SelectValue placeholder="Select property type" />
                                                    </SelectTrigger>
                                                    <SelectContent>
                                                        {PROPERTY_TYPES.map(type => (
                                                            <SelectItem key={type} value={type}>{type}</SelectItem>
                                                        ))}
                                                    </SelectContent>
                                                </Select>
                                            </div>
                                        </div>

                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                            {/* Budget Range */}
                                            <div className="space-y-2">
                                                <Label htmlFor="budgetMin" className="text-base font-medium text-[#111827] flex items-center gap-2">
                                                    <IndianRupee className="w-4 h-4 text-[#581C87]" />
                                                    Budget Range (Min) <span className="text-xs text-gray-500">Optional</span>
                                                </Label>
                                                <Input
                                                    id="budgetMin"
                                                    name="budgetMin"
                                                    type="number"
                                                    placeholder="e.g., 5000000"
                                                    value={formData.budgetMin}
                                                    onChange={handleChange}
                                                    className="h-12 text-base border-gray-300 focus:border-[#581C87] focus:ring-[#581C87]"
                                                />
                                            </div>

                                            <div className="space-y-2">
                                                <Label htmlFor="budgetMax" className="text-base font-medium text-[#111827] flex items-center gap-2">
                                                    <IndianRupee className="w-4 h-4 text-[#581C87]" />
                                                    Budget Range (Max) <span className="text-red-500">*</span>
                                                </Label>
                                                <Input
                                                    id="budgetMax"
                                                    name="budgetMax"
                                                    type="number"
                                                    placeholder="e.g., 10000000"
                                                    value={formData.budgetMax}
                                                    onChange={handleChange}
                                                    className="h-12 text-base border-gray-300 focus:border-[#581C87] focus:ring-[#581C87]"
                                                />
                                            </div>
                                        </div>
                                        <div className="space-y-2">
                                            <Label className="text-base font-medium text-[#111827]">
                                                Risk Tolerance <span className="text-red-500">*</span>
                                            </Label>

                                            <Select
                                                value={formData.riskToleranceLevel}
                                                onValueChange={(value) =>
                                                    setFormData(prev => ({ ...prev, riskToleranceLevel: value }))
                                                }
                                            >
                                                <SelectTrigger className="h-12 border-gray-300">
                                                    <SelectValue placeholder="Select risk tolerance" />
                                                </SelectTrigger>

                                                <SelectContent>
                                                    <SelectItem value="low">Low</SelectItem>
                                                    <SelectItem value="moderate">Moderate</SelectItem>
                                                    <SelectItem value="high">High</SelectItem>
                                                </SelectContent>
                                            </Select>
                                        </div>
                                    </>
                                )}

                                {/* Conditional Fields for Investors */}
                                {formData.userType === 'investor' && (
                                    <div className="space-y-2">
                                        <Label htmlFor="investmentCapital" className="text-base font-medium text-[#111827] flex items-center gap-2">
                                            <IndianRupee className="w-4 h-4 text-[#1E3A8A]" />
                                            Available Investment Capital
                                        </Label>
                                        <Input
                                            id="investmentCapital"
                                            name="investmentCapital"
                                            type="number"
                                            placeholder="e.g., 5000000"
                                            value={formData.investmentCapital}
                                            onChange={handleChange}
                                            className="h-12 text-base border-gray-300 focus:border-[#1E3A8A] focus:ring-[#1E3A8A]"
                                        />
                                    </div>
                                )}

                                {/* Preferred Locations */}
                                {formData.userType && (
                                    <div className="space-y-4">
                                        <Label className="text-base font-medium text-[#111827] flex items-center gap-2">
                                            <MapPin className="w-4 h-4 text-[#581C87]" />
                                            Preferred Locations in Mumbai <span className="text-red-500">*</span>
                                        </Label>
                                        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 max-h-60 overflow-y-auto p-4 bg-gray-50 rounded-lg border border-gray-200">
                                            {MUMBAI_LOCATIONS.map(location => (
                                                <button
                                                    key={location}
                                                    type="button"
                                                    onClick={() => handleLocationToggle(location)}
                                                    className={`px-3 py-2 text-sm rounded-lg border transition-all ${formData.preferredLocations.includes(location)
                                                        ? 'bg-[#581C87] text-white border-[#581C87]'
                                                        : 'bg-white text-gray-700 border-gray-300 hover:border-[#581C87]'
                                                        }`}
                                                >
                                                    {location}
                                                </button>
                                            ))}
                                        </div>
                                        {formData.preferredLocations.length > 0 && (
                                            <p className="text-sm text-gray-600">
                                                Selected: {formData.preferredLocations.join(', ')}
                                            </p>
                                        )}
                                    </div>
                                )}

                                {/* Additional Information */}
                                {formData.userType && (
                                    <div className="space-y-2">
                                        <Label htmlFor="additionalInfo" className="text-base font-medium text-[#111827] flex items-center gap-2">
                                            <Info className="w-4 h-4 text-[#581C87]" />
                                            Additional Information <span className="text-xs text-gray-500">(Optional)</span>
                                        </Label>
                                        <Textarea
                                            id="additionalInfo"
                                            name="additionalInfo"
                                            placeholder="Any specific requirements or preferences you'd like to share..."
                                            value={formData.additionalInfo}
                                            onChange={handleChange}
                                            className="min-h-[100px] text-base border-gray-300 focus:border-[#581C87] focus:ring-[#581C87]"
                                        />
                                    </div>
                                )}

                                {/* Submit Button */}
                                <div className="pt-6">
                                    <Button
                                        type="submit"
                                        className="w-full bg-[#581C87] hover:bg-[#581C87]/90 text-white py-6 text-lg font-medium shadow-lg hover:shadow-xl transition-all"
                                    >
                                        Verify Phone Number
                                        <ArrowRight className="w-5 h-5 ml-2" />
                                    </Button>
                                </div>

                                <p className="text-sm text-gray-500 text-center">
                                    Your information is secure and will only be used to verify your identity.
                                    Location and budget preferences can be updated anytime.
                                </p>
                            </form>
                        </CardContent>
                    </Card>
                </div>
            </section>

            <Footer />
        </div>
    );
}

export default SignUp;
