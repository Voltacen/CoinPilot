### Additional README updates

- Added Flask-Migrate and manage.py for migrations (example: `python manage.py db init` then `python manage.py db migrate` then `python manage.py db upgrade`).
- Docker Compose file provided for running web, redis, postgres, and a celery worker.
- Claim endpoint: POST /claim {"address":"0x..."} will let logged-in users claim off-chain credits sent to an external address into their account (still non-withdrawable).
- Attach address: POST /profile/attach_address {"address":"0x..."} lets a user associate an external address with their account so they can later claim credits.
- Email notifications: Celery task will attempt to send emails when credits are applied; configure MAIL_SERVER and credentials in environment.

Run with Docker Compose (quick):
  docker-compose up --build

Then seed admin in the running container or locally:
  python seed_admin.py

