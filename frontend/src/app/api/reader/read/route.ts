import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  try {
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:4141';

    // Forward cookies to backend
    const cookieHeader = request.headers.get('cookie');

    const response = await fetch(`${backendUrl}/api/reader/read`, {
      method: 'GET',
      headers: {
        ...(cookieHeader && { cookie: cookieHeader }),
      },
    });

    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error('API route error:', error);
    return NextResponse.json(
      { message: 'Internal server error' },
      { status: 500 }
    );
  }
}
