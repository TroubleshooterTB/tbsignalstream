
'use client';

import { useState } from 'react';
import { AlertDetailView } from '@/components/alert-detail-view';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from '@/components/ui/table';

// Mock data for alerts
const alerts = [
    { id: 1, title: 'Unusual Volume', ticker: 'AAPL', severity: 'High', timestamp: '2024-05-23T14:30:00Z', source: 'Market Data Feed' },
    { id: 2, title: 'Price Spike', ticker: 'GOOGL', severity: 'Medium', timestamp: '2024-05-23T14:35:00Z', source: 'News Alert' },
    { id: 3, title: 'Sentiment Shift', ticker: 'TSLA', severity: 'Low', timestamp: '2024-05-23T14:40:00Z', source: 'Social Media Monitor' },
];

export function AlertsDashboard() {
    const [selectedAlert, setSelectedAlert] = useState<any>(null);
    const [isDetailViewOpen, setDetailViewOpen] = useState(false);

    const handleRowClick = (alert: any) => {
        setSelectedAlert(alert);
        setDetailViewOpen(true);
    };

    const handleCloseDetailView = () => {
        setDetailViewOpen(false);
        setSelectedAlert(null);
    };

    return (
        <div>
            <Table>
                <TableHeader>
                    <TableRow>
                        <TableHead>Title</TableHead>
                        <TableHead>Ticker</TableHead>
                        <TableHead>Severity</TableHead>
                        <TableHead>Timestamp</TableHead>
                        <TableHead>Source</TableHead>
                    </TableRow>
                </TableHeader>
                <TableBody>
                    {alerts.map((alert) => (
                        <TableRow key={alert.id} onClick={() => handleRowClick(alert)} className="cursor-pointer">
                            <TableCell>{alert.title}</TableCell>
                            <TableCell>{alert.ticker}</TableCell>
                            <TableCell>{alert.severity}</TableCell>
                            <TableCell>{new Date(alert.timestamp).toLocaleString()}</TableCell>
                            <TableCell>{alert.source}</TableCell>
                        </TableRow>
                    ))}
                </TableBody>
            </Table>
            <AlertDetailView alert={selectedAlert} isOpen={isDetailViewOpen} onClose={handleCloseDetailView} />
        </div>
    );
}
