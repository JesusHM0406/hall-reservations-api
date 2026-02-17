from typing import List, Dict, Any

from pydantic import BaseModel


class AvailableFilter(BaseModel):
  name: str
  label: str
  type: str
  options: List[Dict[str, Any]] | None = None
  current_value: Any = None
