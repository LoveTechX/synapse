'use client';

import React from 'react';
import { FileText, Folder, Clock } from 'lucide-react';

interface ActivityItem {
    timestamp: string;
    file_name: string;
    action: string;
    category: string;
}

interface ActivityListProps {
    activities: ActivityItem[];
    maxItems?: number;
}

export default function ActivityList({ activities, maxItems = 10 }: ActivityListProps) {
    const displayActivities = activities.slice(0, maxItems);

    const getCategoryColor = (category: string) => {
        const colors: { [key: string]: string } = {
            'code': 'bg-blue-500/10 text-blue-400 border-blue-500/20',
            'docs': 'bg-green-500/10 text-green-400 border-green-500/20',
            'media': 'bg-purple-500/10 text-purple-400 border-purple-500/20',
            'data': 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
            'config': 'bg-orange-500/10 text-orange-400 border-orange-500/20',
            'archive': 'bg-gray-500/10 text-gray-400 border-gray-500/20',
        };
        return colors[category.toLowerCase()] || 'bg-slate-500/10 text-slate-400 border-slate-500/20';
    };

    const formatTimestamp = (timestamp: string) => {
        try {
            const date = new Date(timestamp);
            const now = new Date();
            const diffMs = now.getTime() - date.getTime();
            const diffMins = Math.floor(diffMs / 60000);

            if (diffMins < 1) return 'Just now';
            if (diffMins < 60) return `${diffMins}m ago`;
            if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
            return date.toLocaleDateString();
        } catch {
            return timestamp;
        }
    };

    if (displayActivities.length === 0) {
        return (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-12 text-center">
                <Folder className="w-12 h-12 text-slate-600 mx-auto mb-4" />
                <p className="text-slate-400">No recent activity</p>
            </div>
        );
    }

    return (
        <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-lg">
            <div className="px-6 py-4 border-b border-slate-800 bg-slate-800/50">
                <h2 className="text-lg font-semibold text-white">Recent Activity</h2>
            </div>
            <div className="divide-y divide-slate-800">
                {displayActivities.map((activity, index) => (
                    <div
                        key={index}
                        className="px-6 py-4 hover:bg-slate-800/50 transition-colors duration-200"
                    >
                        <div className="flex items-center justify-between gap-4">
                            <div className="flex items-center gap-3 flex-1 min-w-0">
                                <div className="flex-shrink-0">
                                    <FileText className="w-5 h-5 text-slate-400" />
                                </div>
                                <div className="flex-1 min-w-0">
                                    <p className="text-sm font-medium text-white truncate">
                                        {activity.file_name}
                                    </p>
                                    <p className="text-xs text-slate-400 mt-1">
                                        {activity.action}
                                    </p>
                                </div>
                            </div>
                            <div className="flex items-center gap-3 flex-shrink-0">
                                <span
                                    className={`inline-flex px-3 py-1 rounded-full text-xs font-medium border ${getCategoryColor(
                                        activity.category
                                    )}`}
                                >
                                    {activity.category}
                                </span>
                                <div className="flex items-center gap-1 text-xs text-slate-500 min-w-[80px] justify-end">
                                    <Clock className="w-3 h-3" />
                                    <span>{formatTimestamp(activity.timestamp)}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
