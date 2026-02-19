from http import HTTPStatus

from flask import request
from flask_jwt_extended import create_access_token, jwt_required
from flask_restx import Namespace, Resource, fields

from app.apis import MSG
from app.db.users import MEMBER_ROLE, TRAINER_ROLE, UserResource

api = Namespace("users", description="Endpoints for user registration and authentication")

# ---------------------------------------------------------------------------
# Swagger / Flask-RESTX models
# ---------------------------------------------------------------------------

_REGISTER_MODEL = api.model(
    "MemberRegister",
    {
        "name": fields.String(required=True, example="Jane Doe"),
        "email": fields.String(required=True, example="jane.doe@example.com"),
        "password": fields.String(
            required=True,
            example="Secur3P@ssword",
            description=(
                "Must be 10-128 characters and contain at least: "
                "one uppercase letter, one lowercase letter, "
                "one digit, and one special character. No spaces allowed."
            ),
        ),
    },
)

_LOGIN_MODEL = api.model(
    "Login",
    {
        "email": fields.String(required=True, example="jane.doe@example.com"),
        "password": fields.String(required=True, example="Secur3P@ssword"),
    },
)

_TOKEN_RESPONSE = api.model(
    "TokenResponse",
    {
        "access_token": fields.String(description="JWT bearer token"),
        MSG: fields.String(description="Status message"),
    },
)

_ERROR_RESPONSE = api.model(
    "ErrorResponse",
    {MSG: fields.String(description="Error description")},
)

# ---------------------------------------------------------------------------
# POST /users/register  — create a new member account
# ---------------------------------------------------------------------------


@api.route("/register")
class MemberRegister(Resource):
    @api.expect(_REGISTER_MODEL)
    @api.response(
        HTTPStatus.CREATED,
        "Member registered successfully",
        api.model("RegisterOK", {MSG: fields.String()}),
    )
    @api.response(HTTPStatus.BAD_REQUEST, "Missing or invalid fields", _ERROR_RESPONSE)
    @api.response(HTTPStatus.CONFLICT, "Email already registered", _ERROR_RESPONSE)
    def post(self):
        """Register a new member account.

        Password policy:
        - 10 to 128 characters long
        - At least one uppercase letter (A-Z)
        - At least one lowercase letter (a-z)
        - At least one digit (0-9)
        - At least one special character (!@#$%^&*()-_=+[]{}|;:,.<>?/\\)
        - No spaces or whitespace
        """
        assert isinstance(request.json, dict)

        name = request.json.get("name", "").strip()
        email = request.json.get("email", "").strip()
        password = request.json.get("password", "")

        if not name or not email or not password:
            return (
                {MSG: "name, email, and password are all required"},
                HTTPStatus.BAD_REQUEST,
            )

        user_resource = UserResource()
        user_id, error = user_resource.register_member(name, email, password)

        if error is not None:
            status = (
                HTTPStatus.CONFLICT
                if "already exists" in error
                else HTTPStatus.BAD_REQUEST
            )
            return {MSG: error}, status

        return {MSG: f"Member registered with id: {user_id}"}, HTTPStatus.CREATED


# ---------------------------------------------------------------------------
# POST /users/login  — authenticate as a member
# ---------------------------------------------------------------------------


@api.route("/login")
class MemberLogin(Resource):
    @api.expect(_LOGIN_MODEL)
    @api.response(HTTPStatus.OK, "Login successful", _TOKEN_RESPONSE)
    @api.response(
        HTTPStatus.BAD_REQUEST, "Missing fields", _ERROR_RESPONSE
    )
    @api.response(
        HTTPStatus.UNAUTHORIZED, "Invalid credentials", _ERROR_RESPONSE
    )
    def post(self):
        """Log in as a member. Returns a JWT access token on success."""
        assert isinstance(request.json, dict)

        email = request.json.get("email", "").strip()
        password = request.json.get("password", "")

        if not email or not password:
            return {MSG: "email and password are required"}, HTTPStatus.BAD_REQUEST

        user_resource = UserResource()
        user, error = user_resource.authenticate_user(
            email, password, required_role=MEMBER_ROLE
        )

        if error is not None:
            return {MSG: error}, HTTPStatus.UNAUTHORIZED

        token = create_access_token(
            identity=user["_id"],
            additional_claims={"role": MEMBER_ROLE},
        )
        return {"access_token": token, MSG: "Login successful"}, HTTPStatus.OK


# ---------------------------------------------------------------------------
# POST /users/trainer/register  — create a new trainer account (trainer only)
# ---------------------------------------------------------------------------


@api.route("/trainer/register")
class TrainerRegister(Resource):
    @api.expect(_REGISTER_MODEL)
    @api.response(
        HTTPStatus.CREATED,
        "Trainer registered successfully",
        api.model("TrainerRegisterOK", {MSG: fields.String()}),
    )
    @api.response(HTTPStatus.BAD_REQUEST, "Missing or invalid fields", _ERROR_RESPONSE)
    @api.response(HTTPStatus.CONFLICT, "Email already registered", _ERROR_RESPONSE)
    def post(self):
        """Register a new trainer account."""
        assert isinstance(request.json, dict)

        name = request.json.get("name", "").strip()
        email = request.json.get("email", "").strip()
        password = request.json.get("password", "")

        if not name or not email or not password:
            return (
                {MSG: "name, email, and password are all required"},
                HTTPStatus.BAD_REQUEST,
            )

        user_resource = UserResource()
        user_id, error = user_resource.register_trainer(name, email, password)

        if error is not None:
            status = (
                HTTPStatus.CONFLICT
                if "already exists" in error
                else HTTPStatus.BAD_REQUEST
            )
            return {MSG: error}, status

        return {MSG: f"Trainer registered with id: {user_id}"}, HTTPStatus.CREATED


# ---------------------------------------------------------------------------
# POST /users/trainer/login  — authenticate as a trainer / admin
# ---------------------------------------------------------------------------


@api.route("/trainer/login")
class TrainerLogin(Resource):
    @api.expect(_LOGIN_MODEL)
    @api.response(HTTPStatus.OK, "Login successful", _TOKEN_RESPONSE)
    @api.response(
        HTTPStatus.BAD_REQUEST, "Missing fields", _ERROR_RESPONSE
    )
    @api.response(
        HTTPStatus.UNAUTHORIZED, "Invalid credentials", _ERROR_RESPONSE
    )
    def post(self):
        """Log in as a trainer / admin. Returns a JWT access token on success."""
        assert isinstance(request.json, dict)

        email = request.json.get("email", "").strip()
        password = request.json.get("password", "")

        if not email or not password:
            return {MSG: "email and password are required"}, HTTPStatus.BAD_REQUEST

        user_resource = UserResource()
        user, error = user_resource.authenticate_user(
            email, password, required_role=TRAINER_ROLE
        )

        if error is not None:
            return {MSG: error}, HTTPStatus.UNAUTHORIZED

        token = create_access_token(
            identity=user["_id"],
            additional_claims={"role": TRAINER_ROLE},
        )
        return {"access_token": token, MSG: "Login successful"}, HTTPStatus.OK
