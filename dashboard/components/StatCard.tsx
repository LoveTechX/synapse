'use client';

import React from 'react';

interface StatCardProps {
    title: string;
    value: string | number;
    icon?: React.ReactNode;
    trend?: {
        value: number;
        isPositive: boolean;
    };
    gradient?: string;
}

export default function StatCard({
    title,
    value,
    icon,
    trend,
    gradient = 'from-indigo-500/10 to-purple-500/10',
}: StatCardProps) {
    return (
        <div className="group relative bg-slate-900 border border-slate-800 rounded-xl p-6 hover:scale-105 hover:border-indigo-500/50 transition-all duration-300 shadow-lg overflow-hidden">
            {/* Gradient Background */}
            <div className={`absolute inset-0 bg-gradient-to-br ${gradient} opacity-0 group-hover:opacity-100 transition-opacity duration-300`}></div>

            {/* Content */}
            <div className="relative z-10 flex items-start justify-between">
                <div className="flex-1">
                    <p className="text-slate-400 text-sm font-medium mb-2">{title}</p>
                    <p className="text-3xl font-bold text-white mb-2">{value}</p>
                    {trend && (
                        <div
                            className={`inline-flex items-center gap-1 text-xs font-medium px-2 py-1 rounded-full ${trend.isPositive
                                    ? 'text-green-400 bg-green-500/10'
                                    : 'text-red-400 bg-red-500/10'
                                }`}
                        >
                            <span>{trend.isPositive ? '↑' : '↓'}</span>
                            <span>{Math.abs(trend.value)}%</span>
                        </div>
                    )}
                </div>
                {icon && (
                    <div className="text-slate-600 group-hover:text-indigo-400 transition-colors duration-300 ml-4">
                        {icon}
                    </div>
                )}
            </div>

            {/* Bottom glow effect */}
            <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-indigo-500 to-purple-500 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
        </div>
    );
}
