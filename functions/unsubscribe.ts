interface Env {
  DB: D1Database;
}

function page(message: string) {
  return `<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>러너리 수신거부</title>
</head>
<body style="margin:0;background:#f7f5f1;color:#111514;font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo','Noto Sans KR','Malgun Gothic',Arial,sans-serif;">
  <main style="max-width:560px;margin:0 auto;padding:72px 24px;text-align:center;">
    <div style="font-size:13px;font-weight:900;color:#ff6b4a;">runeorrri</div>
    <h1 style="margin:14px 0 10px;font-size:28px;line-height:1.25;">${message}</h1>
    <p style="margin:0;color:#6f7773;font-size:15px;line-height:1.7;">다시 받고 싶다면 러너리 웹사이트에서 같은 이메일로 재구독할 수 있습니다.</p>
    <a href="/" style="display:inline-block;margin-top:28px;color:#111514;font-weight:800;">러너리로 돌아가기</a>
  </main>
</body>
</html>`;
}

export const onRequestGet: PagesFunction<Env> = async (context) => {
  const url = new URL(context.request.url);
  const email = (url.searchParams.get('email') ?? '').toLowerCase().trim();
  const headers = { 'Content-Type': 'text/html; charset=utf-8' };

  if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    return new Response(page('수신거부 링크가 올바르지 않습니다.'), { status: 400, headers });
  }

  try {
    await context.env.DB.prepare(
      'UPDATE subscribers SET status = ? WHERE email = ?'
    ).bind('unsubscribed', email).run();

    return new Response(page('수신거부가 완료됐습니다.'), { headers });
  } catch {
    return new Response(page('잠시 후 다시 시도해주세요.'), { status: 500, headers });
  }
};
