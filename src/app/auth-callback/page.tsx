'use client';

import { useEffect, useState, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { toast } from 'sonner';
import { httpsCallable } from 'firebase/functions';
import { functions, auth } from '@/lib/firebase';
import { isSignInWithEmailLink, signInWithEmailLink } from 'firebase/auth';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Loader2 } from 'lucide-react';

function AuthCallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [flow, setFlow] = useState<'firebase' | 'angelone' | 'error' | 'loading'>('loading');
  const [message, setMessage] = useState('Verifying your request...');

  // State for Angel One flow
  const [authToken, setAuthToken] = useState<string | null>(null);
  const [totp, setTotp] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    const currentUrl = window.location.href;
    const angelAuthToken = searchParams.get('auth_token');

    if (isSignInWithEmailLink(auth, currentUrl)) {
      setFlow('firebase');
      setMessage('Confirming your email address...');
      const email = window.localStorage.getItem('emailForSignIn');
      if (!email) {
        setMessage('Could not find your email for sign-in. Please try logging in again.');
        toast.error('Login session expired.');
        setFlow('error');
        return;
      }

      signInWithEmailLink(auth, email, currentUrl)
        .then(() => {
          window.localStorage.removeItem('emailForSignIn');
          setMessage('You have been successfully signed in! Redirecting...');
          toast.success('Login Successful!');
          router.push('/settings');
        })
        .catch((err) => {
          console.error("Firebase sign-in error:", err);
          setMessage(`Login failed: ${err.message}. Please try again.`);
          toast.error("Login Failed", { description: err.message });
          setFlow('error');
        });
    } else if (angelAuthToken) {
      setFlow('angelone');
      setAuthToken(angelAuthToken);
    } else {
      setMessage('Invalid callback URL. No authentication details found.');
      setFlow('error');
    }
  }, [router, searchParams]);

  const handleAngelSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!authToken || totp.length !== 6) {
      toast.error("Invalid Input", { description: "Please enter a valid 6-digit TOTP." });
      return;
    }

    setIsSubmitting(true);
    setMessage(''); // Clear any previous error messages

    try {
      const exchangeTokenForSession = httpsCallable(functions, 'exchangeTokenForSession');
      await exchangeTokenForSession({ authToken, totp });
      toast.success("Success!", { description: "Your Angel One account has been securely connected." });
      router.push('/settings');
    } catch (err: any) {
      console.error("Token exchange error:", err);
      const errorMessage = err.message || "An unknown error occurred. Please try again.";
      setMessage(errorMessage);
      toast.error("Connection Failed", { description: errorMessage });
    } finally {
      setIsSubmitting(false);
    }
  };

  if (flow === 'loading' || flow === 'firebase') {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle>Please Wait</CardTitle>
          </CardHeader>
          <CardContent className="flex items-center justify-center space-x-3 py-6">
            <Loader2 className="h-6 w-6 animate-spin text-primary" />
            <p className="text-muted-foreground">{message}</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (flow === 'angelone') {
    return (
      <div className="flex items-center justify-center min-h-screen bg-muted/40">
        <Card className="w-full max-w-sm">
          <form onSubmit={handleAngelSubmit}>
            <CardHeader className="text-center">
              <CardTitle>Complete Connection</CardTitle>
              <CardDescription>Enter the 2FA code from your authenticator app.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Input
                type="text"
                value={totp}
                onChange={(e) => setTotp(e.target.value.replace(/[^0-9]/g, ''))}
                maxLength={6}
                placeholder="123456"
                className="text-center text-2xl tracking-widest font-mono h-14"
                disabled={isSubmitting}
                required
              />
              {message && <p className="text-sm text-center text-destructive">{message}</p>}
            </CardContent>
            <CardFooter>
              <Button type="submit" className="w-full" disabled={isSubmitting || totp.length !== 6}>
                {isSubmitting ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : "Connect Account"}
              </Button>
            </CardFooter>
          </form>
        </Card>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-center min-h-screen">
      <Card className="w-full max-w-md border-destructive bg-destructive/10">
        <CardHeader>
          <CardTitle className="text-destructive">An Error Occurred</CardTitle>
        </CardHeader>
        <CardContent>
          <p>{message}</p>
        </CardContent>
        <CardFooter>
          <Button onClick={() => router.push('/')} variant="secondary" className="w-full">Go to Homepage</Button>
        </CardFooter>
      </Card>
    </div>
  );
}

export default function AuthCallbackPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <AuthCallbackContent />
    </Suspense>
  );
}
