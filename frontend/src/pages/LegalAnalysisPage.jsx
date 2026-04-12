import React from 'react'
import Navbar from "@/components/Navbar.jsx"
import Footer from "@/components/Footer.jsx"
import LegalDocumentAnalysis from '@/components/LegalDocumentAnalysis.jsx'

function LegalAnalysisPage() {
    return (
        <div className="min-h-screen bg-white font-inter">
            <Navbar />
            <main className="py-8">
                <LegalDocumentAnalysis />
            </main>
            <Footer />
        </div>
    )
}

export default LegalAnalysisPage
