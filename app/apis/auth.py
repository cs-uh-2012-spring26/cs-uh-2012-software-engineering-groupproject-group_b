from http import HTTPStatus

from flask import request
from flask_jwt_extended import create_access_token
from flask_restx import Namespace, Resource, fields

from app.apis import MSG
from app.db.users import MEMBER_ROLE, TRAINER_ROLE, UserResource

VALID_ROLES = {MEMBER_ROLE, TRAINER_ROLE}

api = Namespace("auth", description="Endpoints for user registration and authentication")

# ---------------------------------------------------------------------------
# Swagger / Flask-RESTX models
# ---------------------------------------------------------------------------

_REGISTER_MODEL = api.model(
    "Register",
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
        "role": fields.String(
            required=True,
            example="member",
            enum=[MEMBER_ROLE, TRAINER_ROLE],
            description="Account type: 'member' or 'trainer'",
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
    "AuthErrorResponse",
    {MSG: fields.String(description="Error description")},
)

_REGISTER_OK_RESPONSE = api.model(
    "RegisterOK",
    {MSG: fields.String(example="Member registered with id: 664f1e...")},
)

# ---------------------------------------------------------------------------
# POST /users/register  — create a new member or trainer account
# ---------------------------------------------------------------------------

@api.route("/register")
class Register(Resource):
    @api.expect(_REGISTER_MODEL)
    @api.response(HTTPStatus.CREATED, "User registered successfully", _REGISTER_OK_RESPONSE)
    @api.response(HTTPStatus.BAD_REQUEST, "Missing or invalid fields", _ERROR_RESPONSE)
    @api.response(HTTPStatus.CONFLICT, "Email already registered", _ERROR_RESPONSE)
    def post(self):
        """Register a new member or trainer account.

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
        role = request.json.get("role", "").strip().lower()

        if not name or not email or not password:
            return (
                {MSG: "name, email, and password are all required"},
                HTTPStatus.BAD_REQUEST,
            )

        if role not in VALID_ROLES:
            return (
                {MSG: f"role must be one of: {', '.join(sorted(VALID_ROLES))}"},
                HTTPStatus.BAD_REQUEST,
            )

        user_resource = UserResource()
        user_id, error = user_resource.register_user(name, email, password, role)

        if error is not None:
            status = (
                HTTPStatus.CONFLICT
                if "already exists" in error
                else HTTPStatus.BAD_REQUEST
            )
            return {MSG: error}, status

        return {MSG: f"{role.capitalize()} registered with id: {user_id}"}, HTTPStatus.CREATED


# ---------------------------------------------------------------------------
# POST /users/login  — authenticate as a member or trainer
# ---------------------------------------------------------------------------


@api.route("/login")
class Login(Resource):
    @api.expect(_LOGIN_MODEL)
    @api.response(HTTPStatus.OK, "Login successful", _TOKEN_RESPONSE)
    @api.response(HTTPStatus.BAD_REQUEST, "Missing fields", _ERROR_RESPONSE)
    @api.response(HTTPStatus.UNAUTHORIZED, "Invalid credentials", _ERROR_RESPONSE)
    def post(self):
        """Log in as a member or trainer. Returns a JWT access token on success."""
        assert isinstance(request.json, dict)

        email = request.json.get("email", "").strip()
        password = request.json.get("password", "")
   

        if not email or not password:
            return {MSG: "email and password are required"}, HTTPStatus.BAD_REQUEST

       

        user_resource = UserResource()
        user, error = user_resource.authenticate_user(
            email, password
        )

        if error is not None:
            return {MSG: error}, HTTPStatus.UNAUTHORIZED


        token = create_access_token(
            identity=user["_id"],
            additional_claims={"role": user["role"]},
        )
        return {"access_token": token, MSG: "Login successful"}, HTTPStatus.OK
