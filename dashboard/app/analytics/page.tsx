'use client';

import React, { useState, useEffect } from 'react';
import {
    BarChart,
    Bar,
    PieChart,
    Pie,
    Cell,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
} from 'recharts';
import { apiClient } from '@/lib/api';
import { TrendingUp, PieChart as PieChartIcon, BarChart3 } from 'lucide-react';

interface CategoryData {
    category: string;
    count: number;
}

interface ConfidenceData {
    bucket: string;
    count: number;
}

const COLORS = ['#6366f1', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#3b82f6'];

export default function AnalyticsPage() {
    const [categories, setCategories] = useState<CategoryData[]>([]);
    const [confidence, setConfidence] = useState<ConfidenceData[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const loadData = async () => {
            try {
                const catData = await apiClient.getCategories();
                setCategories(catData.categories || []);

                const confData = await apiClient.getConfidence();
                setConfidence(confData.distribution || []);
            } catch (error) {
                console.error('Failed to load analytics:', error);
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
                    <div className="text-slate-400">Loading analytics...</div>
                </div>
            </div>
        );
    }

    const totalFiles = categories.reduce((sum, cat) => sum + cat.count, 0);

    return (
        <div className="space-y-8 pb-8">
            {/* Stats Summary */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-gradient-to-br from-indigo-500/10 to-purple-500/10 border border-indigo-500/20 rounded-xl p-6">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-slate-400 text-sm mb-2">Total Files</p>
                            <p className="text-3xl font-bold text-white">{totalFiles}</p>
                        </div>
                        <BarChart3 className="w-10 h-10 text-indigo-400" />
                    </div>
                </div>
                <div className="bg-gradient-to-br from-purple-500/10 to-pink-500/10 border border-purple-500/20 rounded-xl p-6">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-slate-400 text-sm mb-2">Categories</p>
                            <p className="text-3xl font-bold text-white">{categories.length}</p>
                        </div>
                        <PieChartIcon className="w-10 h-10 text-purple-400" />
                    </div>
                </div>
                <div className="bg-gradient-to-br from-green-500/10 to-emerald-500/10 border border-green-500/20 rounded-xl p-6">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-slate-400 text-sm mb-2">Avg Confidence</p>
                            <p className="text-3xl font-bold text-white">
                                {confidence.length > 0
                                    ? ((confidence.reduce((sum, c) => sum + c.count, 0) / confidence.length) * 100).toFixed(0)
                                    : 0}%
                            </p>
                        </div>
                        <TrendingUp className="w-10 h-10 text-green-400" />
                    </div>
                </div>
            </div>

            {/* Charts Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Category Distribution */}
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-lg">
                    <h2 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
                        <BarChart3 className="w-5 h-5 text-indigo-400" />
                        Category Distribution
                    </h2>
                    <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={categories}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                            <XAxis
                                dataKey="category"
                                stroke="#94a3b8"
                                tick={{ fill: '#94a3b8' }}
                            />
                            <YAxis
                                stroke="#94a3b8"
                                tick={{ fill: '#94a3b8' }}
                            />
                            <Tooltip
                                contentStyle={{
                                    backgroundColor: '#1e293b',
                                    border: '1px solid #475569',
                                    borderRadius: '8px',
                                    color: '#e2e8f0',
                                }}
                            />
                            <Bar dataKey="count" fill="#6366f1" radius={[8, 8, 0, 0]} />
                        </BarChart>
                    </ResponsiveContainer>
                </div>

                {/* Confidence Distribution */}
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-lg">
                    <h2 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
                        <PieChartIcon className="w-5 h-5 text-purple-400" />
                        Confidence Distribution
                    </h2>
                    <ResponsiveContainer width="100%" height={300}>
                        <PieChart>
                            <Pie
                                data={confidence}
                                dataKey="count"
                                nameKey="bucket"
                                cx="50%"
                                cy="50%"
                                outerRadius={100}
                                label
                            >
                                {confidence.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                ))}
                            </Pie>
                            <Tooltip
                                contentStyle={{
                                    backgroundColor: '#1e293b',
                                    border: '1px solid #475569',
                                    borderRadius: '8px',
                                    color: '#e2e8f0',
                                }}
                            />
                            <Legend
                                wrapperStyle={{ color: '#94a3b8' }}
                            />
                        </PieChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* Category Details Table */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-lg">
                <div className="px-6 py-4 border-b border-slate-800 bg-slate-800/50">
                    <h2 className="text-lg font-semibold text-white">Category Details</h2>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead>
                            <tr className="border-b border-slate-800 bg-slate-800/30">
                                <th className="px-6 py-4 text-left text-sm font-semibold text-slate-300">
                                    Category
                                </th>
                                <th className="px-6 py-4 text-left text-sm font-semibold text-slate-300">
                                    File Count
                                </th>
                                <th className="px-6 py-4 text-left text-sm font-semibold text-slate-300">
                                    Percentage
                                </th>
                                <th className="px-6 py-4 text-left text-sm font-semibold text-slate-300">
                                    Distribution
                                </th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800">
                            {categories.map((cat, idx) => {
                                const percentage = totalFiles > 0 ? (cat.count / totalFiles) * 100 : 0;
                                return (
                                    <tr key={idx} className="hover:bg-slate-800/50 transition-colors">
                                        <td className="px-6 py-4 text-sm text-white font-medium capitalize">
                                            {cat.category}
                                        </td>
                                        <td className="px-6 py-4 text-sm text-slate-300">
                                            {cat.count}
                                        </td>
                                        <td className="px-6 py-4 text-sm text-slate-300">
                                            {percentage.toFixed(1)}%
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="w-full bg-slate-700 rounded-full h-2">
                                                <div
                                                    className="bg-gradient-to-r from-indigo-500 to-purple-500 h-2 rounded-full transition-all"
                                                    style={{ width: `${percentage}%` }}
                                                ></div>
                                            </div>
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
