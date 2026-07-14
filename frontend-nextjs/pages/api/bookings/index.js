const BACKEND = process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_DJANGO_API_BASE || 'https://parking-backend-22m3.onrender.com';

export default async function handler(req, res) {
  try {
    const url = `${BACKEND.replace(/\/+$/, '')}/api/bookings/`;
    const options = {
      method: req.method,
      headers: {}
    };

    if (req.method === 'POST' || req.method === 'PATCH') {
      options.headers['Content-Type'] = 'application/json';
      options.body = JSON.stringify(req.body);
    }

    const response = await fetch(url, options);
    const payload = await response.text();
    res.status(response.status).setHeader('Content-Type', 'application/json');
    res.send(payload);
  } catch (error) {
    res.status(500).json({ message: error.message || 'Proxy fetch failed' });
  }
}
