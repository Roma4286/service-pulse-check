from flask_jwt_extended import JWTManager, jwt_required
from flask_pydantic_spec import FlaskPydanticSpec
from inflection import camelize

spec = FlaskPydanticSpec("flask", title="Service Pulse Check API", version="1.0.0")
jwt = JWTManager()

# flask_pydantic_spec has no support for security schemes, so they are injected into the
# generated document. _protected_operations holds operationIds, the only link back to the view.
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
            "bearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"},
        },
    }
    for operations in document["paths"].values():
        for operation in operations.values():
            if operation["operationId"] in _protected_operations:
                operation["security"] = [{"bearerAuth": []}]
    return document


spec._generate_spec = _generate_spec_with_security
