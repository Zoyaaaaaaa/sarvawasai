/**
 * ML Investor Similarity Component
 * 
 * Uses ML-powered pairwise ranker to find similar investors
 */

import React, { useState } from 'react';
import axios from 'axios';
import { Brain, Users, TrendingUp, Clock, DollarSign, Target, Sparkles } from 'lucide-react';
import { Button } from "@/components/ui/button.jsx";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card.jsx";
import { Badge } from "@/components/ui/badge.jsx";
import Navbar from "@/components/Navbar.jsx";
import Footer from "@/components/Footer.jsx";
import { apiUrl } from '@/lib/api.js';

const MLInvestorSimilarity = () => {
    const [profile, setProfile] = useState({
        capital_band: 2,
        expected_roi_band: 'medium',
        holding_period_band: 'medium',
        risk_orientation: 0.5,
        collaboration_comfort: 0.5,
        control_preference: 0.5,
        re_conviction: 0.5,
        city_tier: 2
    });

    const [recommendations, setRecommendations] = useState([]);
    const [loading, setLoading] = useState(false);
    const [modelInfo, setModelInfo] = useState(null);
    const [topK, setTopK] = useState(10);

    // Load model info on mount
    React.useEffect(() => {
        loadModelInfo();
    }, []);

    const loadModelInfo = async () => {
        try {
            const response = await axios.get(apiUrl('/api/ml-similarity/model-info'));
            setModelInfo(response.data);
        } catch (error) {
            console.error('Error loading model info:', error);
        }
    };

    const getRecommendations = async () => {
        setLoading(true);
        
        // Log the profile being sent for debugging
        console.log('🔍 Sending investor profile:', profile);
        console.log('📊 Request parameters:', { top_k: topK });
        
        try {
            const response = await axios.post(
                apiUrl('/api/ml-similarity/recommend'),
                profile,
                { params: { top_k: topK } }
            );
            
            console.log('✅ Received matches:', response.data.matches.length);
            console.log('📈 Top match details:', response.data.matches[0]);
            
            setRecommendations(response.data.matches);
        } catch (error) {
            console.error('❌ Error getting recommendations:', error);
            alert('Error: ' + (error.response?.data?.detail || error.message));
        } finally {
            setLoading(false);
        }
    };

    const handleInputChange = (field, value) => {
        setProfile(prev => ({ ...prev, [field]: value }));
    };

    // Helper function to get match quality based on raw score
    const getMatchQuality = (score) => {
        // XGBoost scores are unbounded positive numbers
        // Based on observed ranges from our model
        if (score >= 2.0) return { label: 'Excellent', color: 'bg-green-100 text-green-800' };
        if (score >= 1.0) return { label: 'Good', color: 'bg-blue-100 text-blue-800' };
        if (score >= 0.5) return { label: 'Fair', color: 'bg-yellow-100 text-yellow-800' };
        return { label: 'Low', color: 'bg-gray-100 text-gray-800' };
    };

    return (
        <div className="min-h-screen bg-white font-inter">
            <Navbar />

            
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
                

                {/* Query Profile Display - shows what's being searched */}
                {recommendations.length > 0 && (
                    <Card className="rounded-3xl border-2 border-[#1E3A8A]/20 shadow-lg mb-8">
                        <CardContent className="p-6">
                            <div className="flex items-center gap-3 mb-4">
                                <div className="w-12 h-12 bg-gradient-to-br from-[#1E3A8A] to-[#581C87] rounded-xl flex items-center justify-center">
                                    <Target className="w-6 h-6 text-white" />
                                </div>
                                <div>
                                    <h3 className="text-lg heading text-[#111827]">Current Search Profile</h3>
                                    <p className="text-sm body text-gray-600">Matching against {recommendations.length} similar investors</p>
                                </div>
                            </div>
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                                <div className="bg-white rounded-xl p-3 border border-gray-200">
                                    <p className="text-xs body text-gray-500 mb-1">Capital Band</p>
                                    <p className="text-base heading text-[#111827] font-bold">{profile.capital_band}</p>
                                </div>
                                <div className="bg-white rounded-xl p-3 border border-gray-200">
                                    <p className="text-xs body text-gray-500 mb-1">Expected ROI</p>
                                    <p className="text-base heading text-[#111827] font-bold capitalize">{profile.expected_roi_band}</p>
                                </div>
                                <div className="bg-white rounded-xl p-3 border border-gray-200">
                                    <p className="text-xs body text-gray-500 mb-1">Holding Period</p>
                                    <p className="text-base heading text-[#111827] font-bold capitalize">{profile.holding_period_band}</p>
                                </div>
                                <div className="bg-white rounded-xl p-3 border border-gray-200">
                                    <p className="text-xs body text-gray-500 mb-1">City Tier</p>
                                    <p className="text-base heading text-[#111827] font-bold">{profile.city_tier}</p>
                                </div>
                                <div className="bg-white rounded-xl p-3 border border-gray-200">
                                    <p className="text-xs body text-gray-500 mb-1">Risk</p>
                                    <p className="text-base heading text-[#111827] font-bold">{profile.risk_orientation.toFixed(1)}</p>
                                </div>
                                <div className="bg-white rounded-xl p-3 border border-gray-200">
                                    <p className="text-xs body text-gray-500 mb-1">Collaboration</p>
                                    <p className="text-base heading text-[#111827] font-bold">{profile.collaboration_comfort.toFixed(1)}</p>
                                </div>
                                <div className="bg-white rounded-xl p-3 border border-gray-200">
                                    <p className="text-xs body text-gray-500 mb-1">Control</p>
                                    <p className="text-base heading text-[#111827] font-bold">{profile.control_preference.toFixed(1)}</p>
                                </div>
                                <div className="bg-white rounded-xl p-3 border border-gray-200">
                                    <p className="text-xs body text-gray-500 mb-1">RE Conviction</p>
                                    <p className="text-base heading text-[#111827] font-bold">{profile.re_conviction.toFixed(1)}</p>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                )}

                <div className="grid md:grid-cols-3 gap-8">
                    {/* Input Form */}
                    <div className="md:col-span-1">
                        <Card className="rounded-3xl border-2 border-[#581C87]/20 shadow-lg sticky top-8">
                            <CardHeader>
                                <CardTitle className="text-2xl heading text-[#111827] flex items-center gap-2">
                                    <Users className="w-6 h-6 text-[#581C87]" />
                                    Investor Profile
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-6">
                                <div>
                                    <label className="block text-sm heading text-[#111827] mb-2 flex items-center gap-2">
                                        <DollarSign className="w-4 h-4 text-[#581C87]" />
                                        Capital Band (0-4)
                                    </label>
                                    <input
                                        type="number"
                                        min="0"
                                        max="4"
                                        value={profile.capital_band}
                                        onChange={(e) => handleInputChange('capital_band', parseInt(e.target.value))}
                                        className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-[#581C87] focus:outline-none transition-colors"
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm heading text-[#111827] mb-2 flex items-center gap-2">
                                        <TrendingUp className="w-4 h-4 text-[#581C87]" />
                                        Expected ROI
                                    </label>
                                    <select
                                        value={profile.expected_roi_band}
                                        onChange={(e) => handleInputChange('expected_roi_band', e.target.value)}
                                        className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-[#581C87] focus:outline-none transition-colors"
                                    >
                                        <option value="low">Low (5-10%)</option>
                                        <option value="medium">Medium (10-15%)</option>
                                        <option value="high">High (15%+)</option>
                                    </select>
                                </div>

                                <div>
                                    <label className="block text-sm heading text-[#111827] mb-2 flex items-center gap-2">
                                        <Clock className="w-4 h-4 text-[#581C87]" />
                                        Holding Period
                                    </label>
                                    <select
                                        value={profile.holding_period_band}
                                        onChange={(e) => handleInputChange('holding_period_band', e.target.value)}
                                        className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-[#581C87] focus:outline-none transition-colors"
                                    >
                                        <option value="short">Short (0-2 years)</option>
                                        <option value="medium">Medium (2-5 years)</option>
                                        <option value="long">Long (5+ years)</option>
                                    </select>
                                </div>

                                <div>
                                    <label className="block text-sm heading text-[#111827] mb-2">
                                        Risk Orientation: <span className="text-[#581C87] font-bold">{profile.risk_orientation.toFixed(1)}</span>
                                    </label>
                                    <input
                                        type="range"
                                        min="0"
                                        max="1"
                                        step="0.1"
                                        value={profile.risk_orientation}
                                        onChange={(e) => handleInputChange('risk_orientation', parseFloat(e.target.value))}
                                        className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-[#581C87]"
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm heading text-[#111827] mb-2">
                                        Collaboration Comfort: <span className="text-[#581C87] font-bold">{profile.collaboration_comfort.toFixed(1)}</span>
                                    </label>
                                    <input
                                        type="range"
                                        min="0"
                                        max="1"
                                        step="0.1"
                                        value={profile.collaboration_comfort}
                                        onChange={(e) => handleInputChange('collaboration_comfort', parseFloat(e.target.value))}
                                        className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-[#581C87]"
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm heading text-[#111827] mb-2 flex items-center gap-2">
                                        <Target className="w-4 h-4 text-[#581C87]" />
                                        Top K Results
                                    </label>
                                    <input
                                        type="number"
                                        min="1"
                                        max="50"
                                        value={topK}
                                        onChange={(e) => setTopK(parseInt(e.target.value))}
                                        className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-[#581C87] focus:outline-none transition-colors"
                                    />
                                </div>

                                <Button
                                    onClick={getRecommendations}
                                    disabled={loading}
                                    className="w-full bg-[#581C87] hover:bg-[#581C87]/90 text-white py-6 text-base font-medium shadow-lg hover:shadow-xl transition-all rounded-xl"
                                >
                                    {loading ? (
                                        <>
                                            <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                            </svg>
                                            Finding Matches...
                                        </>
                                    ) : (
                                        <>
                                            <Brain className="w-5 h-5 mr-2" />
                                            Find Similar Investors
                                        </>
                                    )}
                                </Button>
                            </CardContent>
                        </Card>
                    </div>

                    {/* Results */}
                    <div className="md:col-span-2">
                        <Card className="rounded-3xl border-0 shadow-lg">
                            <CardHeader>
                                <div className="flex items-start justify-between">
                                    <div className="flex items-center gap-2">
                                        <TrendingUp className="w-6 h-6 text-[#1E3A8A]" />
                                        <div>
                                            <CardTitle className="text-2xl heading text-[#111827]">
                                                Top {topK} Similar Investors
                                            </CardTitle>
                                            <p className="text-sm body text-gray-600 mt-1">
                                                Ranked by multi-feature similarity (not exact matches)
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            </CardHeader>
                            <CardContent>
                                {/* Info Box - How Matching Works */}
                                {recommendations.length > 0 && (
                                    <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-2xl p-4 mb-4 border border-blue-100">
                                        <div className="flex items-start gap-3">
                                            <Brain className="w-5 h-5 text-[#1E3A8A] mt-0.5 flex-shrink-0" />
                                            <div>
                                                <p className="text-sm heading text-[#111827] mb-1">
                                                    💡 How ML Matching Works
                                                </p>
                                                <p className="text-xs body text-gray-700 leading-relaxed">
                                                    Results are ranked by <strong>overall similarity</strong> across all features (capital, ROI, holding period, risk tolerance, collaboration style, etc.). 
                                                    Top matches may not match <em>every</em> criterion exactly, but are most compatible <strong>holistically</strong>.
                                                </p>
                                            </div>
                                        </div>
                                    </div>
                                )}

                                {recommendations.length === 0 ? (
                                    <div className="text-center py-16">
                                        <div className="w-24 h-24 bg-gradient-to-br from-[#581C87]/10 to-[#1E3A8A]/10 rounded-full flex items-center justify-center mx-auto mb-4">
                                            <Users className="w-12 h-12 text-[#581C87]" />
                                        </div>
                                        <p className="text-lg body text-gray-600">
                                            Configure your profile and click "Find Similar Investors"
                                        </p>
                                    </div>
                                ) : (
                                    <div className="space-y-3">
                                        {recommendations.map((match, index) => (
                                            <div
                                                key={match.investor_id}
                                                className="bg-gradient-to-r from-gray-50 to-white rounded-2xl p-5 border border-gray-100 hover:border-[#581C87]/30 hover:shadow-md transition-all"
                                            >
                                                <div className="flex items-center justify-between mb-3">
                                                    <div className="flex items-center gap-3">
                                                        <div className="w-10 h-10 bg-gradient-to-br from-[#581C87] to-[#1E3A8A] rounded-xl flex items-center justify-center shadow">
                                                            <span className="text-white font-bold text-sm">#{index + 1}</span>
                                                        </div>
                                                        <div>
                                                            <p className="text-xs body text-gray-500 uppercase">Investor ID</p>
                                                            <p className="text-sm heading text-[#111827] font-mono">{match.investor_id.substring(0, 12)}...</p>
                                                        </div>
                                                    </div>
                                                    <div className="flex flex-col items-end gap-1">
                                                        <Badge
                                                            className={`px-4 py-2 text-sm font-bold ${getMatchQuality(match.similarity_score).color}`}
                                                        >
                                                            {getMatchQuality(match.similarity_score).label} Match
                                                        </Badge>
                                                        <span className="text-xs body text-gray-500">
                                                            Score: {match.similarity_score.toFixed(3)}
                                                        </span>
                                                    </div>
                                                </div>
                                                <div className="grid grid-cols-3 gap-3">
                                                    <div className="bg-white rounded-xl p-3 border border-gray-100">
                                                        <p className="text-xs body text-gray-500 mb-1">Capital</p>
                                                        <p className="text-sm heading text-[#111827] font-medium">Band {match.capital_band}</p>
                                                    </div>
                                                    <div className="bg-white rounded-xl p-3 border border-gray-100">
                                                        <p className="text-xs body text-gray-500 mb-1">ROI</p>
                                                        <p className="text-sm heading text-[#111827] font-medium capitalize">{match.expected_roi_band}</p>
                                                    </div>
                                                    <div className="bg-white rounded-xl p-3 border border-gray-100">
                                                        <p className="text-xs body text-gray-500 mb-1">Holding</p>
                                                        <p className="text-sm heading text-[#111827] font-medium capitalize">{match.holding_period_band}</p>
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </CardContent>
                        </Card>
                    </div>
                </div>
            </div>

            <Footer />
        </div>
    );
};

export default MLInvestorSimilarity;
