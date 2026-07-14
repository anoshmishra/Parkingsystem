const BACKEND = process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_DJANGO_API_BASE || 'https://parking-backend-22m3.onrender.com';

export default async function handler(req, res) {
  try {
    const r = await fetch(`${BACKEND.replace(/\/+$/, '')}/api/lots/`);
    const text = await r.text();
    try {
      const json = JSON.parse(text);
      res.status(r.status).json(json);
    } catch (err) {
      // fallback: return raw text
      res.status(r.status).send(text);
    }
  } catch (err) {
    res.status(500).json({ message: err.message || 'Proxy fetch failed' });
  }
}
