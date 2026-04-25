from abc import ABC, abstractmethod
from typing import List, Dict, Tuple, Optional


class MemberTemplate(ABC):
    """ Template for accessonh enorlled members """

    def get_enrolled_members(self, class_id: str) -> Tuple[Optional[List[Dict]], Optional[str]]:

        # Find class
        fitness_class = self._find_class(class_id)
        if not fitness_class:
            return None, "Class not found"

        member_ids = self._extract_member_ids(fitness_class)
        if not member_ids:
            return [], None
        # Fetch members
        members = self._fetch_members(member_ids)
        return self._format_members(members), None

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
