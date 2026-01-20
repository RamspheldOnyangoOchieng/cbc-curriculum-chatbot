"use client";

import React from "react";
import { CheckCircle, Shield, Award, Users, BookOpen, BrainCircuit, GraduationCap, Scale, Globe } from "lucide-react";

export default function AboutPage() {
    return (
        <div className="min-h-screen bg-[#0a0a0a] text-zinc-100 font-sans">
            {/* About Hero */}
            <section className="py-24 bg-zinc-900/20 border-b border-white/5 relative overflow-hidden">
                <div className="absolute top-0 left-0 w-full h-full bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] opacity-5" />
                <div className="max-w-4xl mx-auto px-6 text-center relative z-10">
                    <h1 className="text-4xl md:text-6xl font-extrabold mb-6">Redefining <span className="text-red-500">Education</span> in Kenya</h1>
                    <p className="text-xl text-zinc-400 leading-relaxed max-w-2xl mx-auto">
                        The CBC Expert System is an AI-driven guide designed to navigate the shift from 8-4-4 to the 2-6-6-3 Competency-Based Curriculum.
                    </p>
                </div>
            </section>

            {/* The 2-6-6-3 Structure */}
            <section className="py-20 border-b border-white/5">
                <div className="max-w-7xl mx-auto px-6">
                    <div className="text-center mb-16">
                        <h2 className="text-3xl font-bold mb-4">The 2-6-6-3 Structure Explained</h2>
                        <p className="text-zinc-500">A breakdown of the new educational cycle.</p>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                        {[
                            { level: "Pre-Primary", years: "2 Years", grades: "PP1 - PP2", focus: "Social Skills & Basic Literacy" },
                            { level: "Primary School", years: "6 Years", grades: "Grade 1 - Grade 6", focus: "Foundational Literacy & Numeracy" },
                            { level: "Junior Secondary", years: "3 Years", grades: "Grade 7 - Grade 9", focus: "Broad-based Curriculum & Exploration" },
                            { level: "Senior Secondary", years: "3 Years", grades: "Grade 10 - Grade 12", focus: "Pathway Specialization (STEM, Arts, Social Sciences)" },
                        ].map((item, idx) => (
                            <div key={idx} className="p-6 bg-zinc-900/50 border border-zinc-800 rounded-2xl hover:border-red-500/30 transition-colors">
                                <div className="text-red-500 font-bold text-lg mb-2">{item.years}</div>
                                <h3 className="text-xl font-bold text-white mb-1">{item.level}</h3>
                                <p className="text-zinc-500 text-sm mb-4 font-mono">{item.grades}</p>
                                <p className="text-zinc-400 text-sm leading-relaxed">{item.focus}</p>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* Core Competencies */}
            <section className="py-20 bg-zinc-900/30">
                <div className="max-w-7xl mx-auto px-6">
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
                        <div>
                            <h2 className="text-3xl font-bold mb-6">The 7 Core Competencies</h2>
                            <p className="text-zinc-400 mb-8 leading-relaxed">
                                Unlike the previous exam-oriented system, CBC focuses on what a learner can <strong>DO</strong>, not just what they know. We nurture holistic citizens equipped for the 21st century.
                            </p>
                            <div className="space-y-4">
                                {[
                                    "Communication and Collaboration",
                                    "Critical Thinking and Problem Solving",
                                    "Imagination and Creativity",
                                    "Citizenship",
                                    "Learning to Learn",
                                    "Self-Efficacy",
                                    "Digital Literacy"
                                ].map((comp, idx) => (
                                    <div key={idx} className="flex items-center gap-3">
                                        <CheckCircle className="w-5 h-5 text-green-500 shrink-0" />
                                        <span className="text-zinc-300 font-medium">{comp}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="p-6 bg-black border border-zinc-800 rounded-2xl">
                                <BrainCircuit className="w-8 h-8 text-amber-500 mb-4" />
                                <h4 className="font-bold text-white">Critical Thinking</h4>
                                <p className="text-xs text-zinc-500 mt-2">Solving real-world problems through logic.</p>
                            </div>
                            <div className="p-6 bg-black border border-zinc-800 rounded-2xl translate-y-8">
                                <Users className="w-8 h-8 text-blue-500 mb-4" />
                                <h4 className="font-bold text-white">Collaboration</h4>
                                <p className="text-xs text-zinc-500 mt-2">Working effectively in diverse teams.</p>
                            </div>
                            <div className="p-6 bg-black border border-zinc-800 rounded-2xl">
                                <Globe className="w-8 h-8 text-green-500 mb-4" />
                                <h4 className="font-bold text-white">Citizenship</h4>
                                <p className="text-xs text-zinc-500 mt-2">Understanding rights and responsibilities.</p>
                            </div>
                            <div className="p-6 bg-black border border-zinc-800 rounded-2xl translate-y-8">
                                <GraduationCap className="w-8 h-8 text-purple-500 mb-4" />
                                <h4 className="font-bold text-white">Learning to Learn</h4>
                                <p className="text-xs text-zinc-500 mt-2">Adaptability in a changing world.</p>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* Assessment & Grading */}
            <section className="py-20 border-t border-white/5">
                <div className="max-w-5xl mx-auto px-6 text-center">
                    <div className="inline-block p-3 bg-red-900/10 rounded-xl mb-6">
                        <Scale className="w-8 h-8 text-red-500" />
                    </div>
                    <h2 className="text-3xl font-bold mb-6">A New Way to Assess</h2>
                    <p className="text-zinc-400 leading-relaxed mb-10">
                        Moving away from the high-stakes KCPE, CBC introduces <strong>Competency Based Assessment (CBA)</strong>. This includes 60% continuous assessment and 40% summative assessment.
                    </p>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8 text-left">
                        <div className="p-8 bg-zinc-900/50 rounded-3xl border border-white/5">
                            <h3 className="text-xl font-bold text-white mb-4">KPSEA (Grade 6)</h3>
                            <p className="text-zinc-400 text-sm">
                                Kenya Primary School Education Assessment. It is used to monitor learner progress and not for placement. All learners transition to Junior Secondary.
                            </p>
                        </div>
                        <div className="p-8 bg-zinc-900/50 rounded-3xl border border-white/5">
                            <h3 className="text-xl font-bold text-white mb-4">KJSEA (Grade 9)</h3>
                            <p className="text-zinc-400 text-sm">
                                Kenya Junior School Education Assessment. Used to place learners into Senior School pathways (STEM, Arts, Social Sciences) based on performance and interest.
                            </p>
                        </div>
                    </div>
                </div>
            </section>

            {/* Parental Empowerment */}
            <section className="py-24 bg-gradient-to-b from-zinc-900 to-black">
                <div className="max-w-7xl mx-auto px-6">
                    <div className="flex flex-col md:flex-row items-center gap-12">
                        <div className="flex-1 space-y-8">
                            <h2 className="text-3xl md:text-4xl font-bold">Empowering Parents</h2>
                            <p className="text-lg text-zinc-400">
                                The "Parental Empowerment and Engagement" guidelines emphasize that parents are the first educators. Your role has evolved from passive observer to active partner.
                            </p>

                            <div className="space-y-6">
                                <div className="flex gap-4">
                                    <div className="w-12 h-12 rounded-full bg-zinc-800 flex items-center justify-center font-bold text-white">1</div>
                                    <div>
                                        <h4 className="text-lg font-bold text-white">Shared Responsibility</h4>
                                        <p className="text-zinc-500 text-sm mt-1">Partnership between parents, teachers, and the community is vital for success.</p>
                                    </div>
                                </div>
                                <div className="flex gap-4">
                                    <div className="w-12 h-12 rounded-full bg-zinc-800 flex items-center justify-center font-bold text-white">2</div>
                                    <div>
                                        <h4 className="text-lg font-bold text-white">Value Instillation</h4>
                                        <p className="text-zinc-500 text-sm mt-1">Parents are primarily responsible for nurturing moral values and character.</p>
                                    </div>
                                </div>
                                <div className="flex gap-4">
                                    <div className="w-12 h-12 rounded-full bg-zinc-800 flex items-center justify-center font-bold text-white">3</div>
                                    <div>
                                        <h4 className="text-lg font-bold text-white">Talent Identification</h4>
                                        <p className="text-zinc-500 text-sm mt-1">Early identification of a child's potential helps in selecting the right Senior School pathway.</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div className="flex-1 relative">
                            <div className="absolute inset-0 bg-red-600 blur-[100px] opacity-10" />
                            <div className="relative bg-zinc-950 border border-zinc-800 p-8 rounded-3xl">
                                <h3 className="text-xl font-bold mb-4">Did You Know?</h3>
                                <p className="text-zinc-400 italic mb-6">
                                    "The lack of properly trained teachers stands out as a primary obstacle... The Central Academics Team (CAT) model ensures delivery of high-quality education."
                                </p>
                                <p className="text-sm text-zinc-600 uppercase tracking-widest font-bold">From the "Strengthening Teachers Training" Report</p>
                            </div>
                        </div>
                    </div>
                </div>
            </section>
        </div>
    );
}
