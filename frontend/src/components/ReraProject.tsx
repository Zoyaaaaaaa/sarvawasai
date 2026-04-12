"use client"

import type * as React from "react"
import { useState } from "react"
import { Building2, Loader2, MapPin, AlertCircle, CheckCircle } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { apiUrl } from '@/lib/api.js'

// Types matching the Python backend (project-input-zkmrD.py)
type Probabilities = {
  [label: string]: number // e.g., { "Low Risk": 62.3, "High Risk": 37.7 }
}

type PredictionResponse = {
  prediction: string
  confidence: number
  probabilities: Probabilities
  risk_level: string
  risk_assessment: string // "a | b | c"
  project_analysis: string // "a | b | c"
}

type FormData = {
  project_name: string
  district: string
  taluka: string
  village: string
  location_pin_code: string
  latitude: string // for convenience; combined into location_lat_long
  longitude: string // for convenience; combined into location_lat_long
  number_of_appartments: string
  number_of_booked_appartments: string
  project_area_sqmts: string
  proposed_date_of_completion: string
  revised_proposed_date_of_completion: string
  extended_date_of_completion: string
}

function toNumberOrNull(v: string): number | null {
  if (v === "" || v === null || v === undefined) return null
  const num = Number(v)
  return Number.isFinite(num) ? num : null
}

function ArrayList({ items, icon }: { items: string[]; icon?: React.ReactNode }) {
  if (!items?.length) return null
  return (
    <div className="space-y-2">
      {items.map((it, i) => (
        <div key={i} className="flex items-start gap-2 text-sm text-foreground">
          {icon ? <span className="mt-0.5">{icon}</span> : null}
          <p className="text-muted-foreground">{it}</p>
        </div>
      ))}
    </div>
  )
}

function KeyStat({
  label,
  value,
  emphasis = false,
}: {
  label: string
  value: string
  emphasis?: boolean
}) {
  return (
    <div className="rounded-md border border-border p-3 bg-card">
      <p className="text-xs text-muted-foreground mb-1">{label}</p>
      <p className={emphasis ? "text-lg font-semibold text-foreground" : "text-base font-medium text-foreground"}>
        {value}
      </p>
    </div>
  )
}

