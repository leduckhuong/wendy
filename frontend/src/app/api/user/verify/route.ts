import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  try {
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:4141';

    // Forward cookies to backend
    const cookieHeader = request.headers.get('cookie');

    const response = await fetch(`${backendUrl}/api/user/verify`, {
      method: 'GET',
      headers: {
        ...(cookieHeader && { cookie: cookieHeader }),
      },
    });

    if (response.ok) {
      return NextResponse.json({ authenticated: true }, { status: 200 });
    } else {
      return NextResponse.json({ authenticated: false }, { status: 401 });
    }
  } catch (error) {
    console.error('API route error:', error);
    return NextResponse.json(
      { message: 'Internal server error' },
      { status: 500 }
    );
  }
}
