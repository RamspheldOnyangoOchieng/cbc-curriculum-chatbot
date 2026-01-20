"use client";

import React from "react";
import { Hammer, Music, Calculator, Microscope, Gavel, Briefcase, Globe } from "lucide-react";

export default function PathwaysPage() {
    const pathways = [
        {
            title: "STEM Pathway",
            description: "Science, Technology, Engineering, and Mathematics",
            color: "from-blue-600 to-cyan-400",
            icon: <Microscope className="w-8 h-8 text-cyan-400" />,
            sub_tracks: [
                { name: "Pure Sciences", careers: ["Medicine", "Engineering", "Pharmacy", "Actuarial Science"] },
                { name: "Applied Sciences", careers: ["Agriculture", "Computer Science", "Nursing", "Health Records"] },
                { name: "Technical & Engineering", careers: ["Architecture", "Mechatronics", "Automotive Engineering", "Electrical Engineering"] },
                { name: "Career & Tech Studies (CTS)", careers: ["Hospitality Management", "Fashion & Design", "Information Technology", "Construction"] }
            ]
        },
        {
            title: "Social Sciences",
            description: "Humanities Board, Business, and Languages",
            color: "from-amber-600 to-orange-400",
            icon: <Globe className="w-8 h-8 text-amber-400" />,
            sub_tracks: [
                { name: "Humanities", careers: ["Law", "Psychology", "Theology", "Public Administration"] },
                { name: "Business Studies", careers: ["Accounting", "Economics", "Human Resources", "Entrepreneurship"] },
                { name: "Languages", careers: ["Journalism", "International Relations", "Translation", "Education"] },
            ]
        },
        {
            title: "Arts & Sports Science",
            description: "Creative Arts and Physical Performance",
            color: "from-purple-600 to-pink-400",
            icon: <Music className="w-8 h-8 text-pink-400" />,
            sub_tracks: [
                { name: "Sports Science", careers: ["Sports Management", "Physiotherapy", "Coaching", "Refereeing"] },
                { name: "Performing Arts", careers: ["Music Production", "Film & Theatre", "Dance / Choreography", "Content Creation"] },
                { name: "Visual Arts", careers: ["Graphic Design", "Fine Art", "Multimedia", "Curatorial Studies"] },
            ]
        }
    ];

    return (
        <div className="min-h-screen bg-[#0a0a0a] text-zinc-100 p-8 pb-32">
            <div className="max-w-6xl mx-auto">
                <header className="mb-16 text-center">
                    <div className="inline-block px-4 py-1.5 mb-6 rounded-full bg-zinc-800 border border-zinc-700 text-zinc-300 text-sm font-semibold tracking-wider uppercase">
                        Senior School
                    </div>
                    <h1 className="text-4xl md:text-6xl font-extrabold mb-6">Explore <span className="text-red-500">Pathways</span></h1>
                    <p className="text-xl text-zinc-400 max-w-2xl mx-auto">
                        Grade 10 marks the beginning of specialization. Discover the three major pathways tailored to every learner's potential.
                    </p>
                </header>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                    {pathways.map((path, idx) => (
                        <div key={idx} className="group relative rounded-3xl bg-zinc-900 border border-zinc-800 overflow-hidden hover:border-zinc-600 transition-all duration-300 hover:shadow-2xl">
                            <div className={`absolute top-0 left-0 w-full h-1 bg-gradient-to-r ${path.color}`} />

                            <div className="p-8">
                                <div className="flex items-center gap-4 mb-6">
                                    <div className="p-3 bg-zinc-950 rounded-xl border border-zinc-800 group-hover:scale-110 transition-transform duration-300">
                                        {path.icon}
                                    </div>
                                    <h2 className="text-2xl font-bold">{path.title}</h2>
                                </div>
                                <p className="text-zinc-400 mb-8 h-12">{path.description}</p>

                                <div className="space-y-6">
                                    {path.sub_tracks.map((track, tIdx) => (
                                        <div key={tIdx} className="bg-zinc-950/50 p-4 rounded-xl border border-white/5">
                                            <h4 className="font-semibold text-white mb-2">{track.name}</h4>
                                            <div className="flex flex-wrap gap-2">
                                                {track.careers.slice(0, 3).map((job, jIdx) => (
                                                    <span key={jIdx} className="text-xs px-2 py-1 bg-zinc-800 rounded-md text-zinc-400 border border-zinc-700">
                                                        {job}
                                                    </span>
                                                ))}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
