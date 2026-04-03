const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const apiClient = {
    async getStats() {
        const res = await fetch(`${API_BASE_URL}/stats`, {
            next: { revalidate: 10 },
        });
        if (!res.ok) throw new Error('Failed to fetch stats');
        return res.json();
    },

    async getCategories() {
        const res = await fetch(`${API_BASE_URL}/categories`, {
            next: { revalidate: 10 },
        });
        if (!res.ok) throw new Error('Failed to fetch categories');
        return res.json();
    },

    async getConfidence() {
        const res = await fetch(`${API_BASE_URL}/confidence`, {
            next: { revalidate: 10 },
        });
        if (!res.ok) throw new Error('Failed to fetch confidence');
        return res.json();
    },

    async getActivity(limit = 50) {
        const res = await fetch(`${API_BASE_URL}/activity?limit=${limit}`, {
            next: { revalidate: 5 },
        });
        if (!res.ok) throw new Error('Failed to fetch activity');
        return res.json();
    },

    async getTodayActivity() {
        const res = await fetch(`${API_BASE_URL}/activity/today`, {
            next: { revalidate: 5 },
        });
        if (!res.ok) throw new Error('Failed to fetch today activity');
        return res.json();
    },

    async getSummary() {
        const res = await fetch(`${API_BASE_URL}/summary`, {
            next: { revalidate: 10 },
        });
        if (!res.ok) throw new Error('Failed to fetch summary');
        return res.json();
    },

    async getSettings() {
        const res = await fetch(`${API_BASE_URL}/settings`, {
            next: { revalidate: 60 },
        });
        if (!res.ok) throw new Error('Failed to fetch settings');
        return res.json();
    },
};
