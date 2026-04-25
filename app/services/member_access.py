from app.services.member_template import MemberTemplate
from app.db.classes import ClassResource
from app.db.users import UserResource
from typing import List, Dict, Tuple, Optional


class MemberAccess(MemberTemplate):
    def find_class(self, class_id: str) -> Optional[Dict]:
        class_resource = ClassResource()
        return class_resource.get_class_by_id(class_id)

    def extract_member_ids(self, fitness_class: Dict) -> List:
        return fitness_class.get("user_ids", [])

    def fetch_members(self, member_ids: List) -> List[Dict]:
        user_resource = UserResource()
        return user_resource.get_users_by_ids(member_ids)
