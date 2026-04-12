import React from 'react'
import Navbar from "@/components/Navbar.jsx"
import Footer from "@/components/Footer.jsx"
import HousePrediction from '@/components/HousePrediction.jsx'

function HousePredictionPage() {
    return (
        <div className="min-h-screen bg-white font-inter">
            <Navbar />
            <main className="py-12">
                <HousePrediction />
            </main>
            <Footer />
        </div>
    )
}

export default HousePredictionPage