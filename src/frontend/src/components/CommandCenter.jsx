// src/components/CommandCenter.jsx

import React, { useState, useEffect } from 'react';
// Import your firebase config to get the db instance
// import { db } from '../firebase'; 
// import { collection, onSnapshot, doc, updateDoc } from 'firebase/firestore';
import './CommandCenter.css';

// --- Mock Firestore for Standalone Demonstration ---
// In your real app, you would remove this and use the real Firebase imports above.
const mockDb = {
    collection: (path) => ({
        onSnapshot: (callback) => {
            // Simulate real-time updates
            setInterval(() => {
                if (path === 'bot_logs') {
                    callback({ docs: [{ id: Math.random(), data: () => ({ timestamp: new Date().toISOString(), message: `Simulated log message ${Math.random()}` }) }] });
                }
            }, 5000);
            // Initial mock data
            if (path === 'open_positions') {
                callback({ docs: [{ id: '1', data: () => ({ symbol: 'RELIANCE.NS', entry_price: 2850.50, current_price: 2855.00, stop_loss: 2840.00, pnl_percentage: 0.15 }) }] });
            }
             if (path === 'closed_positions') {
                callback({ docs: [{ id: '2', data: () => ({ symbol: 'TCS.NS', entry_price: 3400.00, exit_price: 3450.00, pnl_percentage: 1.47, status: 'closed_profit_target' }) }] });
            }
        }
    }),
    doc: (path) => ({
        onSnapshot: (callback) => {
             if (path.includes('bot_settings/status')) {
                callback({ exists: () => true, data: () => ({ enabled: true }) });
            }
            if (path.includes('bot_settings/persona')) {
                callback({ exists: () => true, data: () => ({ override: 'auto' }) });
            }
        }
    })
};
const db = mockDb; // Use the mock for this example
// --- End of Mock Firestore ---


