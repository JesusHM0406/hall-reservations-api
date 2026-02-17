from typing import List, Dict, Any

from pydantic import BaseModel


class AvailableFilter(BaseModel):
  name: str
  label: str
  type: str
  options: List[Dict[str, Any]] | None = None
  current_value: Any = None

class FilterFactory:
  @staticmethod
  def select(name: str, label: str, options: Dict[str, str], current: Any = None):
    formatted_options = [{"label": v, "value": k} for k, v in options.items()]
    return AvailableFilter(
      name=name,
      label=label,
      type="select",
      options=formatted_options,
      current_value=current
    )

  @staticmethod
  def boolean(name: str, label: str, current: bool | None = None):
    """To generate filters like switch/checkbox"""
    return AvailableFilter(
      name=name,
      label=label,
      type="boolean",
      current_value=current
    )
