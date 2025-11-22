'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';
import { useAuth } from '@/context/auth-context';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export function AngelConnectButton() {
    const [clientCode, setClientCode] = useState('');
    const [pin, setPin] = useState('');
    const [totp, setTotp] = useState('');
    const [isConnecting, setIsConnecting] = useState(false);
    const { firebaseUser } = useAuth();
    const router = useRouter();

    async function postWithFallback(path: string, idToken: string, payload: any) {
        const tryRequest = async (url: string) => {
            const res = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${idToken}`
                },
                body: JSON.stringify(payload)
            });
            return res;
        };

        // First try relative path (works when hosting rewrites are in place)
        let res = await tryRequest(path);

        // If we got a non-JSON HTML 404 from preview domain, retry against public web.app
        const contentType = res.headers.get('content-type') || '';
        if ((res.status === 404 || contentType.includes('text/html')) && typeof window !== 'undefined' && window.location.hostname.includes('hosted.app')) {
            console.info('Preview domain returned HTML/404; retrying against public hosting domain.');
            const publicUrl = 'https://tbsignalstream.web.app/api/directAngelLogin';
            res = await tryRequest(publicUrl);
        }

        return res;
    }

    const handleConnect = async () => {
        if (!firebaseUser) {
            toast.error("You must be logged in to connect your Angel One account.");
            return;
        }

        if (!clientCode || !pin || !totp) {
            toast.error("Please fill in all Angel One credentials.");
            return;
        }
        
        setIsConnecting(true);
        
        try {
            const idToken = await firebaseUser.getIdToken();

            const response = await postWithFallback('/api/directAngelLogin', idToken, { clientCode, pin, totp });
            let data: any = {};
            const contentType = response.headers.get('content-type') || '';
            if (contentType.includes('application/json')) {
                data = await response.json().catch((err) => {
                    console.warn('Failed to parse JSON response:', err);
                    return {};
                });
            } else {
                const text = await response.text().catch(() => '');
                console.warn('Non-JSON response from /api/directAngelLogin:', response.status, text);
                data = { error: text || `HTTP ${response.status}` };
            }

            if (response.ok) {
                console.log('[AngelConnect] Connection successful, redirecting to dashboard...');
                toast.success(data.message || "Angel One account connected successfully!");
                
                // Clear form
                setClientCode('');
                setPin('');
                setTotp('');
                
                // Redirect to dashboard after 1 second using window.location (works with static hosting)
                setTimeout(() => {
                    console.log('[AngelConnect] Executing redirect to /');
                    window.location.href = '/';
                }, 1500);
            } else {
                console.error('[AngelConnect] Connection failed:', data.error);
                toast.error(data.error || `Failed to connect Angel One account. HTTP ${response.status}`);
            }
        } catch (error) {
            console.error("Direct login error:", error);
            toast.error("An unexpected error occurred. See console for details.");
        } finally {
            setIsConnecting(false);
        }
    };

    const handleAuthenticatedTest = async () => {
        if (!firebaseUser) {
            toast.error("You must be logged in to run the authenticated test.");
            return;
        }

        const confirmRun = window.confirm(
            'Run authenticated Angel One login test using the server-side credentials (if configured)?\n\nThis will send your current Firebase ID token to the server. Proceed?'
        );
        if (!confirmRun) return;

        try {
            const idToken = await firebaseUser.getIdToken();

            const payload: any = {};
            if (clientCode) payload.clientCode = clientCode;
            if (pin) payload.pin = pin;
            if (totp) payload.totp = totp;

            console.debug('Authenticated test: sending POST /api/directAngelLogin', { payload });

            const response = await postWithFallback('/api/directAngelLogin', idToken, payload);
            let data: any = {};
            const contentType2 = response.headers.get('content-type') || '';
            if (contentType2.includes('application/json')) {
                data = await response.json().catch(() => ({}));
            } else {
                const text = await response.text().catch(() => '');
                console.warn('Authenticated test: non-JSON response', response.status, text);
                data = { error: text || `HTTP ${response.status}` };
            }
            console.debug('Authenticated test response:', response.status, data);

            if (response.ok) {
                toast.success(data.message || 'Authenticated test succeeded.');
            } else {
                toast.error(data.error || `Authenticated test failed (${response.status}).`);
            }
        } catch (err) {
            console.error('Authenticated test error:', err);
            toast.error('Authenticated test encountered an error. See console for details.');
        }
    };

    if (!firebaseUser) {
        return (
            <Card className="w-full max-w-md">
                <CardHeader>
                    <CardTitle>Connect to Angel One</CardTitle>
                    <CardDescription>
                        Please sign in or create an account to connect your Angel One brokerage.
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <p>You are not logged in.</p>
                </CardContent>
            </Card>
        );
    }

    return (
        <div className="flex flex-col space-y-4">
            <h3 className="text-lg font-semibold">Connect to Angel One</h3>
            <div>
                <Label htmlFor="clientCode">Client Code / Email / Mobile</Label>
                <Input id="clientCode" type="text" value={clientCode} onChange={(e) => setClientCode(e.target.value)} placeholder="Your Angel One Client ID, Email, or Mobile" />
            </div>
            <div>
                <Label htmlFor="pin">PIN</Label>
                <Input id="pin" type="password" value={pin} onChange={(e) => setPin(e.target.value)} placeholder="Your Angel One PIN" />
            </div>
            <div>
                <Label htmlFor="totp">TOTP</Label>
                <Input id="totp" type="text" value={totp} onChange={(e) => setTotp(e.target.value)} placeholder="Your 6-digit TOTP" />
            </div>
            <Button onClick={handleConnect} disabled={isConnecting}>
                {isConnecting ? 'Connecting...' : 'Connect Account'}
            </Button>
            <Button onClick={handleAuthenticatedTest} className="mt-2" disabled={isConnecting}>
                Authenticated Test (send ID token)
            </Button>
        </div>
    );
}
