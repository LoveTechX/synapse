'use client';

import React, { useState, useEffect } from 'react';
import ActivityList from '@/components/ActivityList';
import { apiClient } from '@/lib/api';
import { Filter, Download } from 'lucide-react';

interface ActivityItem {
    timestamp: string;
    file_name: string;
    file: string;
    category: string;
    action: string;
    subject: string;
    confidence: number;
    reason: string;
}

export default function ActivityPage() {
    const [activity, setActivity] = useState<ActivityItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState('all');

    useEffect(() => {
        const loadActivity = async () => {
            try {
                const data = await apiClient.getActivity(100);
                setActivity(data.activity || []);
            } catch (error) {
                console.error('Failed to load activity:', error);
            } finally {
                setLoading(false);
            }
        };

        loadActivity();
    }, []);

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="flex flex-col items-center gap-4">
                    <div className="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
                    <div className="text-slate-400">Loading activity...</div>
                </div>
            </div>
        );
    }

    const filteredActivity = filter === 'all'
        ? activity
        : activity.filter(item => item.category === filter);

    const categories = ['all', ...new Set(activity.map(item => item.category))];

    return (
        <div className="space-y-6 pb-8">
            {/* Filter Bar */}
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 bg-slate-900 border border-slate-800 rounded-xl p-4">
                <div className="flex items-center gap-3 flex-wrap">
                    <Filter className="w-5 h-5 text-slate-400" />
                    <span className="text-sm text-slate-400">Filter by:</span>
                    {categories.map(cat => (
                        <button
                            key={cat}
                            onClick={() => setFilter(cat)}
                            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${filter === cat
                                    ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-lg'
                                    : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                                }`}
                        >
                            {cat.charAt(0).toUpperCase() + cat.slice(1)}
                        </button>
                    ))}
                </div>
                <button className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition-colors text-sm">
                    <Download className="w-4 h-4" />
                    Export
                </button>
            </div>

            {/* Activity List */}
            <ActivityList activities={filteredActivity} maxItems={100} />

            {/* Stats Summary */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
                    <p className="text-slate-400 text-sm mb-2">Total Actions</p>
                    <p className="text-3xl font-bold text-white">{activity.length}</p>
                </div>
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
                    <p className="text-slate-400 text-sm mb-2">Categories</p>
                    <p className="text-3xl font-bold text-white">{categories.length - 1}</p>
                </div>
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
                    <p className="text-slate-400 text-sm mb-2">Avg Confidence</p>
                    <p className="text-3xl font-bold text-white">
                        {activity.length > 0
                            ? (activity.reduce((sum, item) => sum + (item.confidence || 0), 0) / activity.length).toFixed(1)
                            : 0}%
                    </p>
                </div>
            </div>
        </div>
    );
}
