from flask_restx import Namespace, Resource, fields
from app.apis import MSG
from app.db.bookings import BookingResource
from app.db.bookings import USER_NAME, USER_EMAIL, USER_CONTACT
from http import HTTPStatus

api = Namespace("classes", description="Endpoint for viewing class member lists")

# Example member used in Swagger docs
_EXAMPLE_MEMBER = {
    USER_NAME: "Jane Doe",
    USER_EMAIL: "jane.doe@example.com",
    USER_CONTACT: "+1-555-0100",
}

# Model representing a single booked member (name, email, contact per specs)
MEMBER_FIELDS = api.model(
    "ClassMember",
    {
        USER_NAME: fields.String(example=_EXAMPLE_MEMBER[USER_NAME]),
        USER_EMAIL: fields.String(example=_EXAMPLE_MEMBER[USER_EMAIL]),
        USER_CONTACT: fields.String(example=_EXAMPLE_MEMBER[USER_CONTACT]),
    },
)


@api.route("/<class_id>/members")
@api.param("class_id", "The ID of the class to look up")
class ClassMemberList(Resource):
    @api.response(
        HTTPStatus.OK,
        "Success",
        api.model(
            "Class Member List",
            {
                MSG: fields.List(
                    fields.Nested(MEMBER_FIELDS),
                    example=[_EXAMPLE_MEMBER],
                )
            },
        ),
    )
    @api.response(
        HTTPStatus.NOT_ACCEPTABLE,
        "Invalid Request",
        api.model(
            "Class Member List: Bad Request",
            {MSG: fields.String("Invalid class ID provided")},
        ),
    )
    def get(self, class_id):
        """View the list of members who booked a class (trainer/admin only)."""
        # class_id must be a non-blank string
        if not isinstance(class_id, str) or not class_id.strip():
            return {MSG: "Invalid class ID provided"}, HTTPStatus.NOT_ACCEPTABLE

        booking_resource = BookingResource()
        members = booking_resource.get_class_members(class_id)
        return {MSG: members}, HTTPStatus.OK
