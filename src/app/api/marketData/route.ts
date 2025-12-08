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
    const { mode, exchangeTokens } = body;

    if (!exchangeTokens || typeof exchangeTokens !== 'object') {
      return NextResponse.json(
        { error: 'Invalid request: exchangeTokens object required' },
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
      body: JSON.stringify({ mode, exchangeTokens }),
    });

    if (!response.ok) {
      // Return empty data instead of error when bot not running
      return NextResponse.json(
        { 
          status: false,
          message: 'Market data unavailable',
          data: { fetched: [] }
        },
        { status: 200 }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);

  } catch (error) {
    // Silently handle errors when bot is not running or market is closed
    // This prevents console spam for expected failures
    return NextResponse.json(
      { 
        status: false,
        message: 'Market data unavailable',
        data: { fetched: [] }
      },
      { status: 200 }
    );
  }
}
