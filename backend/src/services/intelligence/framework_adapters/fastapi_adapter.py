import ast
import os
from typing import List, Dict, Any, Optional
from .base_adapter import BaseAdapter

class FastAPIAdapter(BaseAdapter):
    """
    FastAPI-specific analyzer using AST for deterministic route and dependency extraction.
    """
    
    def extract_routes(self, repo_path: str, structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        routes = []
        for file_path in structure.get("file_tree", {}):
            if file_path.endswith(".py"):
                abs_path = os.path.join(repo_path, file_path)
                try:
                    with open(abs_path, 'r') as f:
                        tree = ast.parse(f.read())
                        for node in ast.walk(tree):
                            if isinstance(node, ast.FunctionDef):
                                for decorator in node.decorator_list:
                                    # Detect @app.get, @router.post, etc.
                                    if isinstance(decorator, ast.Call) and hasattr(decorator.func, 'attr'):
                                        if decorator.func.attr.lower() in ['get', 'post', 'put', 'delete', 'patch']:
                                            routes.append({
                                                "file": file_path,
                                                "method": decorator.func.attr.upper(),
                                                "function": node.name,
                                                "path": self._extract_arg(decorator.args[0]) if decorator.args else "unknown",
                                                "lineno": node.lineno
                                            })
                            
                            # Phase 2: Detect Hidden Router inclusions
                            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
                                call = node.value
                                if hasattr(call.func, 'attr') and call.func.attr == "include_router":
                                    routes.append({
                                        "file": file_path,
                                        "type": "ROUTER_INCLUSION",
                                        "evidence": "Found include_router call",
                                        "lineno": node.lineno
                                    })
                except:
                    pass
        return routes

    def detect_middleware(self, repo_path: str, structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        middleware = []
        for file_path in structure.get("file_tree", {}):
            if file_path.endswith(".py"):
                abs_path = os.path.join(repo_path, file_path)
                try:
                    with open(abs_path, 'r') as f:
                        content = f.read()
                        if "add_middleware" in content:
                            middleware.append({
                                "file": file_path,
                                "type": "Global Middleware",
                                "evidence": "Found add_middleware call"
                            })
                except:
                    pass
        return middleware

    def detect_auth_patterns(self, repo_path: str, structure: Dict[str, Any]) -> Dict[str, Any]:
        patterns = {"has_jwt": False, "protected_routes": []}
        for file_path in structure.get("file_tree", {}):
            if file_path.endswith(".py"):
                abs_path = os.path.join(repo_path, file_path)
                try:
                    with open(abs_path, 'r') as f:
                        content = f.read()
                        if "OAuth2PasswordBearer" in content or "pyjwt" in content.lower():
                            patterns["has_jwt"] = True
                except:
                    pass
        return patterns

    def _extract_arg(self, arg):
        if isinstance(arg, ast.Constant):
            return arg.value
        return "dynamic"
