'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { BarChart3, Activity, Settings, Home, Brain } from 'lucide-react';

export default function Sidebar() {
    const pathname = usePathname();

    const isActive = (path: string) => pathname === path || pathname?.startsWith(path + '/');

    const links = [
        { href: '/', label: 'Overview', icon: Home },
        { href: '/activity', label: 'Activity', icon: Activity },
        { href: '/analytics', label: 'Analytics', icon: BarChart3 },
        { href: '/settings', label: 'Settings', icon: Settings },
    ];

    return (
        <aside className="w-64 bg-slate-900 border-r border-slate-800 h-screen fixed left-0 top-0 overflow-y-auto z-50">
            {/* Logo */}
            <div className="p-6 border-b border-slate-800">
                <div className="flex items-center gap-3 mb-2">
                    <div className="relative">
                        <Brain className="w-8 h-8 text-indigo-500" />
                        <div className="absolute inset-0 blur-md bg-indigo-500 opacity-30 -z-10"></div>
                    </div>
                    <div>
                        <h1 className="text-xl font-bold text-white tracking-tight">Synapse</h1>
                        <p className="text-xs text-slate-400">AI Workspace</p>
                    </div>
                </div>
            </div>

            {/* Navigation */}
            <nav className="p-4 space-y-1">
                {links.map((link) => {
                    const Icon = link.icon;
                    const active = isActive(link.href);

                    return (
                        <Link
                            key={link.href}
                            href={link.href}
                            className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 ${active
                                    ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-lg shadow-indigo-500/30'
                                    : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                                }`}
                        >
                            <Icon className={`w-5 h-5 ${active ? 'text-white' : ''}`} />
                            <span className="font-medium">{link.label}</span>
                        </Link>
                    );
                })}
            </nav>

            {/* Footer */}
            <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-slate-800 bg-slate-900">
                <div className="flex items-center justify-center gap-2 py-2">
                    <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
                    <p className="text-xs text-slate-400">
                        v1.0.0 • Online
                    </p>
                </div>
            </div>
        </aside>
    );
}
