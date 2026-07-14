const BACKEND = process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_DJANGO_API_BASE || 'https://parking-backend-22m3.onrender.com';

export default async function handler(req, res) {
  const { id } = req.query;
  try {
    const url = new URL(`${BACKEND.replace(/\/+$/, '')}/api/lots/${id}/slots/available/`);
    Object.entries(req.query || {}).forEach(([key, value]) => {
      if (key === 'id') return;
      if (Array.isArray(value)) {
        value.forEach((entry) => url.searchParams.append(key, entry));
      } else if (value !== undefined) {
        url.searchParams.set(key, value);
      }
    });

    const r = await fetch(url.toString());
    const text = await r.text();
    try {
      const json = JSON.parse(text);
      res.status(r.status).json(json);
    } catch (err) {
      res.status(r.status).send(text);
    }
  } catch (err) {
    res.status(500).json({ message: err.message || 'Proxy fetch failed' });
  }
}
