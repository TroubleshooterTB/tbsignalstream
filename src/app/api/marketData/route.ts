import { NextRequest, NextResponse } from 'next/server';
import { auth } from '@/lib/firebase';

export async function POST(request: NextRequest) {
  try {
    // Verify authentication
    const authHeader = request.headers.get('authorization');
    if (!authHeader?.startsWith('Bearer ')) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    // Get request body
    const body = await request.json();
    const { symbols } = body;

    if (!symbols || !Array.isArray(symbols)) {
      return NextResponse.json(
        { error: 'Invalid request: symbols array required' },
        { status: 400 }
      );
    }

    // Forward request to Cloud Run backend
    const backendUrl = process.env.NEXT_PUBLIC_TRADING_BOT_URL || 
                       'https://trading-bot-service-vmxfbt7qiq-el.a.run.app';
    
    const response = await fetch(`${backendUrl}/market_data`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': authHeader,
      },
      body: JSON.stringify({ symbols }),
    });

    if (!response.ok) {
      const error = await response.json();
      return NextResponse.json(
        { error: error.error || 'Failed to fetch market data' },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);

  } catch (error) {
    console.error('Market data API error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
