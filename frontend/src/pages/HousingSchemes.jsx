import React from 'react'
import Navbar from '@/components/Navbar.jsx'
import Footer from '@/components/Footer.jsx'
import HousingSchemeBot from '@/components/HousingSchemes.jsx'

function HousingSchemes() {
  return (
    <div className="min-h-screen bg-[#F9FAFB] font-inter flex flex-col">
      <Navbar />
      <main className="flex-1">
        <HousingSchemeBot/>
      </main>
      <Footer />
    </div>
  )
}

export default HousingSchemes

