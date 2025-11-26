import type {Metadata} from 'next';
import './globals.css';
import { Toaster } from "sonner";
import { MainLayout } from '@/components/main-layout';
import { AuthProvider } from '@/context/auth-context';
import { TradingProvider } from '@/context/trading-context';

export const metadata: Metadata = {
  title: 'SignalStream',
  description: 'Live Tactical Alert Engine for the Indian stock market.',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet" />
      </head>
      <body className="font-body antialiased">
        <AuthProvider>
          <TradingProvider>
            <MainLayout>
              {children}
            </MainLayout>
          </TradingProvider>
        </AuthProvider>
        <Toaster />
      </body>
    </html>
  );
}
