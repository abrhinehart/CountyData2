"""Pydantic schemas for the Our Projects module sketch."""

from pydantic import BaseModel


class ModuleFocus(BaseModel):
    label: str
    detail: str


class ModuleBootstrapPayload(BaseModel):
    module: str
    stage: str
    purpose: str
    focus_areas: list[ModuleFocus]
    primary_entities: list[str]
    suggested_views: list[str]
    open_questions: list[str]


class ModuleHealthPayload(BaseModel):
    module: str
    status: str
    stage: str
