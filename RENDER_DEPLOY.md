# Render deployment guide

## Build command

pip install -r requirements.txt && python manage.py migrate && python manage.py seed_parking_data && python manage.py collectstatic --noinput

## Start command

gunicorn parking_project.wsgi:application

## Environment variables

- SECRET_KEY=9)3n4t#0@z8%^%pos08q44!1lj)kf$zvxncr7euv8%8$ieisy*
- DEBUG=False
- ALLOWED_HOSTS=parking-backend-22m3.onrender.com
- CORS_ALLOWED_ORIGINS=https://parkingsystem-anosh.vercel.app
- DATABASE_URL=postgresql://parking_user:fyfFsGPswwQoIPPGMfEBT7K7jhHmWwwC@dpg-d9b74j0js32c73ar8vvg-a.singapore-postgres.render.com/parking_db_trcp
- SENDGRID_API_KEY=<your-sendgrid-api-key>
- DEFAULT_FROM_EMAIL=anoshsitu@gmail.com
- PARKING_DEVELOPER_EMAIL=anoshmishra09@gmail.com
- PARKING_RECEIPT_TIME_ZONE=Asia/Kolkata

The application now uses SendGrid's TLS SMTP relay at `smtp.sendgrid.net:587`.
Create an API key with Mail Send permission and set it as `SENDGRID_API_KEY`;
the SMTP username is automatically set to `apikey`. Before deploying, verify
the address in `DEFAULT_FROM_EMAIL` as a Single Sender or authenticate its
domain in SendGrid. Every new booking sends the owner a branded PDF receipt and
sends the developer a private BCC copy.

## Fix an already deployed empty database

If `/api/lots/` returns `[]`, run this in the Render shell:

```bash
python manage.py migrate
python manage.py seed_parking_data
```
