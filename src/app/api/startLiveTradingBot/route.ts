import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const authHeader = request.headers.get('authorization');
    if (!authHeader) {
      return NextResponse.json({ error: 'No authorization header' }, { status: 401 });
    }

    const body = await request.json();
    
    const response = await fetch(
      'https://us-central1-tbsignalstream.cloudfunctions.net/startLiveTradingBot',
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': authHeader,
        },
        body: JSON.stringify(body),
      }
    );

    const data = await response.json();
    
    if (!response.ok) {
      return NextResponse.json(data, { status: response.status });
    }

    return NextResponse.json(data);
  } catch (error: any) {
    console.error('[API startLiveTradingBot] Error:', error);
    return NextResponse.json(
      { error: error.message || 'Failed to start trading bot' },
      { status: 500 }
    );
  }
}