const CommandCenter = () => {
    const [botStatus, setBotStatus] = useState(true);
    const [activePersona, setActivePersona] = useState('auto');
    const [dailyPnl, setDailyPnl] = useState(0.0);
    const [openPositions, setOpenPositions] = useState([]);
    const [closedPositions, setClosedPositions] = useState([]);
    const [botLogs, setBotLogs] = useState([]);

    // Effect for real-time bot settings and status
    useEffect(() => {
        // Listener for the master switch
        const statusUnsub = db.doc('bot_settings/status').onSnapshot(doc => {
            if (doc.exists()) {
                setBotStatus(doc.data().enabled);
            }
        });

        // Listener for persona override
        const personaUnsub = db.doc('bot_settings/persona').onSnapshot(doc => {
            if (doc.exists()) {
                setActivePersona(doc.data().override);
            }
        });

        return () => {
            statusUnsub();
            personaUnsub();
        };
    }, []);

    // Effect for real-time positions
    useEffect(() => {
        const openPosUnsub = db.collection('open_positions').onSnapshot(snapshot => {
            const positions = snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
            setOpenPositions(positions);
        });

        const closedPosUnsub = db.collection('closed_positions').onSnapshot(snapshot => {
            const positions = snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
            setClosedPositions(positions);
            // Calculate Daily PnL from closed positions
            const pnl = positions.reduce((acc, pos) => acc + (pos.pnl_percentage || 0), 0);
            setDailyPnl(pnl);
        });

        return () => {
            openPosUnsub();
            closedPosUnsub();
        };
    }, []);

    // Effect for real-time logs
    useEffect(() => {
        const logsUnsub = db.collection('bot_logs').onSnapshot(snapshot => {
            const logs = snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
            // Keep only the last 50 logs for performance
            setBotLogs(prevLogs => [...logs, ...prevLogs].slice(0, 50));
        });
        return () => logsUnsub();
    }, []);

    const handleToggleBot = async () => {
        // In a real app, this would write to Firestore
        // const statusRef = doc(db, 'bot_settings/status');
        // await updateDoc(statusRef, { enabled: !botStatus });
        console.log(`Toggling bot status to ${!botStatus}`);
        setBotStatus(!botStatus); // Optimistic UI update
    };
    
    return (
        <div className="command-center">
            <header className="cc-header">
                <h1>Arcane Nexus - Grandmaster Engine</h1>
                <div className="cc-main-status">
                    <span>BOT STATUS</span>
                    <span className={`status-indicator ${botStatus ? 'enabled' : 'disabled'}`}>
                        {botStatus ? 'LIVE' : 'DISABLED'}
                    </span>
                </div>
            </header>

            <div className="cc-grid">
                {/* Controls Section */}
                <div className="cc-card cc-controls">
                    <h2>COMMAND & CONTROL</h2>
                    <div className="control-item">
                        <label>Master Switch</label>
                        <button onClick={handleToggleBot} className={`toggle-button ${botStatus ? 'btn-danger' : 'btn-success'}`}>
                            {botStatus ? 'DISABLE BOT' : 'ENABLE BOT'}
                        </button>
                    </div>
                    <div className="control-item">
                        <label>Active Persona</label>
                        <select value={activePersona} onChange={(e) => {/* Firestore update logic here */}}>
                            <option value="auto">Auto-Select</option>
                            <option value="TrendFollowerPersona">Trend Follower</option>
                            <option value="ScalperPersona">Scalper</option>
                            <option value="RangeTraderPersona">Range Trader</option>
                        </select>
                    </div>
                     <div className="control-item">
                        <label>Daily P&L</label>
                        <div className={`pnl-display ${dailyPnl >= 0 ? 'pnl-positive' : 'pnl-negative'}`}>
                            {dailyPnl.toFixed(2)}%
                        </div>
                    </div>
                </div>

                {/* Live Status Log */}
                <div className="cc-card cc-logs">
                    <h2>LIVE STATUS LOG</h2>
                    <div className="log-window">
                        {botLogs.map(log => (
                            <p key={log.id}><span>{new Date(log.timestamp).toLocaleTimeString()}</span>: {log.message}</p>
                        ))}
                    </div>
                </div>

                {/* Open Positions */}
                <div className="cc-card cc-positions full-width">
                    <h2>OPEN POSITIONS</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>Symbol</th>
                                <th>Entry Price</th>
                                <th>Current Price</th>
                                <th>Stop Loss</th>
                                <th>Unrealized P&L</th>
                            </tr>
                        </thead>
                        <tbody>
                            {openPositions.length > 0 ? openPositions.map(pos => (
                                <tr key={pos.id}>
                                    <td>{pos.symbol}</td>
                                    <td>{pos.entry_price?.toFixed(2)}</td>
                                    <td>{pos.current_price?.toFixed(2)}</td>
                                    <td>{pos.stop_loss?.toFixed(2)}</td>
                                    <td className={pos.pnl_percentage >= 0 ? 'pnl-positive' : 'pnl-negative'}>
                                        {pos.pnl_percentage?.toFixed(2)}%
                                    </td>
                                </tr>
                            )) : <tr><td colSpan="5">No open positions.</td></tr>}
                        </tbody>
                    </table>
                </div>

                {/* Closed Positions */}
                <div className="cc-card cc-positions full-width">
                    <h2>RECENTLY CLOSED POSITIONS</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>Symbol</th>
                                <th>Entry Price</th>
                                <th>Exit Price</th>
                                <th>Realized P&L</th>
                                <th>Exit Reason</th>
                            </tr>
                        </thead>
                        <tbody>
                            {closedPositions.length > 0 ? closedPositions.map(pos => (
                                <tr key={pos.id}>
                                    <td>{pos.symbol}</td>
                                    <td>{pos.entry_price?.toFixed(2)}</td>
                                    <td>{pos.exit_price?.toFixed(2)}</td>
                                    <td className={pos.pnl_percentage >= 0 ? 'pnl-positive' : 'pnl-negative'}>
                                        {pos.pnl_percentage?.toFixed(2)}%
                                    </td>
                                    <td>{pos.status}</td>
                                </tr>
                            )) : <tr><td colSpan="5">No closed positions today.</td></tr>}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

export default CommandCenter;
