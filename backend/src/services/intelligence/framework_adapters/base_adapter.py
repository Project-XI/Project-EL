from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class BaseAdapter(ABC):
    """
    Abstract contract for framework-specific static analysis logic.
    """
    @abstractmethod
    def extract_routes(self, repo_path: str, structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def detect_middleware(self, repo_path: str, structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def detect_auth_patterns(self, repo_path: str, structure: Dict[str, Any]) -> Dict[str, Any]:
        pass
