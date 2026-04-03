import type { Metadata } from 'next';
import Sidebar from '@/components/Sidebar';
import Header from '@/components/Header';
import './globals.css';

export const metadata: Metadata = {
    title: '🧠 Synapse Dashboard',
    description: 'AI Workspace Intelligence',
};

export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="en">
            <body className="bg-slate-950">
                <div className="flex h-screen overflow-hidden">
                    <Sidebar />
                    <div className="flex-1 flex flex-col ml-64">
                        <Header />
                        <main className="flex-1 overflow-y-auto bg-slate-950">
                            <div className="p-8">{children}</div>
                        </main>
                    </div>
                </div>
            </body>
        </html>
    );
}
