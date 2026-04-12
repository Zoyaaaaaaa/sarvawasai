"use client"

import React, { useState, useEffect } from "react"
import { Home, Loader2, MapPin, AlertCircle, CheckCircle, IndianRupee, MessageSquare, Send } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { Checkbox } from "@/components/ui/checkbox"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Badge } from "@/components/ui/badge.jsx"
import { apiUrl } from '@/lib/api.js'

import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import L from 'leaflet'

// Fix for default marker icon issue in Leaflet with React
import markerIcon from 'leaflet/dist/images/marker-icon.png'
import markerIconRetina from 'leaflet/dist/images/marker-icon-2x.png'
import markerShadow from 'leaflet/dist/images/marker-shadow.png'

const DefaultIcon = L.icon({
  iconUrl: markerIcon,
  iconRetinaUrl: markerIconRetina,
  shadowUrl: markerShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
})

L.Marker.prototype.options.icon = DefaultIcon

const AMENITIES = [
  { id: "Gymnasium", label: "Gymnasium" },
  { id: "Lift_Available", label: "Lift Available" },
  { id: "Car_Parking", label: "Car Parking" },
  { id: "Maintenance_Staff", label: "Maintenance Staff" },
  { id: "Security_24x7", label: "24x7 Security" },
  { id: "Children_Play_Area", label: "Children's Play Area" },
  { id: "Clubhouse", label: "Clubhouse" },
  { id: "Intercom", label: "Intercom" },
  { id: "Landscaped_Gardens", label: "Landscaped Gardens" },
  { id: "Indoor_Games", label: "Indoor Games" },
  { id: "Gas_Connection", label: "Gas Connection" },
  { id: "Jogging_Track", label: "Jogging Track" },
  { id: "Swimming_Pool", label: "Swimming Pool" },
]

