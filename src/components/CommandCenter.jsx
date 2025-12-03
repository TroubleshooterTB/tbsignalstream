import React, { useState, useEffect } from 'react';
// Import the initialized auth and db from our central firebase.js file
import { auth, db } from '@/lib/firebase';
import { sendSignInLinkToEmail, isSignInWithEmailLink, signInWithEmailLink, onAuthStateChanged } from 'firebase/auth';
import {
    doc, collection, query, limit, onSnapshot
} from 'firebase/firestore';

// --- Global Variables (Provided by Canvas Environment) ---
// Keep appId logic as it seems to be for Firestore paths and separate from the auth issue
const appId = typeof __app_id !== 'undefined' ? __app_id : 'default-app-id';

// This is the main Command Center component for the vX Grandmaster Engine.
const CommandCenter = () => {
    const [botStatus, setBotStatus] = useState({});
    const [marketAnalysis, setMarketAnalysis] = useState({});
    const [openPositions, setOpenPositions] = useState([]);
    const [closedPositions, setClosedPositions] = useState([]);
    const [recentLogs, setRecentLogs] = useState([]);
    const [firebaseReady, setFirebaseReady] = useState(false);
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [email, setEmail] = useState('');
    const [emailSent, setEmailSent] = useState(false);

    // 1. Firebase Authentication
    useEffect(() => {
        // Use the imported auth object directly. No need to initialize the app here.
        try {
            // Handle the sign-in link verification
            if (isSignInWithEmailLink(auth, window.location.href)) {
                let emailForSignIn = window.localStorage.getItem('emailForSignIn');
                if (!emailForSignIn) {
                    emailForSignIn = window.prompt('Please provide your email for confirmation');
                }
                if (emailForSignIn) {
                    signInWithEmailLink(auth, emailForSignIn, window.location.href)
                        .then((result) => {
                            window.localStorage.removeItem('emailForSignIn');
                            setUser(result.user);
                            setFirebaseReady(true); // Firebase is ready once the user is signed in
                        })
                        .catch((error) => {
                            console.error("Sign in with email link error:", error);
                            setLoading(false);
                        });
                }
            } else {
                 // Set up Auth State Listener
                const unsubscribeAuth = onAuthStateChanged(auth, (currentUser) => {
                    if (currentUser) {
                        setUser(currentUser);
                        setFirebaseReady(true);
                    } else {
                        setUser(null);
                        setFirebaseReady(false); // No user, so Firebase is not 'ready' for data fetching
                    }
                    setLoading(false);
                });
                return () => unsubscribeAuth();
            }
        } catch (error) {
            console.error("Firebase auth check failed:", error);
            setLoading(false);
        }
    }, []); // Empty dependency array means this runs once on mount

    // 2. Firestore Listeners
    useEffect(() => {
        // Only run if firebase is ready and we have a user
        if (!firebaseReady || !user) return;

        // Use the imported db object directly. No need to initialize app or get firestore.
        const getPublicDataPath = (collectionName) =>
            `/artifacts/${appId}/public/data/${collectionName}`;

        const listeners = [];

        try {
            const statusDocRef = doc(db, getPublicDataPath('bot_status'), 'settings');
            listeners.push(onSnapshot(statusDocRef, (docSnap) => {
                setBotStatus(docSnap.exists() ? docSnap.data() : {});
            }, (error) => console.error("Error fetching bot status:", error)));

            const analysisDocRef = doc(db, getPublicDataPath('market_analysis'), 'latest');
            listeners.push(onSnapshot(analysisDocRef, (docSnap) => {
                setMarketAnalysis(docSnap.exists() ? docSnap.data() : {});
            }, (error) => console.error("Error fetching market analysis:", error)));

            const openPositionsQ = query(collection(db, getPublicDataPath('positions_open')));
            listeners.push(onSnapshot(openPositionsQ, (snapshot) => {
                const positions = snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
                setOpenPositions(positions);
            }, (error) => console.error("Error fetching open positions:", error)));

            const closedPositionsQ = query(collection(db, getPublicDataPath('positions_closed')));
            listeners.push(onSnapshot(closedPositionsQ, (snapshot) => {
                const positions = snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
                positions.sort((a, b) => (b.exit_timestamp || 0) - (a.exit_timestamp || 0));
                setClosedPositions(positions);
            }, (error) => console.error("Error fetching closed positions:", error)));
            
            const logsQ = query(collection(db, getPublicDataPath('logs')), limit(50));
            listeners.push(onSnapshot(logsQ, (snapshot) => {
                let logs = snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
                logs.sort((a, b) => (a.timestamp || 0) - (b.timestamp || 0));
                setRecentLogs(logs);
            }, (error) => console.error("Error fetching recent logs:", error)));

        } catch (e) {
            console.error("Error setting up Firestore listeners:", e);
        }

        return () => listeners.forEach(unsub => unsub());
    }, [firebaseReady, user]);

    const handleLogin = async (e) => {
        e.preventDefault();
        // Use the imported auth object
        const actionCodeSettings = {
            url: window.location.href, // URL to redirect back to
            handleCodeInApp: true,
        };

        try {
            await sendSignInLinkToEmail(auth, email, actionCodeSettings);
            window.localStorage.setItem('emailForSignIn', email);
            setEmailSent(true);
            alert(`A sign-in link has been sent to ${email}.`);
        } catch (error) {
            console.error("Firebase Login Error:", error);
            alert(`Login Failed: ${error.message}`);
        }
    };

    if (loading) {
        return (
            <div className="flex justify-center items-center h-screen bg-gray-900 text-white">
                <div className="text-xl font-mono animate-pulse">
                    Initializing vX Grandmaster Engine...
                </div>
            </div>
        );
    }
    
    if (!user) {
        return (
            <div className="flex min-h-screen items-center justify-center bg-gray-900">
                <div className="mx-auto max-w-sm p-8 rounded-xl dashboard-card">
                    <h1 className="text-2xl font-bold text-teal-400 mb-2">vX Grandmaster Engine</h1>
                    <p className="text-gray-400 mb-6">Enter your email to receive a login link.</p>
                    {emailSent ? (
                        <p className="text-green-400">Please check your email for the login link.</p>
                    ) : (
                        <form onSubmit={handleLogin} className="grid gap-4">
                            <div className="grid gap-2">
                                <label htmlFor="email" className="text-gray-300">Email</label>
                                <input
                                    id="email"
                                    type="email"
                                    placeholder="me@example.com"
                                    required
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    className="w-full p-2 rounded bg-gray-800 border border-gray-700 text-white focus:outline-none focus:ring-2 focus:ring-teal-500"
                                />
                            </div>
                            <button type="submit" className="w-full bg-teal-600 hover:bg-teal-700 text-white font-bold py-2 px-4 rounded transition duration-300">
                                Send Login Link
                            </button>
                        </form>
                    )}
                </div>
            </div>
        )
    }

    // Helper function for rendering numerical data cleanly
    const formatValue = (value) => {
        if (typeof value === 'number') {
            return value.toFixed(2);
        }
        return value || 'N/A';
    };

    // Main Component Rendering
    return (
        <div className="min-h-screen bg-gray-900 text-gray-100 p-4 sm:p-8 font-inter">
            <style>
                {`
                @import url('https://fonts.googleapis.com/css2?family=Inter:wght@100..900&display=swap');
                .font-inter { font-family: 'Inter', sans-serif; }
                .dashboard-card {
                    background: #1f2937;
                    border: 1px solid #374151;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                }
                .log-line {
                    font-family: monospace;
                    font-size: 0.8rem;
                    white-space: pre-wrap;
                    word-break: break-all;
                }
                `}
            </style>

            <header className="mb-8 text-center">
                <h1 className="text-4xl font-bold text-teal-400 mb-2">vX Grandmaster Engine</h1>
                <p className="text-lg text-gray-400">Real-Time Command Center Dashboard</p>
                <p className="text-sm text-gray-500 mt-2">
                    <span className="font-semibold">User ID:</span> {user.uid}
                </p>
            </header>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

                {/* 1. Bot Status */}
                <section className="dashboard-card p-6 rounded-xl lg:col-span-1">
                    <h2 className="text-2xl font-semibold border-b border-gray-600 pb-3 mb-4 text-teal-300">
                        Operational Status
                    </h2>
                    <div className="space-y-3">
                        <div className="flex justify-between items-center">
                            <span className="text-gray-400">Engine State:</span>
                            <span className={\`font-bold py-1 px-3 rounded-full text-sm \${
                                botStatus.enabled ? 'bg-green-600 text-white' : 'bg-red-600 text-white'
                            }\`}>
                                {botStatus.enabled ? 'ACTIVE' : 'IDLE'}
                            </span>
                        </div>
                        <p><span className="text-gray-400">Engine Version:</span> <span className="font-mono text-sm">{botStatus.version || 'vX.0.1'}</span></p>
                        <p><span className="text-gray-400">Connected Exchange:</span> {botStatus.exchange || 'Simulated Broker'}</p>
                        <p><span className="text-gray-400">Last Heartbeat:</span> {botStatus.last_heartbeat ? new Date(botStatus.last_heartbeat).toLocaleString() : 'N/A'}</p>
                    </div>
                </section>

                {/* 2. Market Analysis */}
                <section className="dashboard-card p-6 rounded-xl lg:col-span-2">
                    <h2 className="text-2xl font-semibold border-b border-gray-600 pb-3 mb-4 text-teal-300">
                        Contextual Market Analysis
                    </h2>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div>
                            <p><span className="text-gray-400">Daily Bias:</span> <span className="font-semibold text-yellow-300">{marketAnalysis.daily_status?.health || 'Neutral'}</span></p>
                            <p><span className="text-gray-400">Active Persona:</span> <span className="font-semibold text-blue-300">{marketAnalysis.daily_status?.active_persona || 'The Opportunist'}</span></p>
                            <p><span className="text-gray-400">Weekly Pattern:</span> <span className="font-mono text-sm">{marketAnalysis.weekly_bias?.best_performing_pattern || 'Volatility Spike'}</span></p>
                        </div>
                        <div>
                            <p><span className="text-gray-400">Weekly Win Rate Bias:</span> <span className="font-semibold">{formatValue((marketAnalysis.weekly_bias?.win_rate_bias || 0) * 100)}%</span></p>
                            <p><span className="text-gray-400">Intermarket (NIFTY):</span> <span className="font-semibold text-orange-300">{marketAnalysis.inter_market_context?.nifty_trend || 'Range-Bound'}</span></p>
                            <p><span className="text-gray-400">Intermarket (USDINR):</span> <span className="font-semibold text-green-300">{marketAnalysis.inter_market_context?.usdinr_trend || 'Weakness'}</span></p>
                        </div>
                    </div>
                </section>
            </div>


            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
                {/* 3. Open Positions */}
                <section className="dashboard-card p-6 rounded-xl overflow-x-auto">
                    <h2 className="text-2xl font-semibold border-b border-gray-600 pb-3 mb-4 text-teal-300">
                        Open Positions ({openPositions.length})
                    </h2>
                    <table className="min-w-full divide-y divide-gray-700">
                        <thead>
                            <tr>
                                <th className="px-3 py-2 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Symbol</th>
                                <th className="px-3 py-2 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Entry Price</th>
                                <th className="px-3 py-2 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Stop Loss</th>
                                <th className="px-3 py-2 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Direction</th>
                                <th className="px-3 py-2 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">P&L (%)</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-800">
                            {openPositions.map((pos) => (
                                <tr key={pos.id || pos.symbol} className="hover:bg-gray-800 transition duration-150">
                                    <td className="px-3 py-2 whitespace-nowrap font-semibold">{pos.symbol}</td>
                                    <td className="px-3 py-2 whitespace-nowrap">{formatValue(pos.entry_price)}</td>
                                    <td className="px-3 py-2 whitespace-nowrap text-red-400">{formatValue(pos.current_stop_loss)}</td>
                                    <td className="px-3 py-2 whitespace-nowrap">
                                        <span className={\`text-xs font-bold py-1 px-2 rounded \${pos.direction === 'LONG' ? 'bg-green-900 text-green-400' : 'bg-red-900 text-red-400'}\`}>
                                            {pos.direction}
                                        </span>
                                    </td>
                                    <td className={\`px-3 py-2 whitespace-nowrap font-mono \${formatValue(pos.pnl_percentage || 0.01) >= 0 ? 'text-green-400' : 'text-red-400'}\`}>
                                        {formatValue((pos.pnl_percentage || 0.01) * 100)}%
                                    </td>
                                </tr>
                            ))}
                            {openPositions.length === 0 && (
                                <tr>
                                    <td colSpan="5" className="px-6 py-4 text-center text-gray-500">No active positions.</td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </section>

                {/* 4. Closed Positions */}
                <section className="dashboard-card p-6 rounded-xl overflow-x-auto">
                    <h2 className="text-2xl font-semibold border-b border-gray-600 pb-3 mb-4 text-teal-300">
                        Closed Positions ({closedPositions.length})
                    </h2>
                    <table className="min-w-full divide-y divide-gray-700">
                        <thead>
                            <tr>
                                <th className="px-3 py-2 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Symbol</th>
                                <th className="px-3 py-2 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Exit Price</th>
                                <th className="px-3 py-2 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">P&L (%)</th>
                                <th className="px-3 py-2 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Reason</th>
                                <th className="px-3 py-2 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Time</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-800">
                            {closedPositions.map((pos) => (
                                <tr key={pos.id || pos.symbol} className="hover:bg-gray-800 transition duration-150">
                                    <td className="px-3 py-2 whitespace-nowrap font-semibold">{pos.symbol}</td>
                                    <td className="px-3 py-2 whitespace-nowrap">{formatValue(pos.exit_price)}</td>
                                    <td className={\`px-3 py-2 whitespace-nowrap font-mono \${pos.pnl_percentage >= 0 ? 'text-green-400' : 'text-red-400'}\`}>
                                        {formatValue(pos.pnl_percentage * 100)}%
                                    </td>
                                    <td className="px-3 py-2 whitespace-nowrap text-sm">{pos.status || 'Target Hit'}</td>
                                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-400">
                                        {pos.exit_timestamp ? new Date(pos.exit_timestamp).toLocaleString() : 'N/A'}
                                    </td>
                                </tr>
                            ))}
                            {closedPositions.length === 0 && (
                                <tr>
                                    <td colSpan="5" className="px-6 py-4 text-center text-gray-500">No recent closed positions.</td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </section>
            </div>

            {/* 5. Recent Logs */}
            <section className="dashboard-card p-6 rounded-xl mt-6">
                <h2 className="text-2xl font-semibold border-b border-gray-600 pb-3 mb-4 text-teal-300">
                    Recent Logs
                </h2>
                <div className="bg-gray-800 p-4 rounded-lg h-96 overflow-y-scroll">
                    <ul className="space-y-1">
                        {recentLogs.slice(-20).map((log, index) => (
                            <li key={log.id || index} className="log-line text-gray-300">
                                <span className="text-gray-500 mr-2">
                                    [{log.timestamp ? new Date(log.timestamp).toLocaleTimeString() : 'TIME'}]
                                </span>
                                {log.message}
                            </li>
                        ))}
                        {recentLogs.length === 0 && (
                            <li className="text-gray-500 text-center py-10">No logs available.</li>
                        )}
                    </ul>
                </div>
            </section>

        </div>
    );
};

export default CommandCenter;