export default function ReraPredictor() {
  const [formData, setFormData] = useState<FormData>({
    project_name: "",
    district: "",
    taluka: "",
    village: "",
    location_pin_code: "",
    latitude: "",
    longitude: "",
    number_of_appartments: "",
    number_of_booked_appartments: "",
    project_area_sqmts: "",
    proposed_date_of_completion: "",
    revised_proposed_date_of_completion: "",
    extended_date_of_completion: "",
  })

  const [prediction, setPrediction] = useState<PredictionResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleChange = (name: keyof FormData) => (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData((prev) => ({ ...prev, [name]: e.target.value }))
  }

  function buildPayload() {
    // Backend expects: location_lat_long as a string, numbers as floats
    const location_lat_long =
      formData.latitude && formData.longitude ? `${formData.latitude}, ${formData.longitude}` : null

    return {
      project_name: formData.project_name || null,
      district: formData.district || null,
      taluka: formData.taluka || null,
      village: formData.village || null,
      location_pin_code: formData.location_pin_code || null,
      location_lat_long,
      number_of_appartments: toNumberOrNull(formData.number_of_appartments),
      number_of_booked_appartments: toNumberOrNull(formData.number_of_booked_appartments),
      project_area_sqmts: toNumberOrNull(formData.project_area_sqmts),
      proposed_date_of_completion: formData.proposed_date_of_completion || null,
      revised_proposed_date_of_completion: formData.revised_proposed_date_of_completion || null,
      extended_date_of_completion: formData.extended_date_of_completion || null,
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setPrediction(null)

    try {
      const payload = buildPayload()
      // console.log("[v0] Submitting payload:", payload)

      const res = await fetch(apiUrl('/ai/predict'), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      })

      if (!res.ok) {
        throw new Error(`Prediction failed (${res.status})`)
      }

      const data: PredictionResponse = await res.json()
      setPrediction(data)
    } catch (err: any) {
      setError(err?.message || "Something went wrong")
    } finally {
      setLoading(false)
    }
  }

  const low = prediction?.probabilities ? prediction.probabilities["Low Risk"] : undefined
  const high = prediction?.probabilities ? prediction.probabilities["High Risk"] : undefined
  const riskChipsColor = prediction?.prediction === "Low Risk" ? "text-foreground" : "text-foreground"

  const assessmentList = prediction?.risk_assessment ? prediction.risk_assessment.split(" | ").filter(Boolean) : []

  const analysisList = prediction?.project_analysis ? prediction.project_analysis.split(" | ").filter(Boolean) : []

  return (
    <div className="mx-auto w-full max-w-7xl px-4 sm:px-6 lg:px-8 py-8">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-foreground text-balance">RERA Project Analysis</h1>
        <p className="text-muted-foreground">Enter project details for AI-powered completion risk evaluation</p>
      </header>

      <div className="grid lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-foreground">Project Details</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6" aria-live="polite">
              {/* Basic */}
              <div className="grid md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="project_name">Project name</Label>
                  <Input
                    id="project_name"
                    value={formData.project_name}
                    onChange={handleChange("project_name")}
                    placeholder="e.g., Skyline Residency"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="district">District</Label>
                  <Input
                    id="district"
                    value={formData.district}
                    onChange={handleChange("district")}
                    placeholder="e.g., Mumbai Suburban"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="taluka">Taluka (optional)</Label>
                  <Input
                    id="taluka"
                    value={formData.taluka}
                    onChange={handleChange("taluka")}
                    placeholder="e.g., Andheri"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="village">Village (optional)</Label>
                  <Input
                    id="village"
                    value={formData.village}
                    onChange={handleChange("village")}
                    placeholder="e.g., Versova"
                  />
                </div>
              </div>

              <Separator />

              {/* Location */}
              <div className="grid md:grid-cols-3 gap-4">
                <div className="space-y-2 md:col-span-1">
                  <Label htmlFor="pin">PIN code</Label>
                  <Input
                    id="pin"
                    inputMode="numeric"
                    pattern="[0-9]*"
                    value={formData.location_pin_code}
                    onChange={handleChange("location_pin_code")}
                    placeholder="e.g., 400018"
                    aria-describedby="pin-help"
                  />
                  <p id="pin-help" className="text-xs text-muted-foreground">
                    6-digit PIN (optional)
                  </p>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="lat">Latitude (optional)</Label>
                  <Input
                    id="lat"
                    inputMode="decimal"
                    value={formData.latitude}
                    onChange={handleChange("latitude")}
                    placeholder="e.g., 19.0760"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="lng">Longitude (optional)</Label>
                  <Input
                    id="lng"
                    inputMode="decimal"
                    value={formData.longitude}
                    onChange={handleChange("longitude")}
                    placeholder="e.g., 72.8777"
                  />
                </div>
              </div>

              <Separator />

              {/* Scale */}
              <div className="grid md:grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="units">Total apartments</Label>
                  <Input
                    id="units"
                    inputMode="numeric"
                    pattern="[0-9]*"
                    value={formData.number_of_appartments}
                    onChange={handleChange("number_of_appartments")}
                    placeholder="e.g., 150"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="booked">Booked apartments</Label>
                  <Input
                    id="booked"
                    inputMode="numeric"
                    pattern="[0-9]*"
                    value={formData.number_of_booked_appartments}
                    onChange={handleChange("number_of_booked_appartments")}
                    placeholder="e.g., 120"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="area">Project area (sq.m)</Label>
                  <Input
                    id="area"
                    inputMode="decimal"
                    value={formData.project_area_sqmts}
                    onChange={handleChange("project_area_sqmts")}
                    placeholder="e.g., 15000"
                  />
                </div>
              </div>

              <Separator />

              {/* Timeline */}
              <div className="grid md:grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="proposed">Proposed completion date</Label>
                  <Input
                    id="proposed"
                    type="date"
                    value={formData.proposed_date_of_completion}
                    onChange={handleChange("proposed_date_of_completion")}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="revised">Revised completion date</Label>
                  <Input
                    id="revised"
                    type="date"
                    value={formData.revised_proposed_date_of_completion}
                    onChange={handleChange("revised_proposed_date_of_completion")}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="extended">Extended completion date</Label>
                  <Input
                    id="extended"
                    type="date"
                    value={formData.extended_date_of_completion}
                    onChange={handleChange("extended_date_of_completion")}
                  />
                </div>
              </div>

              <Button type="submit" disabled={loading} className="w-full">
                {loading ? (
                  <span className="inline-flex items-center gap-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Analyzing...
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-2">
                    <Building2 className="h-4 w-4" />
                    Analyze Project
                  </span>
                )}
              </Button>

              {error && (
                <div role="alert" className="rounded-md border border-border bg-card p-4">
                  <div className="flex items-start gap-2">
                    <AlertCircle className="h-5 w-5" aria-hidden />
                    <div>
                      <p className="font-medium text-foreground">Error</p>
                      <p className="text-sm text-muted-foreground">{error}</p>
                    </div>
                  </div>
                </div>
              )}
            </form>
          </CardContent>
        </Card>

        {/* Results */}
        <div className="space-y-6">
          {!prediction && !loading && !error && (
            <Card>
              <CardContent className="py-10 text-center">
                <Building2 className="h-12 w-12 mx-auto mb-3 opacity-50" />
                <p className="text-muted-foreground">Fill in the details and click “Analyze Project” to see results.</p>
              </CardContent>
            </Card>
          )}

          {prediction && (
            <>
              <Card>
                <CardHeader>
                  <CardTitle className="text-foreground">Prediction</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center gap-3">
                    {prediction.prediction === "Low Risk" ? (
                      <CheckCircle className="h-6 w-6" aria-hidden />
                    ) : (
                      <AlertCircle className="h-6 w-6" aria-hidden />
                    )}
                    <div>
                      <p className="text-lg font-semibold text-foreground">{prediction.prediction}</p>
                      <p className="text-sm text-muted-foreground">Confidence: {prediction.confidence.toFixed(1)}%</p>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <KeyStat label="Low Risk" value={low !== undefined ? `${low.toFixed(1)}%` : "—"} />
                    <KeyStat label="High Risk" value={high !== undefined ? `${high.toFixed(1)}%` : "—"} />
                    <KeyStat label="Risk Level" value={prediction.risk_level} emphasis />
                  </div>
                </CardContent>
              </Card>

              {formData.latitude && formData.longitude && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-foreground">Project Location</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="rounded-md border border-border bg-muted h-48 flex items-center justify-center relative overflow-hidden">
                      <div className="absolute inset-0 opacity-20" />
                      <div className="relative z-10 text-center">
                        <MapPin className="h-8 w-8 mx-auto mb-2" />
                        <p className="text-sm text-muted-foreground">
                          Lat: {Number(formData.latitude).toFixed(4)} | Lng: {Number(formData.longitude).toFixed(4)}
                        </p>
                        <p className="text-xs text-muted-foreground mt-1">{formData.district || "Location"}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}

              <Card>
                <CardHeader>
                  <CardTitle className="text-foreground">Risk Assessment</CardTitle>
                </CardHeader>
                <CardContent>
                  <ArrayList
                    items={assessmentList}
                    icon={<span className="inline-block h-2 w-2 rounded-full bg-foreground" />}
                  />
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-foreground">Project Analysis</CardTitle>
                </CardHeader>
                <CardContent>
                  <ArrayList items={analysisList} icon={<CheckCircle className="h-4 w-4" aria-hidden />} />
                </CardContent>
              </Card>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
