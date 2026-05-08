![CI](https://github.com/cs-uh-2012-spring26/cs-uh-2012-software-engineering-groupproject-group_b/actions/workflows/CI.yaml/badge.svg)

# Fitness Management System API

A REST API for creating and managing fitness classes, users, and class bookings. Built with Flask-RESTX and MongoDB.

## Prerequisites

- Python 3.10 or higher
- MongoDB installed and running. Follow [https://www.mongodb.com/docs/manual/installation/](https://www.mongodb.com/docs/manual/installation/) to install MongoDB locally.
- Docker Desktop installed and running 

## Tech Stack

- [Flask-RESTX](https://flask-restx.readthedocs.io/en/latest/quickstart.html) — REST API framework with automatic [OpenAPI/Swagger](https://swagger.io/docs/specification/v3_0/about/) generation
- [PyMongo](https://pymongo.readthedocs.io/en/stable/) — MongoDB driver
- [Flask-JWT-Extended](https://flask-jwt-extended.readthedocs.io/) — JWT authentication
- [pytest](https://docs.pytest.org/en/stable/) for testing (see [Flask testing docs](https://flask.palletsprojects.com/en/stable/testing/))
- [mongomock](https://docs.mongoengine.org/guide/mongomock.html) — MongoDB mock for unit tests

## Running Locally

### 1. Start MongoDB

Make sure MongoDB is running before starting the server:

- **macOS:** `brew services restart mongodb-community`
- **Linux:** `sudo systemctl restart mongod`

### 2. Set up the `.env` file

Create a `.env` file in the project root with the following variables:

```env
MONGO_URI="mongodb://localhost:27017"
DB_NAME="eventsref_dev"
MOCK_DB="false"
DEBUG="true"
JWT_SECRET_KEY="change-me-to-a-long-random-secret"
AWS_ACCESS_KEY_ID="your-obtained-access-key"
AWS_SECRET_ACCESS_KEY="your-obtained-secret-key"
AWS_SES_REGION="eu-central-1"
SES_SENDER_EMAIL="your-sender-email"
TELEGRAM_BOT_TOKEN="your-telegram-bot-token"
```

> **Note:** Set `JWT_SECRET_KEY` to any long random string. Keep it secret — it signs all JWT tokens.

### 2.1 Amazon SES setup for reminder emails (Feature 5)

To run and test the reminder email feature, configure Amazon SES and IAM, then fill the SES-related values in `.env`.

1. Create an AWS account at [https://aws.amazon.com/ses/](https://aws.amazon.com/ses/).
2. In Amazon SES, verify all sender and receiver email addresses you plan to use for testing.
3. Because this project uses SES in **Sandbox mode** (and no domain is configured), **only verified email addresses can send or receive emails**.
4. Ensure the trainer user email and all member user emails used in tests are verified in SES.
5. Choose the sending email address from your verified identities and set it as `SES_SENDER_EMAIL` in `.env`.
6. Choose the SES region where your verified identity exists and set it as `AWS_SES_REGION` in `.env`.
7. Go to AWS IAM, create a new user with a meaningful name, and attach the `AmazonSESFullAccess` policy.
8. For that IAM user, open **Security credentials** and create an access key.
9. Copy those credentials into `.env` as `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`.

> **Reminder:** If emails fail in sandbox mode, the most common reason is that either the sender or one of the recipient addresses is not verified in SES.

### 2.2: Telegram Bot Setup for Telegram Reminder Notifications (Feature 7)

**Create the bot:**
1. Open Telegram, search for **@BotFather**, send `/newbot`, and follow the prompts.
2. Copy the token BotFather gives you and add it to `.env`:
   ```env
   TELEGRAM_BOT_TOKEN="your-token-here"
   ```

**Register the webhook (local dev only):**

Members link their Telegram account by clicking a deep link, which requires Telegram to push an update to your server. Locally this needs [ngrok](https://ngrok.com) to create a public tunnel:

```bash
# Terminal 1 — run the app
FLASK_APP=app flask run --debug --host=0.0.0.0 --port 8000

# Terminal 2 — expose it publicly
ngrok http 8000
```

Copy the `https://` URL ngrok gives you, then register it as the webhook (run once per ngrok session):

```bash
curl -X POST "https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://<your-ngrok-url>/users/telegram/webhook"}'
```

Expected response: `{"ok":true,"result":true}`.

**Link a member's Telegram account:**

1. Log in as a member → call `GET /users/me/telegram/link` in Swagger UI.
2. Open the returned link on your phone → tap **Start** in Telegram.
3. The server automatically saves your chat ID and enables Telegram notifications — no manual ID entry needed.

> **Note:** The deep link expires in 10 minutes. Call `GET /users/me/telegram/link` again to get a fresh one.

### 3. Create the virtual environment and install dependencies

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

### 4. Run the server

```sh
FLASK_APP=app flask run --debug --host=0.0.0.0 --port 8000
```

The server will be available at [http://127.0.0.1:8000](http://127.0.0.1:8000).

Use `ctrl-c` to stop the server.

### 5. Run the tests

```sh
pytest --cov=app tests/
```

---
## Running the Application with Docker 

### 1. Ensure Docker is installed and running 

- Install Docker Desktop [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- Open it and ensure it says "Docker is running" 

### 2. Set up the .env file 
Create a `.env` file in the project root. 

MONGO_URI=mongodb://mongo:27017
DB_NAME=eventsref_dev
MOCK_DB=false
DEBUG=true
JWT_SECRET_KEY=change-me-to-a-long-random-secret
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_SES_REGION=eu-central-1
SES_SENDER_EMAIL=your-email
TELEGRAM_BOT_TOKEN=your-token

### 3. Run the application 

docker compose up --build

### 4. Access the application 

Open your browser: 
[http://localhost:80](http://localhost:80) 

### 5. Stop the application

Press Ctrl + C in the terminal, then run: 

docker compose down 

---
## Using the Swagger UI

Once the server is running, open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser to access the interactive Swagger UI.

### Authenticating in Swagger

Most endpoints require a JWT token. Here's how to authenticate:

1. **Register an account** — use `POST /users/register` (member) or `POST /users/trainer/register` (trainer)
2. **Log in** — use `POST /users/login` (member) or `POST /users/trainer/login` (trainer)
3. **Copy the `access_token`** from the login response
4. **Click the "Authorize" button** at the top of the Swagger page
5. In the "Bearer" field, enter: `Bearer <your_token>` (include the word `Bearer` followed by a space, then the token)
6. Click **Authorize** then **Close** — all subsequent requests will include your token

---

## API Endpoints

### Users (`/users`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/users/register` | None | Register a new member account |
| POST | `/users/login` | None | Log in as a member, returns JWT |
| POST | `/users/trainer/register` | None | Register a new trainer account |
| POST | `/users/trainer/login` | None | Log in as a trainer, returns JWT |

**Password policy:** 10–128 characters, must include at least one uppercase letter, one lowercase letter, one digit, and one special character. No spaces allowed.

---

### Member (`/member`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/member` | None | View all upcoming fitness classes |
| POST | `/member/<class_id>/book` | Member JWT | Book a spot in a class |

---

### Admin (`/admin`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/admin/` | Trainer JWT | Create a new fitness class |
| GET | `/admin/<class_id>/members` | Trainer JWT | View all members booked in a class |
| POST | `/admin/<class_id>/remind` | Trainer JWT | Send reminder emails to all enrolled members in the class (only the assigned trainer can send) |

**Class fields when creating:**
- `class_name`, `class_description`, `trainer_name` — strings
- `class_date` — date in `YYYY-MM-DD` format (must be today or future)
- `class_start_time`, `class_end_time` — time in `HH:MM` format (24-hour)
- `class_room_number` — string
- `class_capacity` — integer

---

## Manually Managing the Virtual Environment

To activate:

```sh
source .venv/bin/activate
```

To deactivate:

```sh
deactivate
```

---
## Deployed URL for Swagger UI

http://167.99.253.69/

## Member Responsibilities 

** Mustafa
- Completed Feature 5 
- Completed documentation for feature 5
- Checked pull request from Maryam 

** Tinh 
- Completed tests for Feature 5
- Completed tests for Feature 1
- Checked pull request from Mustafa

** Uditi
- Completed tests for Feature 4
- Checked pull request from Tinh

** Raissa
- Completed tests for Feature 2
- Updated README to include member responsibilities
- Checked pull request from Uditi

** Maryam
- Completed tests for Feature 3
- Completed set up for Continuous Integration(CI)
- Checked pull request from Raissa



## Additional Docs

See [/docs/BestPractices.md](/docs/BestPractices.md) for branch naming conventions and other development tips.
