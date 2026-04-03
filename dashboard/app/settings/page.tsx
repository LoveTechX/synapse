'use client';

import React, { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api';
import { Settings as SettingsIcon, Save, Check } from 'lucide-react';

interface Settings {
    confidence_thresholds: {
        high: number;
        medium: number;
        low: number;
    };
    preview_mode: boolean;
    auto_mode: boolean;
    monitoring_enabled: boolean;
}

export default function SettingsPage() {
    const [settings, setSettings] = useState<Settings | null>(null);
    const [loading, setLoading] = useState(true);
    const [saved, setSaved] = useState(false);

    useEffect(() => {
        const loadSettings = async () => {
            try {
                const data = await apiClient.getSettings();
                setSettings(data);
            } catch (error) {
                console.error('Failed to load settings:', error);
            } finally {
                setLoading(false);
            }
        };

        loadSettings();
    }, []);

    const handleSave = async () => {
        if (!settings) return;

        try {
            await apiClient.getSettings();
            setSaved(true);
            setTimeout(() => setSaved(false), 3000);
        } catch (error) {
            console.error('Failed to save settings:', error);
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="flex flex-col items-center gap-4">
                    <div className="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
                    <div className="text-slate-400">Loading settings...</div>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-8 pb-8">
            {/* Status Message */}
            {saved && (
                <div className="bg-gradient-to-r from-green-500/10 to-emerald-500/10 border border-green-500/30 text-green-400 px-6 py-4 rounded-xl flex items-center gap-3 animate-in fade-in slide-in-from-top">
                    <Check className="w-5 h-5" />
                    <span className="font-medium">Settings saved successfully</span>
                </div>
            )}

            {/* System Modes */}
            {settings && (
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-lg">
                    <h2 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
                        <SettingsIcon className="w-5 h-5 text-indigo-400" />
                        System Configuration
                    </h2>

                    <div className="space-y-4">
                        <div className="flex items-center justify-between p-4 bg-slate-800/50 rounded-lg border border-slate-700 hover:border-indigo-500/50 transition-colors">
                            <div>
                                <p className="text-sm font-medium text-white mb-1">Preview Mode</p>
                                <p className="text-xs text-slate-400">Review changes before applying</p>
                            </div>
                            <label className="relative inline-flex items-center cursor-pointer">
                                <input
                                    type="checkbox"
                                    checked={settings.preview_mode}
                                    onChange={(e) =>
                                        setSettings({ ...settings, preview_mode: e.target.checked })
                                    }
                                    className="sr-only peer"
                                />
                                <div className="w-11 h-6 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-gradient-to-r peer-checked:from-indigo-600 peer-checked:to-purple-600"></div>
                            </label>
                        </div>

                        <div className="flex items-center justify-between p-4 bg-slate-800/50 rounded-lg border border-slate-700 hover:border-indigo-500/50 transition-colors">
                            <div>
                                <p className="text-sm font-medium text-white mb-1">Auto Mode</p>
                                <p className="text-xs text-slate-400">Automatically organize files</p>
                            </div>
                            <label className="relative inline-flex items-center cursor-pointer">
                                <input
                                    type="checkbox"
                                    checked={settings.auto_mode}
                                    onChange={(e) =>
                                        setSettings({ ...settings, auto_mode: e.target.checked })
                                    }
                                    className="sr-only peer"
                                />
                                <div className="w-11 h-6 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-gradient-to-r peer-checked:from-indigo-600 peer-checked:to-purple-600"></div>
                            </label>
                        </div>

                        <div className="flex items-center justify-between p-4 bg-slate-800/50 rounded-lg border border-slate-700 hover:border-indigo-500/50 transition-colors">
                            <div>
                                <p className="text-sm font-medium text-white mb-1">Real-time Monitoring</p>
                                <p className="text-xs text-slate-400">Watch for new files continuously</p>
                            </div>
                            <label className="relative inline-flex items-center cursor-pointer">
                                <input
                                    type="checkbox"
                                    checked={settings.monitoring_enabled}
                                    onChange={(e) =>
                                        setSettings({ ...settings, monitoring_enabled: e.target.checked })
                                    }
                                    className="sr-only peer"
                                />
                                <div className="w-11 h-6 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-gradient-to-r peer-checked:from-indigo-600 peer-checked:to-purple-600"></div>
                            </label>
                        </div>
                    </div>
                </div>
            )}

            {/* Confidence Thresholds */}
            {settings && (
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-lg">
                    <h2 className="text-lg font-semibold text-white mb-6">Confidence Thresholds</h2>

                    <div className="space-y-6">
                        <div>
                            <div className="flex items-center justify-between mb-3">
                                <label className="text-sm font-medium text-slate-300">High Confidence</label>
                                <span className="text-sm font-bold text-indigo-400">
                                    {(settings.confidence_thresholds.high * 100).toFixed(0)}%
                                </span>
                            </div>
                            <input
                                type="range"
                                min="0"
                                max="100"
                                value={settings.confidence_thresholds.high * 100}
                                onChange={(e) =>
                                    setSettings({
                                        ...settings,
                                        confidence_thresholds: {
                                            ...settings.confidence_thresholds,
                                            high: parseFloat(e.target.value) / 100,
                                        },
                                    })
                                }
                                className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-indigo-500"
                            />
                        </div>

                        <div>
                            <div className="flex items-center justify-between mb-3">
                                <label className="text-sm font-medium text-slate-300">Medium Confidence</label>
                                <span className="text-sm font-bold text-purple-400">
                                    {(settings.confidence_thresholds.medium * 100).toFixed(0)}%
                                </span>
                            </div>
                            <input
                                type="range"
                                min="0"
                                max="100"
                                value={settings.confidence_thresholds.medium * 100}
                                onChange={(e) =>
                                    setSettings({
                                        ...settings,
                                        confidence_thresholds: {
                                            ...settings.confidence_thresholds,
                                            medium: parseFloat(e.target.value) / 100,
                                        },
                                    })
                                }
                                className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-purple-500"
                            />
                        </div>

                        <div>
                            <div className="flex items-center justify-between mb-3">
                                <label className="text-sm font-medium text-slate-300">Low Confidence</label>
                                <span className="text-sm font-bold text-pink-400">
                                    {(settings.confidence_thresholds.low * 100).toFixed(0)}%
                                </span>
                            </div>
                            <input
                                type="range"
                                min="0"
                                max="100"
                                value={settings.confidence_thresholds.low * 100}
                                onChange={(e) =>
                                    setSettings({
                                        ...settings,
                                        confidence_thresholds: {
                                            ...settings.confidence_thresholds,
                                            low: parseFloat(e.target.value) / 100,
                                        },
                                    })
                                }
                                className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-pink-500"
                            />
                        </div>
                    </div>
                </div>
            )}

            {/* Save Button */}
            <div className="flex justify-end">
                <button
                    onClick={handleSave}
                    className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white rounded-xl font-medium shadow-lg shadow-indigo-500/30 transition-all hover:scale-105"
                >
                    <Save className="w-5 h-5" />
                    Save Changes
                </button>
            </div>
        </div>
    );
}
