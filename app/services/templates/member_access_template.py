from abc import ABC, abstractmethod
from typing import List, Dict, Tuple, Optional


class MemberAccessTemplate(ABC):
    """ Template for access of enrolled members """

    def get_enrolled_members(self, class_id: str) -> Tuple[Optional[List[Dict]], Optional[str]]:

        # Find class
        fitness_class = self.find_class(class_id)
        if not fitness_class:
            return None, "Class not found"

        member_ids = self.extract_member_ids(fitness_class)
        if not member_ids:
            return [], None
        # Fetch members
        members = self.fetch_members(member_ids)
        return self.format_members(members), None

    def get_enrolled_members_with_class(self, class_id: str) -> Tuple[Optional[List[Dict]], Optional[Dict], Optional[str]]:

        # Find class
        fitness_class = self.find_class(class_id)
        if not fitness_class:
            return None, None, "Class not found"

        member_ids = self.extract_member_ids(fitness_class)
        if not member_ids:
            return [], fitness_class, None
        # Fetch members
        members = self.fetch_members(member_ids)
        # fprmat response
        return self.format_members(members), None

    @abstractmethod
    def find_class(self, class_id: str) -> Optional[Dict]:
        pass

    @abstractmethod
    def extract_member_ids(self, fitness_class: Dict) -> List:
        pass

    @abstractmethod
    def fetch_members(self, member_ids: List) -> List[Dict]:
        pass

    def format_members(self, members: List[Dict]) -> List[Dict]:
        return [
            {
                "name": m.get("name", ""),
                "email": m.get("email", ""),
                "contact": m.get("contact", ""),
            }
            for m in members
        ]
