from flask_jwt_extended import JWTManager, jwt_required
from flask_pydantic_spec import FlaskPydanticSpec

spec = FlaskPydanticSpec("flask", title="Service Pulse Check API", version="1.0.0")
jwt = JWTManager()


def protected(func):
    return jwt_required()(func)
