from flask import redirect, render_template, request, url_for

NOT_FOUND_MESSAGE = "Service not found. It may have been deleted."
UNEXPECTED_ERROR_MESSAGE = "Something went wrong. Please try again."
UNAVAILABLE_MESSAGE = (
    "The service is temporarily unavailable. Please try again in a minute."
)


def is_htmx_request() -> bool:
    return request.headers.get("HX-Request") == "true"


def htmx_redirect(url: str, status_code: int = 200):
    return "", status_code, {"HX-Redirect": url}


def error_response(message: str, status_code: int):
    if is_htmx_request():
        headers = {"HX-Retarget": "#toasts", "HX-Reswap": "beforeend"}
        return render_template("_toast.html", message=message), status_code, headers
    return (
        render_template("error.html", message=message, status_code=status_code),
        status_code,
    )


def unauthorized():
    login_url = url_for("web.auth.login")
    if is_htmx_request():
        return htmx_redirect(login_url, 401)
    return redirect(login_url)


def not_found(message: str = NOT_FOUND_MESSAGE):
    return error_response(message, 404)


def internal_error(message: str = UNEXPECTED_ERROR_MESSAGE):
    return error_response(message, 500)


def service_unavailable(message: str = UNAVAILABLE_MESSAGE):
    return error_response(message, 503)
