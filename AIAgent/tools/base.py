from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, fields, replace
from typing import Any
from anthropic.types.beta import BetaToolUnionParam

class BaseAnthropicTool(metaclass=ABCMeta):
    @abstractmethod
    def __call__(self, **kwargs) -> Any:
        pass

    @abstractmethod
    def to_params(self) -> BetaToolUnionParam:
        raise NotImplementedError

@dataclass(kw_only=True, frozen=True)
class ToolResult:
    output: str | None = None
    error: str | None = None
    base64_image: str | None = None
    system: str | None = None

    def __bool__(self):
        from dataclasses import fields
        return any(getattr(self, field.name) for field in fields(self))

    def __add__(self, other: "ToolResult"):
        def combine_fields(field: str | None, other_field: str | None, concatenate: bool = True):
            if field and other_field:
                if concatenate:
                    return field + other_field
                raise ValueError("Cannot combine tool results")
            return field or other_field

        return ToolResult(
            output=combine_fields(self.output, other.output),
            error=combine_fields(self.error, other.error),
            base64_image=combine_fields(self.base64_image, other.base64_image, False),
            system=combine_fields(self.system, other.system),
        )

    def replace(self, **kwargs):
        return replace(self, **kwargs)

class ToolFailure(ToolResult):
    pass

class ToolError(Exception):
    def __init__(self, message):
        self.message = message
