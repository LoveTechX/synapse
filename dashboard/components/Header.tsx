'use client';

import React from 'react';
import { usePathname } from 'next/navigation';
import { Sparkles } from 'lucide-react';

export default function Header() {
    const pathname = usePathname();

    const getTitle = () => {
        switch (pathname) {
            case '/':
                return 'Dashboard Overview';
            case '/activity':
                return 'Recent Activity';
            case '/analytics':
                return 'Analytics & Charts';
            case '/settings':
                return 'Configuration';
            default:
                return 'Synapse Dashboard';
        }
    };

    const getSubtitle = () => {
        switch (pathname) {
            case '/':
                return 'Real-time workspace intelligence and insights';
            case '/activity':
                return 'Track file organization and AI decisions';
            case '/analytics':
                return 'Visualize patterns and performance metrics';
            case '/settings':
                return 'Configure system preferences';
            default:
                return 'AI Workspace Intelligence';
        }
    };

    return (
        <header className="bg-slate-900/50 border-b border-slate-800 backdrop-blur-sm sticky top-0 z-40">
            <div className="flex items-center justify-between h-20 px-8">
                <div>
                    <h2 className="text-2xl font-bold text-white mb-1">{getTitle()}</h2>
                    <p className="text-sm text-slate-400">{getSubtitle()}</p>
                </div>
                <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-slate-800 border border-slate-700">
                        <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
                        <span className="text-sm text-slate-300 font-medium">Live</span>
                    </div>
                    <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-gradient-to-r from-indigo-600/10 to-purple-600/10 border border-indigo-500/20">
                        <Sparkles className="w-4 h-4 text-indigo-400" />
                        <span className="text-sm text-indigo-300 font-medium">AI Active</span>
                    </div>
                </div>
            </div>
        </header>
    );
}
