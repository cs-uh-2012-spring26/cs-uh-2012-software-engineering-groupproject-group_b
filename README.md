![CI](https://github.com/cs-uh-2012-spring26/cs-uh-2012-software-engineering-groupproject-group_b/actions/workflows/CI.yaml/badge.svg)

# Fitness Management System API

A REST API for creating and managing fitness classes, users, and class bookings. Built with Flask-RESTX and MongoDB.

## Prerequisites

- Python 3.10 or higher
- MongoDB installed and running. Follow [https://www.mongodb.com/docs/manual/installation/](https://www.mongodb.com/docs/manual/installation/) to install MongoDB locally.

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
JWT_SECRET_KEY="your-secret-key-here"
```

> **Note:** Set `JWT_SECRET_KEY` to any long random string. Keep it secret — it signs all JWT tokens.

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
