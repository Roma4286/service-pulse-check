from pydantic import BaseModel, ValidationError
from werkzeug.datastructures import MultiDict

from app.web_app.api.services.schemas import ServiceCreateSchema, ServiceUpdateSchema


def parse_form(
    schema: type[BaseModel], form: MultiDict
) -> tuple[BaseModel | None, dict[str, str]]:
    data = {key: value for key, value in form.items() if value.strip()}
    data["is_active"] = "is_active" in form

    try:
        return schema.model_validate(data), {}
    except ValidationError as e:
        errors = {}
        for error in e.errors():
            field = str(error["loc"][0]) if error["loc"] else "__all__"
            errors.setdefault(field, error["msg"].removeprefix("Value error, "))
        return None, errors


def parse_service_create_form(
    form: MultiDict,
) -> tuple[ServiceCreateSchema | None, dict[str, str]]:
    return parse_form(ServiceCreateSchema, form)


def parse_service_update_form(
    form: MultiDict,
) -> tuple[ServiceUpdateSchema | None, dict[str, str]]:
    return parse_form(ServiceUpdateSchema, form)
