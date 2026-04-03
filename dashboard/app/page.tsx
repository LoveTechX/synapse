'use client';

import React, { useState, useEffect } from 'react';
import StatCard from '@/components/StatCard';
import ActivityList from '@/components/ActivityList';
import { FileText, Zap, TrendingUp, Clock, BarChart3, PieChart, Activity as ActivityIcon } from 'lucide-react';
import { apiClient } from '@/lib/api';

interface StatsData {
    total_files: number;
    today_files: number;
}

interface ActivityItem {
    timestamp: string;
    file_name: string;
    action: string;
    category: string;
}

export default function Home() {
    const [stats, setStats] = useState<StatsData | null>(null);
    const [activity, setActivity] = useState<ActivityItem[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const loadData = async () => {
            try {
                const statsData = await apiClient.getStats();
                setStats(statsData);

                const activityData = await apiClient.getActivity(10);
                setActivity(activityData.activity || []);
            } catch (error) {
                console.error('Failed to load data:', error);
            } finally {
                setLoading(false);
            }
        };

        loadData();
    }, []);

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="flex flex-col items-center gap-4">
                    <div className="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
                    <div className="text-slate-400">Loading dashboard...</div>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-8 pb-8">
            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <StatCard
                    title="Total Files"
                    value={stats?.total_files || 0}
                    icon={<FileText className="w-8 h-8" />}
                    gradient="from-blue-500/10 to-cyan-500/10"
                    trend={{ value: 12, isPositive: true }}
                />
                <StatCard
                    title="Organized Today"
                    value={stats?.today_files || 0}
                    icon={<TrendingUp className="w-8 h-8" />}
                    gradient="from-green-500/10 to-emerald-500/10"
                    trend={{ value: 8, isPositive: true }}
                />
                <StatCard
                    title="System Status"
                    value="Operational"
                    icon={<Zap className="w-8 h-8" />}
                    gradient="from-yellow-500/10 to-orange-500/10"
                />
                <StatCard
                    title="Last Activity"
                    value={activity.length > 0 ? 'Just now' : 'Never'}
                    icon={<Clock className="w-8 h-8" />}
                    gradient="from-purple-500/10 to-pink-500/10"
                />
            </div>

            {/* Charts Section */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Confidence Distribution Chart Placeholder */}
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-lg">
                    <div className="flex items-center justify-between mb-6">
                        <div>
                            <h3 className="text-lg font-semibold text-white">Confidence Distribution</h3>
                            <p className="text-sm text-slate-400 mt-1">AI classification confidence levels</p>
                        </div>
                        <BarChart3 className="w-6 h-6 text-indigo-400" />
                    </div>
                    <div className="h-64 flex items-center justify-center bg-slate-800/50 rounded-lg border border-slate-700">
                        <div className="text-center">
                            <BarChart3 className="w-12 h-12 text-slate-600 mx-auto mb-3" />
                            <p className="text-slate-500 text-sm">Chart placeholder</p>
                            <p className="text-slate-600 text-xs mt-1">Coming soon</p>
                        </div>
                    </div>
                </div>

                {/* Category Breakdown Chart Placeholder */}
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-lg">
                    <div className="flex items-center justify-between mb-6">
                        <div>
                            <h3 className="text-lg font-semibold text-white">Category Breakdown</h3>
                            <p className="text-sm text-slate-400 mt-1">File distribution by category</p>
                        </div>
                        <PieChart className="w-6 h-6 text-purple-400" />
                    </div>
                    <div className="h-64 flex items-center justify-center bg-slate-800/50 rounded-lg border border-slate-700">
                        <div className="text-center">
                            <PieChart className="w-12 h-12 text-slate-600 mx-auto mb-3" />
                            <p className="text-slate-500 text-sm">Chart placeholder</p>
                            <p className="text-slate-600 text-xs mt-1">Coming soon</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Activity Timeline Chart Placeholder */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-lg">
                <div className="flex items-center justify-between mb-6">
                    <div>
                        <h3 className="text-lg font-semibold text-white">Activity Timeline</h3>
                        <p className="text-sm text-slate-400 mt-1">File organization over time</p>
                    </div>
                    <ActivityIcon className="w-6 h-6 text-green-400" />
                </div>
                <div className="h-64 flex items-center justify-center bg-slate-800/50 rounded-lg border border-slate-700">
                    <div className="text-center">
                        <ActivityIcon className="w-12 h-12 text-slate-600 mx-auto mb-3" />
                        <p className="text-slate-500 text-sm">Chart placeholder</p>
                        <p className="text-slate-600 text-xs mt-1">Coming soon</p>
                    </div>
                </div>
            </div>

            {/* Recent Activity with new component */}
            <ActivityList activities={activity} maxItems={10} />
        </div>
    );
}
