from datetime import date
from typing import Annotated, Any, Optional
from fastapi import Path as PathParam
from pydantic import (
    AnyUrl,
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    RootModel,
    ValidationError,
    field_validator,
)
from pydantic.alias_generators import to_camel
from .defaults import DEFAULT_PREFIX_MAP


SLUG_PATTERN = r"^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$"
Slug = Annotated[str, PathParam(pattern=SLUG_PATTERN)]


class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )


class Query_Templates(CamelModel):
    subject_completion: Optional[str] = None
    predicate_completion_context_sensitive: Optional[str] = None
    predicate_completion_context_insensitive: Optional[str] = None
    object_completion_context_sensitive: Optional[str] = None
    object_completion_context_insensitive: Optional[str] = None
    values_completion_context_sensitive: Optional[str] = None
    values_completion_context_insensitive: Optional[str] = None
    hover: Optional[str] = None


class SparqlEndpointConfiguration(CamelModel):
    name: str
    url: HttpUrl
    engine: Optional[str] = None
    default: bool = False
    sort_key: Optional[str] = None
    prefix_map: dict[str, AnyUrl] = Field(default_factory=dict)
    map_view_url: Optional[str] = None
    query_templates: Optional[Query_Templates] = None

    @field_validator("prefix_map", mode="before")
    @classmethod
    def _merge_prefix_defaults(cls, v: Any) -> dict[str, Any]:
        configured = dict(v or {})
        used_uris = {str(uri) for uri in configured.values()}
        merged = dict(configured)
        for prefix, uri in DEFAULT_PREFIX_MAP.items():
            if prefix in merged or str(uri) in used_uris:
                continue
            merged[prefix] = uri
            used_uris.add(str(uri))
        return merged


class AppConfig(RootModel[dict[str, SparqlEndpointConfiguration]]):
    pass


def validate_config(data: dict[str, Any]) -> dict[str, Any]:
    """Validate and return the normalized dict. Raises ValueError on failure."""
    try:
        config = AppConfig.model_validate(data)
        return config.model_dump(mode="json", exclude_none=True)
    except ValidationError as exc:
        raise ValueError(f"Schema validation failed:\n{exc}") from exc


class SparqlEndpointPatch(CamelModel):
    name: Optional[str] = None
    url: Optional[HttpUrl] = None
    engine: Optional[str] = None
    default: Optional[bool] = None
    sort_key: Optional[str] = None
    prefix_map: Optional[dict[str, AnyUrl]] = None
    map_view_url: Optional[str] = None
    query_templates: Optional[Query_Templates] = None


class ExampleQuery(BaseModel):
    name: str
    query: str


class SharedQuery(CamelModel):
    id: str
    query: str
    creation_date: date
