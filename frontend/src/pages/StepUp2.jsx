import { useState } from "react";
import axios from "axios";
import Navbar from "@/components/Navbar.jsx";
import Footer from "@/components/Footer.jsx";

import {
  Home,
  TrendingUp,
  DollarSign,
  ArrowUpRight,
  Brain
} from "lucide-react";

export default function StepUp2() {

  const [form, setForm] = useState({
    area: 900,
    bedroom_num: 2,
    bathroom_num: 2,
    balcony_num: 1,
    locality: "",
    city: "Mumbai",
    property_type: "Apartment",
    furnished: "Unfurnished",
    age: "",
    total_floors: "",
    years: 5,
    investor_stake: 0.1,
    monthly_rent: 30000,
  });

  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleChange = (e) =>
    setForm({ ...form, [e.target.name]: e.target.value });

  const runSimulation = async () => {
    try {
      setLoading(true);

      const res = await axios.post(
        "http://127.0.0.1:8000/stepup/simulate",
        {
          ...form,
          area: Number(form.area),
          bedroom_num: Number(form.bedroom_num),
          bathroom_num: Number(form.bathroom_num),
          balcony_num: Number(form.balcony_num),
          age: Number(form.age),
          total_floors: Number(form.total_floors),
          years: Number(form.years),
          investor_stake: Number(form.investor_stake),
          monthly_rent: Number(form.monthly_rent),
        }
      );

      setResult(res.data);


    } catch (err) {
      alert("Backend error — check locality spelling.");
    } finally {
      setLoading(false);
    }
  };

  const input =
    "w-full px-4 py-3 border border-gray-300 rounded-xl bg-white focus:outline-none focus:ring-2 focus:ring-purple-500";

  const helper = "text-xs text-slate-400 mt-1"; // ✅ FIXED

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">

      <Navbar />

      <section className="flex-1 px-6 py-12">

        <div className="max-w-6xl mx-auto">

          <h1 className="text-4xl font-bold text-slate-900 mb-2">
            StepUp
          </h1>

          <p className="text-slate-600 mb-10">
            Simulate how partnering with an investor today impacts your property ownership and financial outcome.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-10">

            {/* LEFT PANEL */}

            <div className="bg-white p-8 rounded-2xl shadow-xl">

              <h2 className="text-xl font-semibold mb-6">
                Property Details
              </h2>

              <div className="grid grid-cols-2 gap-4">

                <div>
                  <label className="text-sm font-medium mb-1 block">Area (sqft)</label>
                  <input className={input} name="area" value={form.area} onChange={handleChange} />
                  <p className={helper}>Total usable area</p>
                </div>

                <div>
                  <label className="text-sm font-medium mb-1 block">Bedrooms</label>
                  <select className={input} name="bedroom_num" value={form.bedroom_num} onChange={handleChange}>
                    {[1, 2, 3, 4, 5].map(v => <option key={v}>{v} BHK</option>)}
                  </select>
                  <p className={helper}>Number of bedrooms</p>
                </div>

                <div>
                  <label className="text-sm font-medium mb-1 block">Bathrooms</label>
                  <select className={input} name="bathroom_num" value={form.bathroom_num} onChange={handleChange}>
                    {[1, 2, 3, 4].map(v => <option key={v}>{v}</option>)}
                  </select>
                </div>

                <div>
                  <label className="text-sm font-medium mb-1 block">Balconies</label>
                  <select className={input} name="balcony_num" value={form.balcony_num} onChange={handleChange}>
                    {[0, 1, 2, 3].map(v => <option key={v}>{v}</option>)}
                  </select>
                </div>

                <div className="col-span-2">
                  <label className="text-sm font-medium mb-1 block">Locality</label>
                  <input
                    className={input}
                    name="locality"
                    value={form.locality}
                    onChange={handleChange}
                    placeholder="e.g. Worli, Bandra"
                  />
                  <p className={helper}>Used to estimate property value</p>
                </div>

                <div>
                  <label className="text-sm font-medium mb-1 block">Property Type</label>
                  <select className={input} name="property_type" value={form.property_type} onChange={handleChange}>
                    <option>Apartment</option>
                    <option>Villa</option>
                    <option>Independent House</option>
                  </select>
                </div>

                <div>
                  <label className="text-sm font-medium mb-1 block">Furnishing</label>
                  <select className={input} name="furnished" value={form.furnished} onChange={handleChange}>
                    <option>Unfurnished</option>
                    <option>Semi-Furnished</option>
                    <option>Fully Furnished</option>
                  </select>
                </div>

                <div>
                  <label className="text-sm font-medium mb-1 block">Property Age</label>
                  <input className={input} name="age" value={form.age} onChange={handleChange} />
                </div>

                <div>
                  <label className="text-sm font-medium mb-1 block">Total Floors</label>
                  <input className={input} name="total_floors" value={form.total_floors} onChange={handleChange} />
                </div>

              </div>

              <hr className="my-6" />

              <h2 className="text-xl font-semibold mb-4">
                Investment Setup
              </h2>

              <label className="text-sm font-medium">
                Holding Period: {form.years} years
              </label>
              <p className={helper}>How long you keep the property</p>

              <input
                type="range"
                min="1"
                max="20"
                value={form.years}
                onChange={(e) => setForm({ ...form, years: e.target.value })}
                className="w-full mb-6"
              />

              <label className="text-sm font-medium">
                Investor Ownership: {(form.investor_stake * 100).toFixed(0)}%
              </label>
              <p className={helper}>Higher % = lower upfront cost for you</p>

              <input
                type="range"
                min="5"
                max="40"
                value={form.investor_stake * 100}
                onChange={(e) => setForm({ ...form, investor_stake: e.target.value / 100 })}
                className="w-full mb-6"
              />

              <div>
                <label className="text-sm font-medium mb-1 block">
                  Expected Monthly Rent (₹)
                </label>
                <input className={input} name="monthly_rent" value={form.monthly_rent} onChange={handleChange} />
              </div>

              <button
                onClick={runSimulation}
                disabled={!form.locality || loading}
                className="w-full mt-6 bg-gradient-to-r from-purple-600 to-indigo-600 text-white py-3 rounded-xl text-lg font-semibold hover:opacity-90 disabled:opacity-50"
              >
                {loading ? "Running Simulation..." : "Calculate Investment Outcome"}
              </button>

            </div>

            {/* RIGHT PANEL */}

            {!result ? (

              <div className="bg-gradient-to-br from-slate-900 to-indigo-950 text-white p-8 rounded-2xl shadow-xl flex flex-col justify-center">

                <h3 className="text-xl font-semibold mb-4">
                  How StepUp works
                </h3>

                <div className="space-y-4 text-sm text-slate-300">
                  <p>1. You and an investor jointly buy the property</p>
                  <p>2. Investor reduces your upfront cost</p>
                  <p>3. Property value grows over time</p>
                  <p>4. You buy back their share later</p>
                </div>

              </div>

            ) : (

              <div className="bg-gradient-to-br from-slate-900 to-indigo-950 text-white p-8 rounded-2xl shadow-xl">

                <div className="bg-gradient-to-r from-purple-600 to-indigo-600 rounded-xl p-6 text-center mb-6">
                  <p className="text-sm opacity-80">Projected Investor Return</p>
                  <p className="text-4xl font-bold">{result.finance.roi}%</p>
                  <p className="text-xs opacity-80">
                    Including rent + appreciation over {form.years} years
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-4 mb-6">

                  <div className="bg-slate-800 rounded-lg p-4 flex gap-3 items-center">
                    <Home size={18} className="text-purple-400" />
                    <div>
                      <p className="text-xs text-slate-400">Current Price</p>
                      <p className="text-lg font-semibold">₹ {result.current_price.toLocaleString("en-IN")}</p>
                    </div>
                  </div>

                  <div className="bg-slate-800 rounded-lg p-4 flex gap-3 items-center">
                    <TrendingUp size={18} className="text-purple-400" />
                    <div>
                      <p className="text-xs text-slate-400">Future Price</p>
                      <p className="text-lg font-semibold">₹ {result.future_price.toLocaleString("en-IN")}</p>
                    </div>
                  </div>

                  <div className="bg-slate-800 rounded-lg p-4 flex gap-3 items-center">
                    <DollarSign size={18} className="text-purple-400" />
                    <div>
                      <p className="text-xs text-slate-400">Investor Investment</p>
                      <p className="text-lg font-semibold">₹ {result.finance.invested.toLocaleString("en-IN")}</p>
                    </div>
                  </div>

                  <div className="bg-slate-800 rounded-lg p-4 flex gap-3 items-center">
                    <ArrowUpRight size={18} className="text-purple-400" />
                    <div>
                      <p className="text-xs text-slate-400">Buyback Price</p>
                      <p className="text-lg font-semibold">₹ {result.finance.buyback_price.toLocaleString("en-IN")}</p>
                    </div>
                  </div>

                </div>

                <div className="bg-gradient-to-r from-purple-100 to-indigo-100 text-slate-800 rounded-xl p-5 mt-6">
                  <p className="text-sm font-semibold text-purple-700 mb-3">
                    HOW TO INTERPRET THIS RESULT
                  </p>

                  <ul className="text-sm space-y-2 list-disc pl-5">

                    <li>
                      Property value may grow from{" "}
                      <span className="font-semibold">
                        ₹ {result.current_price.toLocaleString("en-IN")}
                      </span>{" "}
                      to{" "}
                      <span className="font-semibold">
                        ₹ {result.future_price.toLocaleString("en-IN")}
                      </span>{" "}
                      over{" "}
                      <span className="font-semibold">{form.years} years</span>.
                    </li>

                    <li>
                      Investor contributes{" "}
                      <span className="font-semibold">
                        ₹ {result.finance.invested.toLocaleString("en-IN")}
                      </span>{" "}
                      for a{" "}
                      <span className="font-semibold">
                        {(form.investor_stake * 100).toFixed(0)}%
                      </span>{" "}
                      stake, reducing your upfront cost.
                    </li>

                    <li>
                      Estimated total rental income:{" "}
                      <span className="font-semibold">
                        ₹ {result.finance.rent_income.toLocaleString("en-IN")}
                      </span>.
                    </li>

                    <li>
                      To regain full ownership, you may pay around{" "}
                      <span className="font-semibold">
                        ₹ {result.finance.buyback_price.toLocaleString("en-IN")}
                      </span>.
                    </li>

                    <li>
                      Investor ROI is approximately{" "}
                      <span className="font-semibold">
                        {result.finance.roi}%
                      </span>, combining appreciation + rent.
                    </li>

                  </ul>

                  <p className="text-xs text-slate-500 mt-4">
                      *These insights are designed to help you explore possibilities and make informed decisions.
                    </p>
                </div>

              </div>

            )}

          </div>

        </div>

      </section>

      <Footer />

    </div>
  );
}
