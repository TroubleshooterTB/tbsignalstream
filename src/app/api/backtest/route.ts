import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { strategy, start_date, end_date, symbols, capital } = body;

    // Validate inputs
    if (!strategy || !start_date || !end_date) {
      return NextResponse.json(
        { error: 'Missing required fields: strategy, start_date, end_date' },
        { status: 400 }
      );
    }

    // Get backend URL from environment or default
    const backendUrl = process.env.BACKEND_URL || 'https://trading-bot-service-vmxfbt7qiq-el.a.run.app';

    // Forward request to Cloud Run backend
    const response = await fetch(`${backendUrl}/backtest`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        strategy,
        start_date,
        end_date,
        symbols: symbols || 'NIFTY50',
        capital: capital || 100000,  // Default to ₹1L if not provided
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Backend backtest error:', errorText);
      return NextResponse.json(
        { error: `Backtest failed: ${errorText}` },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);

  } catch (error) {
    console.error('Backtest API error:', error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Internal server error' },
      { status: 500 }
    );
  }
}
