# api/core/response.py
import json
from typing import Any

from fastapi.responses import JSONResponse


class ApiJSONResponse(JSONResponse):
    """Custom JSON Response class that wraps responses in ApiResponse structure."""

    def render(self, content: Any) -> bytes:
        # If content is already wrapped (has data and error fields), return as is
        if isinstance(content, dict) and "data" in content and "error" in content:
            return json.dumps(content, ensure_ascii=False).encode("utf-8")

        # Otherwise, wrap in ApiResponse structure
        wrapped_content = {
            "data": content,
            "error": None
        }
        return json.dumps(wrapped_content, ensure_ascii=False).encode("utf-8")
