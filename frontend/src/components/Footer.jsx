import { Home } from 'lucide-react';
import { Separator } from "@/components/ui/separator.jsx";

function Footer() {
  return (
    <footer className="bg-[#111827] text-white py-16">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-12">
          <div className="col-span-2 md:col-span-1">
            <div className="heading text-2xl mb-6 flex items-center gap-3">
              <div className="w-8 h-8 bg-gradient-to-br from-[#581C87] to-[#1E3A8A] rounded-lg flex items-center justify-center">
                <Home className="w-5 h-5 text-white" />
              </div>
              SarvAwas AI
            </div>
            <p className="text-base text-gray-300 leading-relaxed">
              Making homeownership accessible for everyone through AI and community investment
            </p>
          </div>
          <div>
            <h4 className="heading text-lg mb-6">For Buyers</h4>
            <ul className="space-y-3 text-gray-300">
              <li><a href="#" className="hover:text-white transition-colors">TrueHome AI</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Pehla Kadam</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Step-Up Program</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Success Stories</a></li>
            </ul>
          </div>
          <div>
            <h4 className="heading text-lg mb-6">For Investors</h4>
            <ul className="space-y-3 text-gray-300">
              <li><a href="#" className="hover:text-white transition-colors">Co-Vest Platform</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Investment Options</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Returns Calculator</a></li>
              <li><a href="#" className="hover:text-white transition-colors">FAQ</a></li>
            </ul>
          </div>
          <div>
            <h4 className="heading text-lg mb-6">Company</h4>
            <ul className="space-y-3 text-gray-300">
              <li><a href="#" className="hover:text-white transition-colors">About Us</a></li>
              <li><a href="#" className="hover:text-white transition-colors">How It Works</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Careers</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Contact</a></li>
            </ul>
          </div>
        </div>
        <Separator className="bg-gray-700 mb-8" />
        <div className="flex flex-col md:flex-row justify-between items-center text-gray-300">
          <p className="text-base">© 2024 SarvAwas AI. All rights reserved.</p>
          <div className="flex gap-6 mt-4 md:mt-0">
            <a href="#" className="hover:text-white transition-colors">Privacy</a>
            <a href="#" className="hover:text-white transition-colors">Terms</a>
            <a href="#" className="hover:text-white transition-colors">Security</a>
          </div>
        </div>
      </div>
    </footer>
  );
}

export default Footer;