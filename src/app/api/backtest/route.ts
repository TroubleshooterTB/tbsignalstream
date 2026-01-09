import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { strategy, start_date, end_date, symbols, capital, custom_params } = body;

    // Validate inputs
    if (!strategy || !start_date || !end_date) {
      return NextResponse.json(
        { error: 'Missing required fields: strategy, start_date, end_date' },
        { status: 400 }
      );
    }

    // Get backend URL from environment or default
    const backendUrl = process.env.BACKEND_URL || 'https://trading-bot-service-818546654122.asia-south1.run.app';

    const requestBody: any = {
      strategy,
      start_date,
      end_date,
      symbols: symbols || 'NIFTY50',
      capital: capital || 100000,  // Default to ₹1L if not provided
    };

    // Include custom parameters if provided
    if (custom_params) {
      requestBody.custom_params = custom_params;
      console.log('Using custom parameters:', custom_params);
    }

    console.log('Sending backtest request:', {
      url: `${backendUrl}/backtest`,
      body: requestBody
    });

    // Forward request to Cloud Run backend
    const response = await fetch(`${backendUrl}/backtest`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody),
    });

    if (!response.ok) {
      let errorText = 'Unknown error';
      try {
        errorText = await response.text();
      } catch (e) {
        console.error('Could not read error response:', e);
      }
      console.error('Backend backtest error:', {
        status: response.status,
        statusText: response.statusText,
        error: errorText
      });
      return NextResponse.json(
        { error: `Backtest failed (${response.status}): ${errorText || response.statusText}` },
        { status: response.status }
      );
    }

    const data = await response.json();
    console.log('Backtest successful:', data.summary);
    return NextResponse.json(data);

  } catch (error) {
    console.error('Backtest API error:', error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Internal server error' },
      { status: 500 }
    );
  }
}
