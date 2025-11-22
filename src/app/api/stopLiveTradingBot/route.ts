import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const authHeader = request.headers.get('authorization');
    if (!authHeader) {
      return NextResponse.json({ error: 'No authorization header' }, { status: 401 });
    }

    const response = await fetch(
      'https://us-central1-tbsignalstream.cloudfunctions.net/stopLiveTradingBot',
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': authHeader,
        },
      }
    );

    const data = await response.json();
    
    if (!response.ok) {
      return NextResponse.json(data, { status: response.status });
    }

    return NextResponse.json(data);
  } catch (error: any) {
    console.error('[API stopLiveTradingBot] Error:', error);
    return NextResponse.json(
      { error: error.message || 'Failed to stop trading bot' },
      { status: 500 }
    );
  }
}
