import { useState } from 'react'
import { Loader2 } from 'lucide-react'
import Navbar from '@/components/Navbar.jsx'
import Footer from '@/components/Footer.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Input } from '@/components/ui/input.jsx'
import { Button } from '@/components/ui/button.jsx'
import { apiUrl } from '@/lib/api.js'

export default function StepUp() {
  const [formData, setFormData] = useState({
    buyerBudgetMax: '',
    buyerRisk: '',
    location: ''
  })
  const [loading, setLoading] = useState(false)
  const [recommendations, setRecommendations] = useState(null)

  const handleChange = (e) => {
    setFormData((prev) => ({ ...prev, [e.target.name]: e.target.value }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setRecommendations(null)

    try {
      const response = await fetch(apiUrl('/api/recommend'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          buyerBudgetMax: Number(formData.buyerBudgetMax),
          buyerRisk: Number(formData.buyerRisk),
          location: formData.location
        })
      })

      if (!response.ok) throw new Error(`Error: ${response.status}`)

      const data = await response.json()
      setRecommendations(data.recommendations || [])
    } catch (err) {
      console.error('StepUp recommendations failed:', err)
      alert('Error fetching recommendations from backend.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-[#F9FAFB] font-inter flex flex-col">
      <Navbar />

      <section className="flex-1 py-20 px-4">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-10">
            <Badge className="bg-[#581C87] text-white px-4 py-2 text-sm font-medium mb-6">
              Step-Up: Smart Matchmaking
            </Badge>
            <h1 className="text-4xl heading text-accent-gray mb-4">
              Find Your Perfect Investor Match
            </h1>
            <p className="text-gray-600 text-lg max-w-2xl mx-auto">
              Enter your homebuying profile and let our ML model find compatible investors for your journey.
            </p>
          </div>

          <Card className="rounded-3xl shadow-lg border-0 bg-white/90">
            <CardContent className="p-10">
              <form onSubmit={handleSubmit} className="grid md:grid-cols-3 gap-6 items-end justify-center">
                <div className="flex flex-col">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Buyer Budget Max (INR)
                  </label>
                  <Input
                    type="number"
                    name="buyerBudgetMax"
                    placeholder="e.g. 25000000"
                    value={formData.buyerBudgetMax}
                    onChange={handleChange}
                    required
                  />
                </div>

                <div className="flex flex-col">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Buyer Risk (0 = Low, 1 = Medium, 2 = High)
                  </label>
                  <Input
                    type="number"
                    name="buyerRisk"
                    placeholder="e.g. 1"
                    value={formData.buyerRisk}
                    onChange={handleChange}
                    required
                  />
                </div>

                <div className="flex flex-col">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Location (e.g. Bandra West)
                  </label>
                  <Input
                    type="text"
                    name="location"
                    placeholder="e.g. Bandra West"
                    value={formData.location}
                    onChange={handleChange}
                    required
                  />
                </div>

                <div className="md:col-span-3 flex justify-center mt-6">
                  <Button
                    type="submit"
                    className="w-full bg-[#581C87] hover:bg-[#581C87]/90 text-white shadow-md transition-all active:scale-[0.98]"
                    disabled={loading}
                  >
                    {loading ? <Loader2 className="w-6 h-6 animate-spin" /> : 'Find Matches'}
                  </Button>
                </div>
              </form>

              {recommendations && (
                <div className="text-center mt-16">
                  <h2 className="text-3xl heading text-accent-gray mb-10">Top Investor Matches</h2>

                  <div className="grid md:grid-cols-3 gap-8 justify-center">
                    {recommendations.map((inv, idx) => (
                      <Card
                        key={idx}
                        className="rounded-2xl shadow-md border border-purple-100 bg-gradient-to-b from-purple-50 to-white text-left"
                      >
                        <CardHeader>
                          <CardTitle className="text-lg font-semibold text-[#581C87]">
                            Investor #{inv.investorId}
                          </CardTitle>
                          <p className="text-gray-500 text-sm">{inv.profession}</p>
                        </CardHeader>
                        <CardContent>
                          <p className="text-sm text-gray-600 mb-2">
                            Risk Appetite: <span className="font-medium">{inv.riskAppetite}</span>
                          </p>
                          <p className="text-sm text-gray-600 mb-2">
                            Max Investment: INR {Number(inv.budget || 0).toLocaleString('en-IN')}
                          </p>
                          <p className="text-sm text-gray-600 mb-2">
                            Location Match: {inv.locationMatch ? 'Yes' : 'No'}
                          </p>
                          <Badge className="bg-[#581C87] text-white px-3 py-1">
                            Score: {inv.score}
                          </Badge>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </section>

      <Footer />
    </div>
  )
}
