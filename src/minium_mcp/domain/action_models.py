"""动作与断言相关模型。"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class Locator(BaseModel):
    """结构化定位器。"""

    type: Literal["css", "text", "id"]
    value: str = Field(min_length=1)
    index: int = Field(default=0, ge=0)

    @field_validator("value")
    @classmethod
    def strip_value(cls, value: str) -> str:
        """去掉首尾空白。"""
        normalized = value.strip()
        if not normalized:
            raise ValueError("locator value cannot be empty")
        return normalized


class WaitCondition(BaseModel):
    """显式等待条件。"""

    kind: Literal["page_path_equals", "element_exists", "element_visible"]
    expected_value: str | None = None
    locator: Locator | None = None
    timeout_ms: int = Field(default=3000, ge=1, le=60000)

    @model_validator(mode="after")
    def validate_condition(self) -> "WaitCondition":
        """校验条件参数。"""
        if self.kind == "page_path_equals" and not self.expected_value:
            raise ValueError("page_path_equals requires expected_value")
        if self.kind in {"element_exists", "element_visible"} and self.locator is None:
            raise ValueError(f"{self.kind} requires locator")
        return self


class GestureTarget(BaseModel):
    """手势目标，支持定位器或绝对坐标。"""

    locator: Locator | None = None
    x: float | None = None
    y: float | None = None

    @model_validator(mode="after")
    def validate_target(self) -> "GestureTarget":
        has_locator = self.locator is not None
        has_coordinates = self.x is not None or self.y is not None

        if has_locator and has_coordinates:
            raise ValueError("gesture target must use either locator or coordinates")
        if not has_locator and (self.x is None or self.y is None):
            raise ValueError("gesture target requires locator or both x and y")
        return self
