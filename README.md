# Library Service

Online management system for book borrowings.

## Features

* JWT authenticated.
* Admin panel /admin/
* Documentation at /api/doc/swagger/
* Books inventory management.
* Books borrowing management.
* Notifications service through Telegram API (bot and chat).
* Scheduled notifications with Django Q and Redis.
* Payments handle with Stripe API.

## Getting access

* create user via /api/users/
* get access token via /api/users/token/

## How to run

Install PostgreSQL and create database.

1. Clone project and create virtual environment

```shell
git clone https://github.com/yuliia-stopkyna/library-service.git
cd library-service
python -m venv venv
source venv/bin/activate # on MacOS
venv\Scripts\activate # on Windows
pip install -r requirements.txt
```
2. Set environment variables

On Windows use ```export``` command instead of ```set```
```shell
set POSTGRES_HOST=<your db host>
set POSTGRES_DB=<your db name>
set POSTGRES_USER=<your db user>
set POSTGRES_PASSWORD=<your db password>
set SECRET_KEY=<your Django secret key>
set TELEGRAM_BOT_TOKEN=<your Telegram Bot token>
set TELEGRAM_CHAT_ID=<your Telegram chat id>
set STRIPE_API_KEY=<your Stripe API key>
```
3. Make migrations and run server

```shell
python manage.py migrate
python manage.py runserver
```

4. Getting daily scheduled notifications in Telegram

* start Redis server
* run `python manage.py qcluster`
* run in separate terminal `python manage.py shell`
to open interactive console
* to activate scheduled task write in opened console 
`from borrowing import tasks` 
* the task will be first processed in a minute after activating 
and will be scheduled for the same time the next day
