# Render deployment guide

## Build command

pip install -r requirements.txt && python manage.py migrate && python manage.py collectstatic --noinput

## Start command

gunicorn parking_project.wsgi:application

## Environment variables

- SECRET_KEY=<generate on Render>
- DEBUG=False
- ALLOWED_HOSTS=<your-render-domain>
- DATABASE_URL=<Render PostgreSQL connection>
