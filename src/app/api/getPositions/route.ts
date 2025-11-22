import { NextRequest, NextResponse } from 'next/server';

/**
 * Get Positions API Route
 */
export async function GET(request: NextRequest) {
  try {
    const authHeader = request.headers.get('Authorization');

    if (!authHeader) {
      return NextResponse.json(
        { error: 'Missing Authorization header' },
        { status: 401 }
      );
    }

    const response = await fetch(
      'https://us-central1-tbsignalstream.cloudfunctions.net/getPositions',
      {
        method: 'GET',
        headers: {
          'Authorization': authHeader,
        },
      }
    );

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Get positions API error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
