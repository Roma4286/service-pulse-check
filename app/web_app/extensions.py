from flask_jwt_extended import JWTManager, jwt_required
from flask_pydantic_spec import FlaskPydanticSpec
from inflection import camelize

spec = FlaskPydanticSpec("flask", title="Service Pulse Check API", version="1.0.0")
jwt = JWTManager()

_protected_operations: set[str] = set()


def protected(func):
    _protected_operations.add(camelize(func.__name__, False))
    return jwt_required()(func)


_generate_spec = spec._generate_spec


def _generate_spec_with_security():
    document = dict(_generate_spec())
    document["components"] = {
        **document.get("components", {}),
        "securitySchemes": {
            "csrfToken": {
                "type": "apiKey",
                "in": "header",
                "name": "X-CSRF-TOKEN",
                "description": "Value of the csrf_access_token cookie set by "
                "/api/auth/login. The access token itself is sent by the browser "
                "in an HttpOnly cookie.",
            },
        },
    }
    for operations in document["paths"].values():
        for operation in operations.values():
            if operation.get("operationId") in _protected_operations:
                operation["security"] = [{"csrfToken": []}]
    return document


spec._generate_spec = _generate_spec_with_security
