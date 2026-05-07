interface Env {
  DB: D1Database;
}

interface RequestBody {
  email: string;
}

export const onRequestPost: PagesFunction<Env> = async (context) => {
  const headers = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
  };

  try {
    const body = await context.request.json() as RequestBody;
    const email = (body.email ?? '').toLowerCase().trim();

    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      return new Response(JSON.stringify({ error: 'invalid_email' }), { status: 400, headers });
    }

    const existing = await context.env.DB.prepare(
      'SELECT id, status FROM subscribers WHERE email = ?'
    ).bind(email).first();

    if (existing) {
      if (existing.status === 'active') {
        return new Response(JSON.stringify({ error: 'already_subscribed' }), { status: 409, headers });
      }

      await context.env.DB.prepare(
        'UPDATE subscribers SET status = ?, subscribed_at = ? WHERE email = ?'
      ).bind('active', new Date().toISOString(), email).run();

      return new Response(JSON.stringify({ ok: true, resubscribed: true }), { headers });
    }

    await context.env.DB.prepare(
      'INSERT INTO subscribers (email, subscribed_at, status) VALUES (?, ?, ?)'
    ).bind(email, new Date().toISOString(), 'active').run();

    return new Response(JSON.stringify({ ok: true }), { headers });
  } catch {
    return new Response(JSON.stringify({ error: 'server_error' }), { status: 500, headers });
  }
};

export const onRequestOptions: PagesFunction = async () => {
  return new Response(null, {
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    },
  });
};
