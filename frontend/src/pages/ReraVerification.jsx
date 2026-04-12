import React from 'react'
import Navbar from '@/components/Navbar.jsx'
import Footer from '@/components/Footer.jsx'
import ReraPredictor from '@/components/ReraProject.tsx'

function ReraVerification() {
  return (
    <div className="min-h-screen bg-white font-inter flex flex-col">
      <Navbar />
      <main className="flex-1">
        <ReraPredictor/>
      </main>
      <Footer />
    </div>
  )
}

export default ReraVerification

