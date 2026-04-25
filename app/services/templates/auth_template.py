from abc import ABC, abstractmethod
from typing import Dict, Tuple, Optional


class RegistrationTemplate(ABC):
    """
    Template pattern for user registration

    This defines the skeleton algorithm for registration
    All validation and common logic are in this class 

    """

    def register(self, request_data: Dict) -> Tuple[bool, str, int, Optional[str]]:

        # extarct and clean input
        name, email, password, role = self.extract_input(request_data)

        # validate required fields
        error = self.validate_required(name, email, password, role)
        if error:
            return False, error, 400, None
        # validate role
        error = self.validate_role(role)
        if error:
            return False, error, 400, None
        # validate password
        error = self.validate_password(password)
        if error:
            return False, error, 400, None

        if self.email_exists(email):
            return False, "Email already registered", 409, None

        user_id = self.create_user(name, email, password, role)

        if not user_id:
            return False, "Registration failed", 500, None

        self.after_registration(user_id, name, email, role)

        return True, f"{role.capitalize()} registered successfully", 201, user_id

    # Common methods for any form of registration

    def extract_input(self, data: Dict) -> Tuple[str, str, str, str]:
        """ Extract and clean input data"""
        name = data.get("name", "").strip()
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")
        role = data.get("role", "").strip().lower()

        return name, email, password, role

    def validate_required(self, name: str, email: str, password: str, role: str) -> Optional[str]:
        """ Check if required fields are present"""

        if not name:
            return "name is required"
        if not email:
            return "email is required"
        if not password:
            return "password is required"
        if not role:
            return "role is required"
        return None

    def validate_role(self, role: str) -> Optional[str]:

        from app.db.users import MEMBER_ROLE, TRAINER_ROLE
        valid_roles = {MEMBER_ROLE, TRAINER_ROLE}

        if role not in valid_roles:
            return f"role must be one of: {', '.join(sorted(valid_roles))}"
        return None

    def email_exists(self, email: str) -> bool:
        """ Check if email is registered"""
        from app.db.users import UserResource
        user_resource = UserResource()
        existing = user_resource.get_user_by_email(email)
        return existing is not None

    @abstractmethod
    def validate_password(self, password: str) -> Optional[str]:
        pass

    @abstractmethod
    def create_user(self, name: str, email: str, passowrd: str, role: str) -> Optional[str]:
        pass

    def after_registration(self, user_id: str, name: str, email: str, role: str) -> None:
        pass
