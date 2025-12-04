'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { sendSignInLinkToEmail } from 'firebase/auth';
import { auth } from '@/lib/firebase';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    
    const actionCodeSettings = {
      url: `${window.location.origin}/auth-callback`,
      handleCodeInApp: true,
    };

    // Retry logic for network errors
    const maxRetries = 3;
    let lastError: any = null;
    
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        console.log(`Login attempt ${attempt}/${maxRetries}...`);
        await sendSignInLinkToEmail(auth, email, actionCodeSettings);
        window.localStorage.setItem('emailForSignIn', email);
        setIsLoading(false);
        alert(`✅ Sign-in link sent to ${email}. Check your inbox!`);
        return; // Success!
      } catch (error: any) {
        lastError = error;
        console.error(`Firebase sign-in error (attempt ${attempt}):`, error);
        
        // If it's not a network error, don't retry
        if (error.code !== 'auth/network-request-failed') {
          break;
        }
        
        // Wait before retrying (exponential backoff)
        if (attempt < maxRetries) {
          const waitTime = Math.pow(2, attempt) * 500; // 1s, 2s, 4s
          console.log(`Retrying in ${waitTime}ms...`);
          await new Promise(resolve => setTimeout(resolve, waitTime));
        }
      }
    }
    
    // All retries failed
    setIsLoading(false);
    const errorMessage = lastError?.code === 'auth/network-request-failed'
      ? 'Network error. Please check your internet connection and try again.'
      : lastError?.message || 'Login failed. Please try again.';
    setError(errorMessage);
    alert(`❌ ${errorMessage}`);
  };

  return (
    <div className="flex min-h-screen items-center justify-center">
      <Card className="mx-auto max-w-sm">
        <CardHeader>
          <CardTitle className="text-2xl">Login</CardTitle>
          <CardDescription>Enter your email below to receive a login link.</CardDescription>
        </CardHeader>
        <CardContent>
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}
          <form onSubmit={handleLogin} className="grid gap-4">
            <div className="grid gap-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="me@example.com"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={isLoading}
              />
            </div>
            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? 'Sending...' : 'Send Login Link'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
