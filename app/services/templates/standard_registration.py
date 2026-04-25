from app.services.templates.auth_template import RegistrationTemplate
from app.db.users import UserResource
from typing import Optional
import re


class Registration(RegistrationTemplate):

    """Register a new member or trainer account.

        Password policy:
        - 10 to 128 characters long
        - At least one uppercase letter (A-Z)
        - At least one lowercase letter (a-z)
        - At least one digit (0-9)
        - At least one special character (!@#$%^&*()-_=+[]{}|;:,.<>?/\\)
        - No spaces or whitespace
        """

    def validate_password(self, password: str) -> Optional[str]:
        """ Standard password validation"""
        if len(password) < 10:
            return "Password must be atleast 10 characters long"
        if len(password) > 128:
            return "Password must be atmost 128 characters long"
        if " " in password:
            return "Password can't contain spaces"
        if not re.search(r'[a-z]', password):
            return "Password must contain atleast one lowercase letter"
        if not re.search(r'[A-Z]', password):
            return "Password must contain atleast one uppercase letter"
        if not re.search(r'\d', password):
            return "Password must contain atleast one digit"
        if not re.search(r'[!@#$%^&*()\-_=+\[\]{}|;:,.<>?/\\]', password):
            return "Password must contain atleast one special character"
        return None

    def create_user(self, name: str, email: str, password: str, role: str) -> Optional[str]:

        user_resource = UserResource()
        user_id, error = user_resource.register_user(
            name, email, password, role)
        return user_id if not error else None

    def after_registration(self, user_id: str, name: str, email: str, role: str) -> None:
        pass
