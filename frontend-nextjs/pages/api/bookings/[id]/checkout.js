const BACKEND = process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_DJANGO_API_BASE || 'https://parking-backend-22m3.onrender.com';

export default async function handler(req, res) {
  const { id } = req.query;
  try {
    const response = await fetch(`${BACKEND.replace(/\/+$/, '')}/api/bookings/${id}/checkout/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    const payload = await response.text();
    res.status(response.status).setHeader('Content-Type', 'application/json');
    res.send(payload);
  } catch (error) {
    res.status(500).json({ message: error.message || 'Proxy fetch failed' });
  }
}
