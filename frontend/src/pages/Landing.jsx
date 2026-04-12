import { Home, DollarSign, Brain, Users, ArrowRight, PiggyBank, Building2, Users2 } from 'lucide-react';
import { Button } from "@/components/ui/button.jsx";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card.jsx";
import { Badge } from "@/components/ui/badge.jsx";
import { Accordion, AccordionItem, AccordionTrigger, AccordionContent } from "@/components/ui/accordion.jsx";
import { Link, useNavigate } from 'react-router-dom'
import { useState, useEffect } from 'react';
import Navbar from "@/components/Navbar.jsx";
import Footer from "@/components/Footer.jsx";
import { getDashboardPath, loadAuthSession } from '@/lib/auth.js'

function Landing() {
  const navigate = useNavigate();
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [userRole, setUserRole] = useState(null);

  useEffect(() => {
    const session = loadAuthSession()
    if (session?.userId) {
      setIsLoggedIn(true);
      setUserRole(session.role);
    }
  }, []);

  const handleDashboardClick = () => {
    navigate(getDashboardPath(userRole));
  };
  return (
    <div className="min-h-screen bg-white font-inter">
      <Navbar />


      <section className="relative overflow-hidden bg-[url('/img.svg')] bg-cover bg-center">
        <div className="absolute inset-0 bg-[#FCFCFC]/95"></div>
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_120%,rgba(88,28,135,0.1),transparent_70%)]"></div>
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24 md:py-32 text-center">
          <div className="max-w-4xl mx-auto">
            <h1 className="text-5xl md:text-6xl lg:text-7xl heading text-accent-gray mb-8 leading-[1.1] tracking-tight">
              Making Homeownership<br />
              <span className="bg-gradient-to-r from-[#581C87] to-[#1E3A8A] bg-clip-text text-transparent">
                Possible
              </span>
            </h1>
            <p className="text-xl md:text-2xl body text-gray-600 mb-12 max-w-3xl mx-auto leading-relaxed">
              No down payment? No problem. Build your dream home through smart savings, AI-powered property analysis, and investor partnerships.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-6">
              {isLoggedIn ? (
                <>
                  <Button 
                    size="lg" 
                    onClick={handleDashboardClick}
                    className="bg-[#581C87] hover:bg-[#581C87]/90 text-white px-8 py-6 text-lg font-medium shadow-lg hover:shadow-xl transition-all"
                  >
                    <ArrowRight className="w-6 h-6 mr-3" /> Go to Dashboard
                  </Button>
                </>
              ) : (
                <>
                  <Link to="/sign-up">
                    <Button size="lg" className="bg-[#581C87] hover:bg-[#581C87]/90 text-white px-8 py-6 text-lg font-medium shadow-lg hover:shadow-xl transition-all">
                      <Home className="w-6 h-6 mr-3" /> Start Your Journey
                    </Button>
                  </Link>
                  <Link to="/login">
                    <Button size="lg" variant="outline" className="border-2 border-[#111827]/20 text-[#111827] px-8 py-6 text-lg font-medium hover:bg-[#111827] hover:text-white transition-all">
                      <Users className="w-6 h-6 mr-3" /> Log In
                    </Button>
                  </Link>
                </>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* Journey Section */}
      <section id="journey" className="bg-gray-50/50 py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <Badge className="bg-[#581C87] text-white px-4 py-2 text-sm font-medium mb-6">The Homebuyer's Journey</Badge>
            <h2 className="text-4xl md:text-5xl heading text-[#111827] mb-6">
              Meet Priya
            </h2>
            <p className="text-xl body text-gray-600 max-w-3xl mx-auto leading-relaxed">
              A 28-year-old software developer who wants to buy a home but lacks the down payment
            </p>
          </div>

          <Card className="rounded-3xl border-0 shadow-lg hover:shadow-xl transition-all duration-300 mb-12">
            <CardContent className="p-10 md:p-12">
              <div className="flex items-start gap-8 mb-8">
                <div className="w-20 h-20 bg-gradient-to-br from-[#581C87] to-[#1E3A8A] rounded-2xl flex items-center justify-center flex-shrink-0 shadow-lg">
                  <Brain className="w-10 h-10 text-white" />
                </div>
                <div className="flex-1">
                  <h3 className="text-3xl md:text-4xl heading text-[#111827] mb-4">TrueHome AI: The Advisor</h3>
                  <p className="text-lg body text-gray-700 mb-6 leading-relaxed">
                    Priya found a ₹90 Lakh 2BHK in Kharghar. Using TrueHome AI, she analyzes the property's legal status, market potential, and investment viability. The AI confirms it's a legally safe and high-potential property, giving her the confidence to proceed.
                  </p>
                  <div className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-2xl p-6 inline-block border border-purple-100">
                    <p className="text-base heading text-[#111827] mb-2">✓ Legal verification complete</p>
                    <p className="text-sm body text-gray-600">Property approved for investment</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          <div className="text-center mb-12">
            <div className="inline-flex flex-col sm:flex-row items-center gap-3 bg-white rounded-full px-6 py-4 shadow-lg border border-gray-100">
              <span className="text-base heading text-[#111827] tracking-wide">CHOOSE YOUR ROLE</span>
              
            </div>
          </div>

          <div className="grid md:grid-cols-2 gap-8">
            <Card className="rounded-3xl border-2 border-[#581C87] shadow-lg hover:shadow-xl transition-all duration-300 hover:border-[#581C87]/80">
              <CardContent className="p-8">
                <div className="flex items-center gap-4 mb-6">
                  <div className="w-16 h-16 bg-[#581C87] rounded-2xl flex items-center justify-center shadow-lg">
                    <Home className="w-8 h-8 text-white" />
                  </div>
                  <div>
                    <span className="text-sm heading text-[#581C87] uppercase tracking-wide">Role A</span>
                    <h4 className="text-2xl heading text-[#111827]">Homebuyer</h4>
                  </div>
                </div>
                <p className="text-lg heading text-[#111827] mb-3">Homebuyer Pathway</p>
                <p className="text-gray-600 body mb-6 leading-relaxed">
                  "Step into your future home now with a capital partner. We connect you to investors who can cover your down payment, so you can move in as a co-owner and start building equity immediately."
                </p>
                <div className="bg-gradient-to-r from-purple-50 to-purple-100 rounded-2xl p-5 mb-6">
                  <p className="text-sm heading text-[#111827] mb-2">Best For:</p>
                  <p className="text-sm body text-gray-700">Early-stage homebuyers who want to move in quickly with investor-backed down payment support and clear equity growth.</p>
                </div>
                <Link to="/homebuyer-dashboard">
                  <Button variant="link" className="text-base text-[#581C87] p-0 h-auto font-medium hover:text-[#581C87]/80">
                    Know more <ArrowRight className="w-5 h-5 ml-2" />
                  </Button>
                </Link>
              </CardContent>
            </Card>

            <Card className="rounded-3xl border-2 border-[#1E3A8A] shadow-lg hover:shadow-xl transition-all duration-300 hover:border-[#1E3A8A]/80">
              <CardContent className="p-8">
                <div className="flex items-center gap-4 mb-6">
                  <div className="w-16 h-16 bg-[#1E3A8A] rounded-2xl flex items-center justify-center shadow-lg">
                    <PiggyBank className="w-8 h-8 text-white" />
                  </div>
                  <div>
                    <span className="text-sm heading text-[#1E3A8A] uppercase tracking-wide">Role B</span>
                    <h4 className="text-2xl heading text-[#111827]">Investor</h4>
                  </div>
                </div>
                <p className="text-lg heading text-[#111827] mb-3">Investor Pathway</p>
                <p className="text-gray-600 body mb-6 leading-relaxed">
                  "Deploy capital into proven homebuyer opportunities and earn predictable real estate cashflows. Funds are matched with creditworthy buyers, and we manage the savings and payment collection on your behalf for low-touch portfolio growth."
                </p>
                <div className="bg-gradient-to-r from-blue-50 to-blue-100 rounded-2xl p-5 mb-6">
                  <p className="text-sm heading text-[#111827] mb-2">Best For:</p>
                  <p className="text-sm body text-gray-700">Investors seeking risk-adjusted real-estate yield through managed co-investments with transparent performance tracking.</p>
                </div>
                <Button variant="link" className="text-base text-[#1E3A8A] p-0 h-auto font-medium hover:text-[#1E3A8A]/80">
                  Know more <ArrowRight className="w-5 h-5 ml-2" />
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Investor Section */}
      <section id="invest" className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <Badge className="bg-[#1E3A8A] text-white px-4 py-2 text-sm font-medium mb-6">The Investor's Journey</Badge>
            <h2 className="text-4xl md:text-5xl heading text-[#111827] mb-6">
              Meet Mr. Sharma
            </h2>
            <p className="text-xl body text-gray-600 max-w-3xl mx-auto leading-relaxed">
              A 50-year-old doctor from Vashi with ₹20 Lakhs to invest. He wants real estate returns without landlord hassles.
            </p>
          </div>

          <Card className="rounded-3xl border-0 shadow-xl">
            <CardContent className="bg-gradient-to-br from-gray-50 via-blue-50/50 to-purple-50/30 rounded-3xl p-10 md:p-12">
              <div className="flex items-start gap-8 mb-10">
                <div className="w-20 h-20 bg-gradient-to-br from-orange-500 to-[#1E3A8A] rounded-2xl flex items-center justify-center flex-shrink-0 shadow-lg">
                  <Building2 className="w-10 h-10 text-white" />
                </div>
                <div className="flex-1">
                  <h3 className="text-3xl md:text-4xl heading text-[#111827] mb-4">Co-Vest: The Passive Investor Marketplace</h3>
                  <p className="text-lg body text-gray-700 leading-relaxed">
                    Mr. Sharma discovers our investor marketplace with two types of pre-vetted opportunities:
                  </p>
                </div>
              </div>

              <div className="grid md:grid-cols-2 gap-8">
                <Card className="rounded-2xl border-0 shadow-lg bg-white/80 backdrop-blur-sm">
                  <CardContent className="p-8">
                    <div className="flex items-center gap-3 mb-4">
                      <div className="w-12 h-12 bg-orange-500 rounded-xl flex items-center justify-center shadow-md">
                        <Building2 className="w-6 h-6 text-white" />
                      </div>
                      <h4 className="text-xl heading text-[#111827]">Pure Investment Co-Ownership</h4>
                    </div>
                    <p className="text-base body text-gray-600 mb-6 leading-relaxed">
                      Invest in a ₹1 Crore commercial shop in Seawoods. Join three other investors, contribute ₹20 Lakhs for a 20% stake. Receive 20% of monthly rent, hassle-free.
                    </p>
                    <div className="bg-gradient-to-r from-orange-50 to-orange-100 rounded-xl p-4">
                      <p className="text-sm heading text-[#111827]">₹20L Investment = 20% Ownership + Monthly Rent</p>
                    </div>
                  </CardContent>
                </Card>

                <Card className="rounded-2xl border-0 shadow-lg bg-white/80 backdrop-blur-sm">
                  <CardContent className="p-8">
                    <div className="flex items-center gap-3 mb-4">
                      <div className="w-12 h-12 bg-[#581C87] rounded-xl flex items-center justify-center shadow-md">
                        <Users className="w-6 h-6 text-white" />
                      </div>
                      <h4 className="text-xl heading text-[#111827]">Fund a Homebuyer (Step-Up)</h4>
                    </div>
                    <p className="text-base body text-gray-600 mb-6 leading-relaxed">
                      Fund Priya's ₹18 Lakh down payment. Get steady monthly income from her "rent-share" plus property appreciation benefits, with a motivated homeowner maintaining your investment.
                    </p>
                    <div className="bg-gradient-to-r from-purple-50 to-purple-100 rounded-xl p-4">
                      <p className="text-sm heading text-[#111827]">₹18L Investment + Monthly Returns + Appreciation</p>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </CardContent>
          </Card>
        </div>
      </section>

      <section id="stories" className="bg-gray-50 py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl md:text-4xl heading text-accent-gray text-center mb-4">
            Real Stories, Real Dreams
          </h2>
          <p className="text-gray-600 body text-center mb-12 max-w-2xl mx-auto">
            Lives transformed through our ecosystem
          </p>

          <div className="grid md:grid-cols-2 gap-8">
            <Card className="rounded-2xl">
              <CardContent className="p-8">
                <div className="flex items-start gap-4 mb-4">
                  <div className="w-12 h-12 bg-gradient-to-br from-accent-purple to-accent-blue rounded-full"></div>
                  <div>
                    <h3 className="heading text-accent-gray">Priya Patel</h3>
                    <p className="text-sm body text-gray-600">Software Developer, Mumbai</p>
                  </div>
                </div>
                <p className="text-gray-700 body mb-4">
                  "I always thought I'd need years to save for a down payment. With TrueHome's Step-Up model, I moved into my 2BHK in Kharghar within 3 months. TrueHome AI helped me choose the right property, and now I'm building equity every month."
                </p>
                <div className="flex gap-4 mb-4">
                  <div className="bg-purple-50 rounded-lg p-3 flex-1">
                    <p className="text-lg heading text-accent-gray">₹18L</p>
                    <p className="text-xs body text-gray-600">Down payment funded</p>
                  </div>
                  <div className="bg-blue-50 rounded-lg p-3 flex-1">
                    <p className="text-lg heading text-accent-gray">3 months</p>
                    <p className="text-xs body text-gray-600">From start to keys</p>
                  </div>
                </div>
                <Button variant="link" className="text-sm text-accent-purple p-0 h-auto">
                  <Home className="w-4 h-4 mr-1" /> Read full story
                </Button>
              </CardContent>
            </Card>

            <Card className="rounded-2xl">
              <CardContent className="p-8">
                <div className="flex items-start gap-4 mb-4">
                  <div className="w-12 h-12 bg-gradient-to-br from-orange-500 to-accent-blue rounded-full"></div>
                  <div>
                    <h3 className="heading text-accent-gray">Dr. Rajesh Sharma</h3>
                    <p className="text-sm body text-gray-600">Cardiologist, Vashi</p>
                  </div>
                </div>
                <p className="text-gray-700 body mb-4">
                  "As a busy professional, I wanted real estate returns without the management headaches. Through Co-Vest, I invested ₹20 Lakhs in a commercial property and funded two homebuyers. Completely passive income every month."
                </p>
                <div className="flex gap-4 mb-4">
                  <div className="bg-orange-50 rounded-lg p-3 flex-1">
                    <p className="text-lg heading text-accent-gray">8.5%</p>
                    <p className="text-xs body text-gray-600">Annual returns</p>
                  </div>
                  <div className="bg-purple-50 rounded-lg p-3 flex-1">
                    <p className="text-lg heading text-accent-gray">Zero</p>
                    <p className="text-xs body text-gray-600">Management effort</p>
                  </div>
                </div>
                <Button variant="link" className="text-sm text-accent-blue p-0 h-auto">
                  <DollarSign className="w-4 h-4 mr-1" /> See investment options
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      <section id="ecosystem" className="py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl md:text-4xl heading text-accent-gray text-center mb-4">
            The SarvAwas AI Ecosystem
          </h2>
          <p className="text-gray-600 body text-center mb-12">
            Four features creating a self-sustaining loop
          </p>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card className="bg-gray-50 rounded-2xl hover:shadow-lg transition-shadow">
              <CardContent className="p-8">
                <div className="w-12 h-12 bg-white rounded-xl flex items-center justify-center mb-4">
                  <Brain className="w-6 h-6 " />
                </div>
                <h3 className="heading text-accent-gray mb-3">TrueHome AI</h3>
                <p className="text-sm body text-gray-600 mb-4">
                  The foundation of trust that analyzes and approves all properties for the ecosystem with AI-powered price and risk insights.
                </p>
                <div className="flex flex-col gap-2">
                  <Link to="/rera-verification">
                    <Button variant="link" className="text-sm text-accent-blue p-0 h-auto">RERA Risk Analysis</Button>
                  </Link>
                  <Link to="/house-prediction">
                    <Button variant="link" className="text-sm text-accent-blue p-0 h-auto">Price Prediction</Button>
                  </Link>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-gray-50 rounded-2xl hover:shadow-lg transition-shadow">
              <CardContent className="p-8">
                <div className="w-12 h-12 bg-accent-blue rounded-xl flex items-center justify-center mb-4">
                  <PiggyBank className="w-6 h-6 text-white" />
                </div>
                <h3 className="heading text-accent-gray mb-3">Pehla Kadam</h3>
                <p className="text-sm body text-gray-600 mb-4">
                  Discover government housing schemes and subsidies tailored for first-time buyers.
                </p>
                <Button variant="link" className="text-sm text-accent-blue p-0 h-auto">Explore schemes</Button>
              </CardContent>
            </Card>

            <Card className="bg-gray-50 rounded-2xl hover:shadow-lg transition-shadow">
              <CardContent className="p-8">
                <div className="w-12 h-12 bg-accent-purple rounded-xl flex items-center justify-center mb-4">
                  <Home className="w-6 h-6 text-white" />
                </div>
                <h3 className="heading text-accent-gray mb-3">Step-Up</h3>
                <p className="text-sm body text-gray-600 mb-4">
                  Connects ready homebuyers with capital from investors. Move into your home today, build equity immediately.
                </p>
                <Button variant="link" className="text-sm text-accent-blue p-0 h-auto">Get pre-qualified</Button>
              </CardContent>
            </Card>

            <Card className="bg-gray-50 rounded-2xl hover:shadow-lg transition-shadow">
              <CardContent className="p-8">
                <div className="w-12 h-12 bg-orange-500 rounded-xl flex items-center justify-center mb-4">
                  <Building2 className="w-6 h-6 text-white" />
                </div>
                <h3 className="heading text-accent-gray mb-3">Co-Vest</h3>
                <p className="text-sm body text-gray-600 mb-4">
                  Platform for passive investors. Your funds power both pure investment deals and the Step-Up model.
                </p>
                <Button variant="link" className="text-sm text-accent-blue p-0 h-auto">View opportunities</Button>
              </CardContent>
            </Card>
          </div>

          <div className="mt-12 gradient-accent rounded-2xl p-8 text-white text-center">
            <h3 className="text-2xl heading mb-3">A Self-Sustaining Loop</h3>
            <p className="text-white/90 max-w-2xl mx-auto">
              TrueHome AI validates properties → Pehla Kadam prepares buyers → Step-Up connects buyers with investors → Co-Vest provides the capital. Each feature strengthens the others.
            </p>
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="py-20 bg-gray-50/50">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl heading text-[#111827] mb-6">Frequently Asked Questions</h2>
            <p className="text-xl body text-gray-600 max-w-2xl mx-auto">Quick answers about SarvAwas AI programs and investing</p>
          </div>
          <div className="bg-white rounded-3xl shadow-lg p-8">
            <Accordion type="single" collapsible className="w-full">
              <AccordionItem value="item-1" className="border-b border-gray-100">
                <AccordionTrigger className="text-left text-lg heading text-[#111827] hover:text-[#581C87] py-6">
                  How does Step-Up work for buyers?
                </AccordionTrigger>
                <AccordionContent className="text-base body text-gray-600 pb-6 leading-relaxed">
                  We partner you with an investor who covers the down payment. You move in now and build equity from day one, with a clear path to full ownership over time through monthly payments.
                </AccordionContent>
              </AccordionItem>
              <AccordionItem value="item-2" className="border-b border-gray-100">
                <AccordionTrigger className="text-left text-lg heading text-[#111827] hover:text-[#581C87] py-6">
                  What is Pehla Kadam?
                </AccordionTrigger>
                <AccordionContent className="text-base body text-gray-600 pb-6 leading-relaxed">
                  A disciplined savings program that automates rent+extra into verified investments to grow your down payment over time. Think of it as a smart way to build your future home fund.
                </AccordionContent>
              </AccordionItem>
              <AccordionItem value="item-3" className="border-b border-gray-100">
                <AccordionTrigger className="text-left text-lg heading text-[#111827] hover:text-[#581C87] py-6">
                  Are investor returns guaranteed?
                </AccordionTrigger>
                <AccordionContent className="text-base body text-gray-600 pb-6 leading-relaxed">
                  Returns vary by opportunity type and duration. We provide transparent projections and risks for each deal on the platform, with historical performance data to guide your decisions.
                </AccordionContent>
              </AccordionItem>
              <AccordionItem value="item-4">
                <AccordionTrigger className="text-left text-lg heading text-[#111827] hover:text-[#581C87] py-6">
                  How does TrueHome AI verify properties?
                </AccordionTrigger>
                <AccordionContent className="text-base body text-gray-600 pb-6 leading-relaxed">
                  TrueHome AI conducts comprehensive legal, financial, and market analysis using AI and verified databases to ensure every property meets our safety and investment standards.
                </AccordionContent>
              </AccordionItem>
            </Accordion>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="relative bg-gradient-to-br from-[#111827] via-[#1E3A8A] to-[#581C87] text-white py-24 overflow-hidden">
        <div className="absolute inset-0 opacity-20">
          <div className="absolute inset-0" style={{
            backgroundImage: 'radial-gradient(circle at 2px 2px, rgba(255,255,255,0.15) 1px, transparent 0)',
            backgroundSize: '40px 40px'
          }}></div>
        </div>
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-4xl md:text-5xl heading mb-6">
            Ready to Transform Your Future?
          </h2>
          <p className="text-xl text-white/90 mb-12 max-w-3xl mx-auto leading-relaxed">
            Whether you're a homebuyer or investor, SarvAwas AI has a path for you
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-6">
            <Link to="/sign-up">
              <Button size="lg" className="bg-white text-[#111827] px-10 py-6 text-lg font-medium hover:bg-gray-100 shadow-lg hover:shadow-xl transition-all">
                <Home className="w-6 h-6 mr-3" /> Start Your Journey
              </Button>
            </Link>
            <Button size="lg" variant="outline" className="border-2 border-white text-black px-10 py-6 text-lg font-medium hover:bg-white hover:text-[#111827] transition-all">
              <Users className="w-6 h-6 mr-3" /> Explore Investments
            </Button>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
}

export default Landing;