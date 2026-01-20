"use client";

import React from "react";
import Link from "next/link";
import { ArrowRight, BookOpen, Users, Compass, Star } from "lucide-react";
import { motion } from "framer-motion";

export default function Home() {
  return (
    <div className="flex flex-col min-h-screen text-zinc-100">

      {/* Hero Section */}
      <section className="relative h-[80vh] flex items-center justify-center overflow-hidden">
        {/* Abstract Background */}
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-red-900/20 via-black to-black" />
        <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/carbon-fibre.png')] opacity-20" />

        <div className="relative z-10 max-w-5xl mx-auto px-6 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            <div className="inline-block px-4 py-1.5 mb-6 rounded-full bg-red-900/30 border border-red-500/30 text-red-400 text-sm font-semibold tracking-wider uppercase">
              The Future of Education
            </div>
            <h1 className="text-5xl md:text-7xl font-extrabold mb-6 tracking-tight leading-tight">
              Navigating <span className="bg-gradient-to-r from-red-500 to-amber-500 bg-clip-text text-transparent">CBC & Grade 9</span> Transitions
            </h1>
            <p className="text-xl text-zinc-400 mb-10 max-w-2xl mx-auto leading-relaxed">
              Your inclusive A.I. guide for Senior School pathways, career choices, and curriculum updates.
              Trusted by parents, students, and educators.
            </p>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link href="/pathways" className="group px-8 py-4 bg-white text-black font-bold rounded-full hover:bg-zinc-200 transition-all flex items-center gap-2">
                Explore Pathways <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </Link>
              <Link href="/about" className="px-8 py-4 bg-zinc-900 border border-zinc-800 text-white font-bold rounded-full hover:bg-zinc-800 transition-all">
                Learn More
              </Link>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-20 border-y border-white/5 bg-zinc-900/30 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 md:grid-cols-3 gap-10 text-center">
          <div>
            <h3 className="text-4xl font-bold text-white mb-2">1.13M</h3>
            <p className="text-zinc-500 font-medium uppercase tracking-wide">Learners Placed</p>
          </div>
          <div>
            <h3 className="text-4xl font-bold text-white mb-2">3</h3>
            <p className="text-zinc-500 font-medium uppercase tracking-wide">Main Pathways</p>
          </div>
          <div>
            <h3 className="text-4xl font-bold text-white mb-2">100%</h3>
            <p className="text-zinc-500 font-medium uppercase tracking-wide">Transition Rate</p>
          </div>
        </div>
      </section>

      {/* Feature Grid */}
      <section className="py-32 bg-black">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-20">
            <h2 className="text-3xl font-bold mb-4">Everything you need to know</h2>
            <p className="text-zinc-500">Comprehensive tools for the Competency Based Curriculum.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {/* Card 1 */}
            <div className="p-8 rounded-3xl bg-zinc-900/50 border border-white/5 hover:border-red-500/30 transition-colors group">
              <div className="w-12 h-12 bg-red-900/20 rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <Compass className="w-6 h-6 text-red-500" />
              </div>
              <h3 className="text-xl font-bold mb-3">Career Pathways</h3>
              <p className="text-zinc-400 leading-relaxed">Detailed breakdown of STEM, Social Sciences, and Arts & Sports Science pathways to help you choose right.</p>
            </div>

            {/* Card 2 */}
            <div className="p-8 rounded-3xl bg-zinc-900/50 border border-white/5 hover:border-amber-500/30 transition-colors group">
              <div className="w-12 h-12 bg-amber-900/20 rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <BookOpen className="w-6 h-6 text-amber-500" />
              </div>
              <h3 className="text-xl font-bold mb-3">Curriculum Resources</h3>
              <p className="text-zinc-400 leading-relaxed">Access approved course books, syllabus updates, and assessment guidelines directly from KICD.</p>
            </div>

            {/* Card 3 */}
            <div className="p-8 rounded-3xl bg-zinc-900/50 border border-white/5 hover:border-green-500/30 transition-colors group">
              <div className="w-12 h-12 bg-green-900/20 rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <Users className="w-6 h-6 text-green-500" />
              </div>
              <h3 className="text-xl font-bold mb-3">Expert Guidance</h3>
              <p className="text-zinc-400 leading-relaxed">Our AI Assistant provides localized, accurate advice for parents and teachers 24/7.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 border-t border-white/5 bg-zinc-950">
        <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row justify-between items-center gap-6">
          <p className="text-zinc-600 text-sm">© {new Date().getFullYear()} CBC Expert System. All rights reserved.</p>
          <div className="flex gap-6 text-zinc-500 text-sm font-medium">
            <Link href="#" className="hover:text-white transition-colors">Privacy Policy</Link>
            <Link href="#" className="hover:text-white transition-colors">Terms of Service</Link>
            <Link href="#" className="hover:text-white transition-colors">Contact</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
