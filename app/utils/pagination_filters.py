from enum import Enum
from typing import List, Dict

from pydantic import BaseModel

class FilterTypeEnum(Enum):
  SELECT = 'select'
  TEXT = 'text'

class AvailableFilter(BaseModel):
  name: str
  label: str
  type: FilterTypeEnum
  options: List[Dict[str, str]] | None = None
  current_value: str | int | None = None

class FilterFactory:
  @staticmethod
  def select(
    *,
    name: str,
    label: str,
    options: Dict[str, str],
    current: str | int | None = None
  ):
    formatted_options = [{"label": v, "value": k} for k, v in options.items()]
    return AvailableFilter(
      name=name,
      label=label,
      type=FilterTypeEnum.SELECT,
      options=formatted_options,
      current_value=current
    )

  @staticmethod
  def text(
    *,
    name: str,
    label: str
  ):
    return AvailableFilter(
      name=name,
      label=label,
      type=FilterTypeEnum.TEXT
    )
