"use client"

import React, { useState, useRef } from "react"
import { FileText, Loader2, AlertCircle, CheckCircle, Scale, BookOpen, Upload, X } from "lucide-react"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { Badge } from "@/components/ui/badge.jsx"
import { ScrollArea } from "@/components/ui/scroll-area"
import { apiUrl } from '@/lib/api.js'

const FOCUS_AREAS = [
  { id: "general", label: "General Legal Review", icon: "📋" },
  { id: "property_transfer", label: "Property Transfer", icon: "🏠" },
  { id: "mortgage", label: "Mortgage Agreement", icon: "🏦" },
  { id: "tenant_rights", label: "Tenant Rights", icon: "👥" },
  { id: "rera_compliance", label: "RERA Compliance", icon: "⚖️" },
]

const LANGUAGES = [
  { id: "english", label: "English" },
  { id: "hindi", label: "हिंदी (Hindi)" },
  { id: "mixed", label: "Mixed (English + Hindi)" },
]

export default function LegalDocumentAnalysis() {
  const [formData, setFormData] = useState({
    focus_area: "general",
    language: "english",
  })

  const [selectedFile, setSelectedFile] = useState(null)
  const [analysis, setAnalysis] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [dragActive, setDragActive] = useState(false)
  const [expandedSections, setExpandedSections] = useState({
    analysis: true,
    keyPoints: true,
    recommendations: true,
    riskFactors: true,
  })
  const fileInputRef = useRef(null)

  const renderMarkdown = (text) => {
    const linkClass = 'text-slate-900 underline hover:text-slate-700'
    const processInline = (line) =>
      line
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/\[(.*?)\]\((https?:\/\/[^\)]+)\)/g, `<a href="$2" target="_blank" rel="noopener noreferrer" class="${linkClass}">$1</a>`)

    const lines = text.split('\n')
    const elements = []
    let listItems = []

    const flushList = () => {
      if (listItems.length > 0) {
        elements.push(
          <ul key={`list-${elements.length}`} className="list-disc list-inside space-y-2 text-slate-700">
            {listItems.map((item, idx) => (
              <li key={idx} className="ml-4" dangerouslySetInnerHTML={{ __html: item }} />
            ))}
          </ul>
        )
        listItems = []
      }
    }

    lines.forEach((line, index) => {
      const trimmed = line.trim()

      if (/^#{1,6}\s+/.test(trimmed)) {
        flushList()
        const level = trimmed.match(/^#{1,6}/)[0].length
        const content = processInline(trimmed.replace(/^#{1,6}\s+/, ''))
        const Tag = `h${Math.min(level + 1, 4)}`
        elements.push(
          <Tag key={index} className="mt-4 mb-3 text-slate-900">
            <span dangerouslySetInnerHTML={{ __html: content }} />
          </Tag>
        )
      } else if (/^([-*•])\s+/.test(trimmed)) {
        listItems.push(processInline(trimmed.replace(/^([-*•])\s+/, '')))
      } else if (trimmed === '') {
        flushList()
        elements.push(<div key={index} className="py-1" />)
      } else {
        flushList()
        elements.push(
          <p key={index} className="mb-3 text-slate-700 leading-relaxed" dangerouslySetInnerHTML={{ __html: processInline(trimmed) }} />
        )
      }
    })

    flushList()
    return elements
  }

  const handleChange = (name, value) => {
    setFormData((prev) => ({ ...prev, [name]: value }))
  }

  const toggleSection = (section) => {
    setExpandedSections((prev) => ({
      ...prev,
      [section]: !prev[section],
    }))
  }

  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    const files = e.dataTransfer.files
    if (files && files[0]) {
      const file = files[0]
      if (file.type === "application/pdf") {
        setSelectedFile(file)
        setError(null)
      } else {
        setError("Please upload a PDF file")
      }
    }
  }

  const handleFileInput = (e) => {
    const file = e.target.files?.[0]
    if (file) {
      if (file.type === "application/pdf") {
        setSelectedFile(file)
        setError(null)
      } else {
        setError("Please upload a PDF file")
      }
    }
  }

  const handleAnalyze = async (e) => {
    e.preventDefault()
    
    if (!selectedFile) {
      setError("Please select a PDF file")
      return
    }

    setLoading(true)
    setError(null)
    setAnalysis(null)

    try {
      const formDataToSend = new FormData()
      formDataToSend.append("file", selectedFile)
      formDataToSend.append("focus_area", formData.focus_area)
      formDataToSend.append("language", formData.language)

      const response = await fetch(apiUrl("/legal/analyze-pdf"), {
        method: "POST",
        credentials: 'include',
        body: formDataToSend,
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || "Analysis failed")
      }

      const result = await response.json()
      setAnalysis(result)

      // Scroll to results
      setTimeout(() => {
        const el = document.getElementById("analysis-results")
        if (el) {
          el.scrollIntoView({ behavior: "smooth", block: "start" })
        }
      }, 100)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      <div className="container mx-auto px-4 py-12 max-w-6xl">
        {/* Header */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-12">
          {/* Form Section */}
          <div>
            <h1 className="text-4xl font-bold text-slate-900 mb-2">Legal Document Analysis</h1>
            <p className="text-slate-600 mb-6">
              Upload your legal documents and get instant AI-powered analysis focused on Indian real estate law and regulations.
            </p>

            <Card className="border-slate-200 shadow-lg">
              <CardHeader className="bg-gradient-to-r from-emerald-50 to-teal-50 border-b border-slate-200">
                <CardTitle className="flex items-center gap-2 text-emerald-800">
                  <FileText className="w-5 h-5" />
                  Document Analysis Form
                </CardTitle>
                <CardDescription>Upload and analyze PDF documents</CardDescription>
              </CardHeader>

              <CardContent className="pt-6">
                <form onSubmit={handleAnalyze} className="space-y-6">
                  {/* File Upload */}
                  <div className="space-y-2">
                    <Label htmlFor="file-upload" className="text-sm font-semibold text-slate-700">
                      Upload PDF Document *
                    </Label>
                    <div
                      onDragEnter={handleDrag}
                      onDragLeave={handleDrag}
                      onDragOver={handleDrag}
                      onDrop={handleDrop}
                      className={`relative border-2 border-dashed rounded-lg p-8 transition-all text-center cursor-pointer ${
                        dragActive
                          ? "border-emerald-500 bg-emerald-50"
                          : "border-slate-300 bg-slate-50 hover:border-slate-400"
                      }`}
                      onClick={() => fileInputRef.current?.click()}
                    >
                      <input
                        ref={fileInputRef}
                        type="file"
                        id="file-upload"
                        accept=".pdf"
                        onChange={handleFileInput}
                        className="hidden"
                        disabled={loading}
                      />
                      
                      {selectedFile ? (
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <FileText className="w-8 h-8 text-emerald-600" />
                            <div className="text-left">
                              <p className="font-medium text-slate-900">{selectedFile.name}</p>
                              <p className="text-sm text-slate-500">
                                {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                              </p>
                            </div>
                          </div>
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation()
                              setSelectedFile(null)
                            }}
                            className="p-1 hover:bg-slate-200 rounded"
                          >
                            <X className="w-5 h-5 text-slate-600" />
                          </button>
                        </div>
                      ) : (
                        <div className="flex flex-col items-center gap-2">
                          <Upload className="w-8 h-8 text-slate-400" />
                          <div>
                            <p className="font-medium text-slate-700">Drag and drop your PDF here</p>
                            <p className="text-sm text-slate-500">or click to browse</p>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>

                  <Separator />

                  {/* Focus Area Selection */}
                  <div className="space-y-3">
                    <Label className="text-sm font-semibold text-slate-700">Focus Area *</Label>
                    <div className="grid grid-cols-1 gap-2">
                      {FOCUS_AREAS.map((area) => (
                        <button
                          key={area.id}
                          type="button"
                          onClick={() => handleChange("focus_area", area.id)}
                          disabled={loading}
                          className={`p-3 rounded-lg border-2 transition-all text-left ${
                            formData.focus_area === area.id
                              ? "border-emerald-500 bg-emerald-50"
                              : "border-slate-200 bg-white hover:border-slate-300"
                          }`}
                        >
                          <div className="flex items-center gap-2">
                            <span className="text-xl">{area.icon}</span>
                            <span className="font-medium text-slate-700">{area.label}</span>
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>

                  <Separator />

                  {/* Language Selection */}
                  <div className="space-y-3">
                    <Label className="text-sm font-semibold text-slate-700">Response Language *</Label>
                    <div className="grid grid-cols-3 gap-2">
                      {LANGUAGES.map((lang) => (
                        <button
                          key={lang.id}
                          type="button"
                          onClick={() => handleChange("language", lang.id)}
                          disabled={loading}
                          className={`p-2 rounded-lg border-2 transition-all text-sm font-medium ${
                            formData.language === lang.id
                              ? "border-blue-500 bg-blue-50 text-blue-700"
                              : "border-slate-200 bg-white text-slate-700 hover:border-slate-300"
                          }`}
                        >
                          {lang.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  <Separator />

                  {/* Additional Info */}
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <p className="text-sm text-blue-800 font-medium mb-2">💡 Analysis Includes:</p>
                    <ul className="text-sm text-blue-700 space-y-1">
                      <li>✓ Executive Summary</li>
                      <li>✓ Key Legal Points</li>
                      <li>✓ Risk Factors & Compliance Status</li>
                      <li>✓ Actionable Recommendations</li>
                    </ul>
                  </div>

                  {/* Error Display */}
                  {error && (
                    <div className="flex gap-3 bg-red-50 border border-red-200 rounded-lg p-4">
                      <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                      <div>
                        <p className="font-semibold text-red-900">Analysis Failed</p>
                        <p className="text-sm text-red-700">{error}</p>
                      </div>
                    </div>
                  )}

                  {/* Submit Button */}
                  <Button
                    type="submit"
                    disabled={loading || !selectedFile}
                    className="w-full bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 text-white font-semibold h-11"
                  >
                    {loading ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Analyzing Document...
                      </>
                    ) : (
                      <>
                        <FileText className="w-4 h-4 mr-2" />
                        Analyze Document
                      </>
                    )}
                  </Button>
                </form>
              </CardContent>
            </Card>
          </div>

          {/* Info Section */}
          <div className="space-y-6">
            <Card className="border-slate-200">
              <CardHeader className="bg-gradient-to-r from-blue-50 to-cyan-50 border-b border-slate-200">
                <CardTitle className="text-blue-900 flex items-center gap-2">
                  <BookOpen className="w-5 h-5" />
                  About This Service
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-6 space-y-4 text-slate-700">
                <p>
                  Our AI-powered legal analysis service specializes in <strong>Indian real estate law</strong>, including:
                </p>
                <ul className="space-y-2 ml-4">
                  <li className="flex gap-2">
                    <span className="text-emerald-600 font-bold">•</span>
                    <span><strong>RERA</strong> (Real Estate Regulation and Development Act)</span>
                  </li>
                  <li className="flex gap-2">
                    <span className="text-emerald-600 font-bold">•</span>
                    <span><strong>Property Transfer</strong> regulations and procedures</span>
                  </li>
                  <li className="flex gap-2">
                    <span className="text-emerald-600 font-bold">•</span>
                    <span><strong>Mortgage Agreements</strong> and loan terms</span>
                  </li>
                  <li className="flex gap-2">
                    <span className="text-emerald-600 font-bold">•</span>
                    <span><strong>Tenant Rights</strong> and landlord obligations</span>
                  </li>
                  <li className="flex gap-2">
                    <span className="text-emerald-600 font-bold">•</span>
                    <span>Stamp Duty and registration laws</span>
                  </li>
                </ul>

                <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mt-6">
                  <p className="text-sm text-amber-900">
                    <strong>⚠️ Note:</strong> This analysis is for informational purposes. For specific legal advice, please consult a qualified attorney.
                  </p>
                </div>
              </CardContent>
            </Card>

            <Card className="border-slate-200 bg-gradient-to-br from-emerald-50 to-teal-50">
              <CardContent className="pt-6">
                <h3 className="font-semibold text-emerald-900 mb-3 flex items-center gap-2">
                  <Scale className="w-5 h-5" />
                  How It Works
                </h3>
                <ol className="space-y-3 text-sm text-slate-700">
                  <li className="flex gap-3">
                    <span className="font-bold text-emerald-600 min-w-6">1</span>
                    <span>Select your PDF file and drag-drop or click to upload</span>
                  </li>
                  <li className="flex gap-3">
                    <span className="font-bold text-emerald-600 min-w-6">2</span>
                    <span>Choose your focus area (general or specific legal aspect)</span>
                  </li>
                  <li className="flex gap-3">
                    <span className="font-bold text-emerald-600 min-w-6">3</span>
                    <span>Select your preferred response language</span>
                  </li>
                  <li className="flex gap-3">
                    <span className="font-bold text-emerald-600 min-w-6">4</span>
                    <span>Click "Analyze Document" to get instant insights</span>
                  </li>
                </ol>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Analysis Results */}
        {analysis && (
          <div id="analysis-results" className="space-y-6">
            <Card className="border-emerald-200 bg-gradient-to-r from-emerald-50 to-teal-50">
              <CardHeader>
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <CardTitle className="text-emerald-900 flex items-center gap-2">
                      <CheckCircle className="w-6 h-6 text-emerald-600" />
                      Analysis Complete
                    </CardTitle>
                    <CardDescription className="text-emerald-700">
                      Model: {analysis.model_used}
                    </CardDescription>
                  </div>
                  <Badge className="bg-emerald-600 hover:bg-emerald-700">
                    {formData.focus_area.replace(/_/g, " ").toUpperCase()}
                  </Badge>
                </div>
              </CardHeader>
            </Card>

            {/* Main Analysis */}
            <Card className="border-slate-200">
              <CardHeader className="bg-slate-50 border-b cursor-pointer hover:bg-slate-100"
                onClick={() => toggleSection("analysis")}
              >
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg">Full Legal Analysis</CardTitle>
                  <span className="text-2xl">{expandedSections.analysis ? "−" : "+"}</span>
                </div>
              </CardHeader>
              {expandedSections.analysis && (
                <CardContent className="pt-6">
                  <ScrollArea className="h-96">
                    <div className="text-slate-700 max-w-none pr-4">
                      {renderMarkdown(analysis.analysis)}
                    </div>
                  </ScrollArea>
                </CardContent>
              )}
            </Card>

            {/* Key Points */}
            {analysis.key_points && analysis.key_points.length > 0 && (
              <Card className="border-blue-200">
                <CardHeader
                  className="bg-blue-50 border-b cursor-pointer hover:bg-blue-100"
                  onClick={() => toggleSection("keyPoints")}
                >
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg text-blue-900">Key Legal Points</CardTitle>
                    <span className="text-2xl">{expandedSections.keyPoints ? "−" : "+"}</span>
                  </div>
                </CardHeader>
                {expandedSections.keyPoints && (
                  <CardContent className="pt-6">
                    <ul className="space-y-3">
                      {analysis.key_points.map((point, idx) => (
                        <li key={idx} className="flex gap-3">
                          <span className="text-blue-600 font-bold">•</span>
                          <span className="text-slate-700">{point}</span>
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                )}
              </Card>
            )}

            {/* Risk Factors */}
            {analysis.risk_factors && analysis.risk_factors.length > 0 && (
              <Card className="border-orange-200">
                <CardHeader
                  className="bg-orange-50 border-b cursor-pointer hover:bg-orange-100"
                  onClick={() => toggleSection("riskFactors")}
                >
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg text-orange-900">⚠️ Risk Factors</CardTitle>
                    <span className="text-2xl">{expandedSections.riskFactors ? "−" : "+"}</span>
                  </div>
                </CardHeader>
                {expandedSections.riskFactors && (
                  <CardContent className="pt-6">
                    <ul className="space-y-3">
                      {analysis.risk_factors.map((risk, idx) => (
                        <li key={idx} className="flex gap-3">
                          <span className="text-orange-600 font-bold">⚠</span>
                          <span className="text-slate-700">{risk}</span>
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                )}
              </Card>
            )}

            {/* Recommendations */}
            {analysis.recommendations && analysis.recommendations.length > 0 && (
              <Card className="border-green-200">
                <CardHeader
                  className="bg-green-50 border-b cursor-pointer hover:bg-green-100"
                  onClick={() => toggleSection("recommendations")}
                >
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg text-green-900">✓ Recommendations</CardTitle>
                    <span className="text-2xl">{expandedSections.recommendations ? "−" : "+"}</span>
                  </div>
                </CardHeader>
                {expandedSections.recommendations && (
                  <CardContent className="pt-6">
                    <ul className="space-y-3">
                      {analysis.recommendations.map((rec, idx) => (
                        <li key={idx} className="flex gap-3">
                          <span className="text-green-600 font-bold">✓</span>
                          <span className="text-slate-700">{rec}</span>
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                )}
              </Card>
            )}

            {/* Actions */}
            <div className="flex gap-4">
              <Button
                onClick={() => {
                  setAnalysis(null)
                  setSelectedFile(null)
                  setFormData({
                    focus_area: "general",
                    language: "english",
                  })
                }}
                variant="outline"
                className="flex-1"
              >
                Analyze Another Document
              </Button>
              <Button
                onClick={() => {
                  const analysisText = `
Legal Analysis Report
=====================
Document: ${selectedFile?.name || "Uploaded Document"}
Focus Area: ${formData.focus_area}
Language: ${formData.language}

${analysis.analysis}

Key Points:
${analysis.key_points.map((p) => `- ${p}`).join("\n")}

Recommendations:
${analysis.recommendations.map((r) => `- ${r}`).join("\n")}

Risk Factors:
${analysis.risk_factors.map((r) => `- ${r}`).join("\n")}
                  `
                  const blob = new Blob([analysisText], { type: "text/plain" })
                  const url = window.URL.createObjectURL(blob)
                  const a = document.createElement("a")
                  a.href = url
                  a.download = "legal-analysis-report.txt"
                  a.click()
                }}
                className="flex-1 bg-blue-600 hover:bg-blue-700"
              >
                Download Report
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