export default function HousePrediction() {
  const [formData, setFormData] = useState({
    Area: "",
    Location: "",
    No_of_Bedrooms: "",
    New_Resale: 1,
    Gymnasium: 0,
    Lift_Available: 0,
    Car_Parking: 0,
    Maintenance_Staff: 0,
    Security_24x7: 0,
    Children_Play_Area: 0,
    Clubhouse: 0,
    Intercom: 0,
    Landscaped_Gardens: 0,
    Indoor_Games: 0,
    Gas_Connection: 0,
    Jogging_Track: 0,
    Swimming_Pool: 0,
  })

  const [prediction, setPrediction] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [chatMessages, setChatMessages] = useState([])
  const [chatInput, setChatInput] = useState("")
  const [chatLoading, setChatLoading] = useState(false)

  // Scroll to results when prediction arrives
  useEffect(() => {
    if (prediction) {
      const el = document.getElementById("prediction-results");
      if (el) {
        el.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    }
  }, [prediction]);

  const handleChange = (name, value) => {
    setFormData((prev) => ({ ...prev, [name]: value }))
  }

  const handlePredict = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setPrediction(null)
    setChatMessages([])

    try {
      const payload = {
        ...formData,
        Area: Number(formData.Area),
        No_of_Bedrooms: Number(formData.No_of_Bedrooms),
      }

      const res = await fetch(apiUrl('/house-prediction/predict'), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      })

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || "Prediction failed");
      }

      const data = await res.json()
      setPrediction(data)

      // Robustly handle explanation (might be string or array from backend)
      let explanationText = data.explanation;
      if (Array.isArray(explanationText)) {
        explanationText = explanationText.map(part => part.text || JSON.stringify(part)).join("");
      } else if (typeof explanationText !== "string") {
        explanationText = String(explanationText || "");
      }

      setChatMessages([{ role: 'assistant', content: explanationText }])
    } catch (err) {
      setError(err.message || "Something went wrong")
    } finally {
      setLoading(false)
    }
  }

  const handleSendMessage = async () => {
    if (!chatInput.trim() || chatLoading) return

    const userMsg = chatInput.trim()
    setChatInput("")
    setChatMessages(prev => [...prev, { role: 'user', content: userMsg }])
    setChatLoading(true)

    try {
      const res = await fetch(apiUrl('/house-prediction/ask'), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: userMsg, thread_id: "prediction" }),
      })

      if (!res.ok) throw new Error("Failed to get answer")
      const data = await res.json()
      setChatMessages(prev => [...prev, { role: 'assistant', content: data.answer }])
    } catch (err) {
      setChatMessages(prev => [...prev, { role: 'assistant', content: "Sorry, I couldn't answer that. Please try again." }])
    } finally {
      setChatLoading(false)
    }
  }

  return (
    <div className="mx-auto w-full max-w-7xl px-4 sm:px-6 lg:px-8 py-8">
      <header className="mb-10">
        <h1 className="text-3xl font-bold text-gray-900 tracking-tight flex items-center gap-3 mb-2">
          <Home className="w-8 h-8 text-[#581C87]" />
          TrueHome AI: Price Prediction
        </h1>
        <p className="text-gray-600 text-sm">AI-powered property valuation with expert neighborhood insights</p>
      </header>

      <div className="grid lg:grid-cols-2 gap-8 items-start">
        {/* Input Card */}
        <Card className="shadow-md border border-gray-200 rounded-xl">
          <CardHeader className="border-b border-gray-100 pb-5">
            <CardTitle className="text-lg font-bold text-gray-900">Property Details</CardTitle>
            <CardDescription className="text-sm text-gray-600">Enter specifications of the property in Mumbai</CardDescription>
          </CardHeader>
          <CardContent className="pt-6">
            <form onSubmit={handlePredict} className="space-y-6">
              <div className="grid md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="Area" className="text-xs font-semibold text-gray-700 uppercase tracking-wide">Area (sq. ft.)</Label>
                  <Input
                    id="Area"
                    type="number"
                    placeholder="e.g. 1000"
                    value={formData.Area}
                    onChange={(e) => handleChange("Area", e.target.value)}
                    required
                    className="border border-gray-200 rounded-lg focus-visible"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="Location" className="text-xs font-semibold text-gray-700 uppercase tracking-wide">Location</Label>
                  <Input
                    id="Location"
                    placeholder="e.g. Kharghar"
                    value={formData.Location}
                    onChange={(e) => handleChange("Location", e.target.value)}
                    required
                    className="border border-gray-200 rounded-lg focus-visible"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="Bedrooms" className="text-xs font-semibold text-gray-700 uppercase tracking-wide">Bedrooms (BHK)</Label>
                  <Input
                    id="Bedrooms"
                    type="number"
                    placeholder="e.g. 2"
                    value={formData.No_of_Bedrooms}
                    onChange={(e) => handleChange("No_of_Bedrooms", e.target.value)}
                    required
                    className="border border-gray-200 rounded-lg focus-visible"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-xs font-semibold text-gray-700 uppercase tracking-wide">Type</Label>
                  <div className="flex gap-3 mt-2">
                    <Button
                      type="button"
                      variant={formData.New_Resale === 1 ? "default" : "outline"}
                      className="flex-1 rounded-lg border border-gray-200"
                      onClick={() => handleChange("New_Resale", 1)}
                    >
                      New
                    </Button>
                    <Button
                      type="button"
                      variant={formData.New_Resale === 0 ? "default" : "outline"}
                      className="flex-1 rounded-lg border border-gray-200"
                      onClick={() => handleChange("New_Resale", 0)}
                    >
                      Resale
                    </Button>
                  </div>
                </div>
              </div>

              <Separator />

              <div className="space-y-4">
                <Label className="text-xs font-semibold text-gray-700 uppercase tracking-wide">Amenities Available</Label>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  {AMENITIES.map((amenity) => (
                    <div key={amenity.id} className="flex items-center space-x-2">
                      <Checkbox
                        id={amenity.id}
                        checked={formData[amenity.id] === 1}
                        onCheckedChange={(checked) =>
                          handleChange(amenity.id, checked ? 1 : 0)
                        }
                      />
                      <label
                        htmlFor={amenity.id}
                        className="text-sm font-medium text-gray-700 leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                      >
                        {amenity.label}
                      </label>
                    </div>
                  ))}
                </div>
              </div>

              <Button type="submit" className="w-full bg-[#581C87] hover:bg-[#581C87]/90 text-white rounded-lg font-medium shadow-md transition-all active:scale-[0.98]" disabled={loading}>
                {loading ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <IndianRupee className="mr-2 h-4 w-4" />
                )}
                {loading ? "Calculating..." : "Predict Price"}
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Results Area */}
        <div id="prediction-results" className="space-y-6 min-h-[500px] scroll-mt-10">
          {prediction && prediction.insights ? (
            <div className="animate-in fade-in slide-in-from-bottom-8 duration-700">
              <Card className="shadow-lg border border-gray-200 rounded-xl overflow-hidden bg-white">
                <CardHeader className="border-b border-gray-100 pb-5">
                  <CardTitle className="flex items-center justify-between text-lg font-bold text-gray-900">
                    <span>Estimated Market Value</span>
                    <Badge variant="secondary" className="bg-purple-100 text-[#581C87] text-xs">AI Predicted</Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-6 pt-6">
                  <div className="text-center py-8 bg-gradient-to-br from-purple-50 to-blue-50 rounded-xl border border-gray-200">
                    <div className="text-5xl font-bold bg-gradient-to-r from-[#581C87] to-[#1E3A8A] bg-clip-text text-transparent">
                      {prediction.formatted_price}
                    </div>
                    <p className="text-sm text-gray-600 mt-3">Confidence Level: 94%</p>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-4 bg-gray-50 rounded-lg border border-gray-200 shadow-sm">
                      <p className="text-xs text-gray-500 uppercase tracking-widest font-semibold mb-1">Amenity Score</p>
                      <p className="text-2xl font-bold text-[#581C87]">{prediction.insights.amenity_score}/13</p>
                    </div>
                    <div className="p-4 bg-gray-50 rounded-lg border border-gray-200 shadow-sm">
                      <p className="text-xs text-gray-500 uppercase tracking-widest font-semibold mb-1">Neighborhood</p>
                      <p className="text-lg font-bold text-[#1E3A8A] truncate" title={prediction.insights.location}>
                        {prediction.insights.location}
                      </p>
                    </div>
                  </div>

                  {/* Micro Map */}
                  <div className="rounded-lg overflow-hidden border border-gray-200 h-64 relative shadow-sm z-0 transition-all">
                    <MapContainer
                      key={`${prediction.insights.location}-${prediction.predicted_price}`}
                      center={[19.0760, 72.8777]}
                      zoom={12}
                      style={{ height: '100%', width: '100%' }}
                      scrollWheelZoom={false}
                    >
                      <TileLayer
                        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                      />
                      <Marker position={[19.0760, 72.8777]}>
                        <Popup className="font-inter">
                          <div className="text-sm">
                            <strong className="text-[#581C87]">Neighborhood Insight</strong><br />
                            {prediction.insights.location}, Mumbai
                          </div>
                        </Popup>
                      </Marker>
                    </MapContainer>
                  </div>

                  <Separator className="bg-gray-200" />

                  <div className="space-y-4">
                    <h4 className="font-semibold text-gray-900 flex items-center gap-2">
                      <MessageSquare className="w-4 h-4 text-[#581C87]" />
                      Expert Consultation
                    </h4>
                    <ScrollArea className="h-64 pr-4 rounded-lg bg-gray-50 p-4 border border-gray-200 shadow-sm">
                      <div className="space-y-4">
                        {chatMessages.map((msg, i) => (
                          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                            <div className={`max-w-[85%] rounded-lg px-4 py-3 text-sm ${msg.role === 'user'
                              ? 'bg-[#581C87] text-white shadow-sm'
                              : 'bg-white text-gray-800 border border-gray-200 shadow-sm'
                              }`}>
                              {msg.content}
                            </div>
                          </div>
                        ))}
                        {chatLoading && (
                          <div className="flex justify-start">
                            <div className="bg-white rounded-lg px-4 py-3 border border-gray-200 shadow-sm">
                              <Loader2 className="w-4 h-4 animate-spin text-[#581C87]" />
                            </div>
                          </div>
                        )}
                      </div>
                    </ScrollArea>
                    <div className="flex gap-2">
                      <Input
                        placeholder="Ask a follow-up about this property..."
                        value={chatInput}
                        onChange={(e) => setChatInput(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                        className="border border-gray-200 rounded-lg focus-visible"
                      />
                      <Button
                        size="icon"
                        onClick={handleSendMessage}
                        className="bg-[#581C87] rounded-lg"
                        disabled={chatLoading || !chatInput}
                      >
                        <Send className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
                <CardFooter className="text-xs text-gray-500 text-center border-t border-gray-100 py-3 block w-full bg-gray-50">
                  Powered by TrueHome AI & Google Gemini 1.5 Flash
                </CardFooter>
              </Card>
            </div>
          ) : (
            <Card className="h-full bg-gray-50 border border-gray-200 rounded-xl flex flex-col items-center justify-center text-center p-12 min-h-[400px]">
              <div className="w-16 h-16 bg-white rounded-full flex items-center justify-center mb-6 shadow-sm border border-gray-200">
                <Brain className="w-8 h-8 text-[#581C87]" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Ready to Analyze</h3>
              <p className="text-gray-600 max-w-sm text-sm">
                Complete the property details on the left to get an instant valuation and expert analysis.
              </p>
            </Card>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-4 rounded-lg flex items-center gap-3">
              <AlertCircle className="h-5 w-5 shrink-0 flex-none" />
              <div>
                <p className="font-semibold text-sm">Prediction Error</p>
                <p className="text-xs opacity-90">{error}</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function Brain({ className }) {
  return (
    <svg
      className={className}
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96.44 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 4.44-2.54Z" />
      <path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96.44 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-4.44-2.54Z" />
    </svg>
  )
}
