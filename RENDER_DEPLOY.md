# Render deployment guide

## Build command

pip install -r requirements.txt && python manage.py migrate && python manage.py seed_parking_data && python manage.py collectstatic --noinput

## Start command

gunicorn parking_project.wsgi:application

## Environment variables

- SECRET_KEY=<generate on Render>
- DEBUG=False
- ALLOWED_HOSTS=<your-render-domain>
- CORS_ALLOWED_ORIGINS=https://<your-vercel-domain>
- DATABASE_URL=<Render PostgreSQL connection>

## Fix an already deployed empty database

If `/api/lots/` returns `[]`, run this in the Render shell:

```bash
python manage.py migrate
python manage.py seed_parking_data
```
