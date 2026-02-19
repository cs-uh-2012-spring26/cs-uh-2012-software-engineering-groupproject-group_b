from flask_restx import Namespace, Resource, fields
from app.apis import MSG
from app.db.classes import ClassResource
from app.db.users import UserResource

from http import HTTPStatus
from flask_jwt_extended import jwt_required, get_jwt

api = Namespace("classes", description="Endpoint for class member list")

# Model for a single booked member entry returned in the response
MEMBER_MODEL = api.model(
    "BookedMember",
    {
        "name": fields.String(description="Member's full name"),
        "email": fields.String(description="Member's email address"),
        "contact": fields.String(description="Member's contact number"),
    },
)


@api.route("/<class_id>/members")
@api.param("class_id", "The ID of the class")
class ClassMemberList(Resource):

    @jwt_required()
    @api.doc(security="Bearer")
    @api.marshal_list_with(MEMBER_MODEL)
    @api.response(HTTPStatus.OK, "List of booked members returned")
    @api.response(HTTPStatus.UNAUTHORIZED, "Missing or invalid JWT token", api.model("MembersUnauthorized", {MSG: fields.String()}))
    @api.response(HTTPStatus.FORBIDDEN, "Access restricted to trainers and admins", api.model("MembersForbidden", {MSG: fields.String()}))
    @api.response(HTTPStatus.NOT_FOUND, "Class not found", api.model("MembersNotFound", {MSG: fields.String()}))
    def get(self, class_id):
        """View the list of members who booked a spot in a class (trainer/admin only)"""

        # Check that the requester's role is trainer or admin (A2: Insufficient role)
        claims = get_jwt()
        role = claims.get("role", "")
        if role not in ("trainer", "admin"):
            return {MSG: "Access restricted to trainers and admins"}, HTTPStatus.FORBIDDEN

        # Look up the class by its ID (A3: Class not found)
        class_resource = ClassResource()
        fitness_class = class_resource.get_class_by_id(class_id, str)
        if fitness_class is None:
            return {MSG: "Class not found"}, HTTPStatus.NOT_FOUND

        # Get the list of ObjectIds of users who booked this class
        user_oids = fitness_class.get("user_ids", [])

        # A4: Class has no bookings — return empty list with 200 OK
        if not user_oids:
            return []

        # Fetch full details for each booked user
        user_resource = UserResource()
        members = user_resource.get_users_by_ids(user_oids)

        # Return only name, email, and contact for each member
        return [
            {
                "name": m.get("name", ""),
                "email": m.get("email", ""),
                "contact": m.get("contact", ""),
            }
            for m in members
        ]
