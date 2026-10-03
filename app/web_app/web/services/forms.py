from pydantic import ValidationError
from werkzeug.datastructures import MultiDict

from app.web_app.api.services.schemas import ServiceCreateSchema


def parse_service_create_form(
    form: MultiDict,
) -> tuple[ServiceCreateSchema | None, dict[str, str]]:
    data = {key: value for key, value in form.items() if value.strip()}
    data["is_active"] = "is_active" in form

    try:
        return ServiceCreateSchema.model_validate(data), {}
    except ValidationError as e:
        errors = {}
        for error in e.errors():
            field = str(error["loc"][0]) if error["loc"] else "__all__"
            errors.setdefault(field, error["msg"].removeprefix("Value error, "))
        return None, errors
