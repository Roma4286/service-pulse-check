import re

import pytest

from app.models import CheckResult, Service, ServiceType
from tests.factories import create_check_result, create_service, create_user

HX_HEADERS = {"HX-Request": "true"}


def get_html(response) -> str:
    return response.get_data(as_text=True)


def get_text(response) -> str:
    return " ".join(get_html(response).split())


def get_stored_service(session, service_id: int) -> Service | None:
    session.expunge_all()
    return session.get(Service, service_id)


def get_field_errors(response) -> list[str]:
    return re.findall(
        r'<p class="(?:field|form)-error">([^<]*)</p>', get_html(response)
    )


def assert_toast(response, status_code: int, message: str):
    assert response.status_code == status_code
    assert response.headers["HX-Retarget"] == "#toasts"
    assert response.headers["HX-Reswap"] == "beforeend"
    assert '<div class="toast" role="alert"' in get_html(response)
    assert message in get_html(response)


# auth

PROTECTED_ENDPOINTS = [
    ("GET", "/services/1"),
    ("POST", "/services/1/active"),
    ("GET", "/services/1/update"),
    ("POST", "/services/1/update"),
    ("POST", "/services/1/delete"),
    ("GET", "/services/new"),
    ("GET", "/services/new-tile"),
    ("POST", "/services"),
]


@pytest.mark.parametrize(("method", "url"), PROTECTED_ENDPOINTS)
def test_endpoint_without_login_redirects_htmx_to_login(client, method, url):
    response = client.open(url, method=method, headers=HX_HEADERS)

    assert response.status_code == 401
    assert response.headers["HX-Redirect"] == "/login"


def test_page_without_login_redirects_to_login(client):
    response = client.get("/services/1")

    assert response.status_code == 302
    assert response.headers["Location"] == "/login"


@pytest.mark.parametrize(
    ("method", "url"),
    [(method, url) for method, url in PROTECTED_ENDPOINTS if method == "POST"],
)
@pytest.mark.usefixtures("logged_in")
def test_post_without_csrf_token_redirects_to_login(
    client, csrf_header_key, method, url
):
    del client.environ_base[csrf_header_key]

    response = client.open(url, method=method, headers=HX_HEADERS)

    assert response.status_code == 401
    assert response.headers["HX-Redirect"] == "/login"


# GET /services/<id>


def test_detail_without_results_shows_no_data(client, session, logged_in):
    service = create_service(session, logged_in)

    response = client.get(f"/services/{service.id}")

    assert "% uptime" not in get_text(response)


@pytest.mark.usefixtures("logged_in")
def test_detail_for_foreign_service_returns_404_page(client, session):
    foreign_service = create_service(session, create_user(session))

    response = client.get(f"/services/{foreign_service.id}")

    assert response.status_code == 404
    assert "<h1>404</h1>" in get_text(response)
    assert "Service not found" in get_text(response)


@pytest.mark.usefixtures("logged_in")
def test_detail_for_missing_service_returns_404_page(client):
    response = client.get("/services/999")

    assert response.status_code == 404
    assert "Service not found" in get_text(response)


# POST /services/<id>/active


def test_set_active_off_updates_service_and_returns_card_with_stats(
    client, session, scheduler, logged_in
):
    service = create_service(session, logged_in, is_active=True)
    create_service(session, logged_in, is_active=True)

    response = client.post(
        f"/services/{service.id}/active",
        data={"is_active": "false"},
        headers=HX_HEADERS,
    )

    html = get_html(response)
    assert response.status_code == 200
    assert "service-card--inactive" in html
    assert '{"is_active": "true"}' in html
    assert "2 services · 1 active" in get_text(response)
    assert get_stored_service(session, service.id).is_active is False
    scheduler.delete_task.assert_called_once_with(service.id)


def test_set_active_with_same_state_changes_nothing(
    client, session, scheduler, logged_in
):
    service = create_service(session, logged_in, is_active=False)

    response = client.post(
        f"/services/{service.id}/active", data={"is_active": "false"}
    )

    assert response.status_code == 200
    assert get_stored_service(session, service.id).is_active is False
    scheduler.create_task.assert_not_called()
    scheduler.delete_task.assert_not_called()


@pytest.mark.usefixtures("logged_in")
def test_set_active_for_foreign_service_returns_404_toast(client, session, scheduler):
    foreign_service = create_service(session, create_user(session), is_active=True)

    response = client.post(
        f"/services/{foreign_service.id}/active",
        data={"is_active": "false"},
        headers=HX_HEADERS,
    )

    assert_toast(response, 404, "Service not found")
    assert get_stored_service(session, foreign_service.id).is_active is True
    scheduler.delete_task.assert_not_called()


def test_set_active_when_scheduling_fails_returns_500_toast(
    client, session, scheduler, logged_in
):
    service = create_service(session, logged_in, is_active=True)
    scheduler.delete_task.side_effect = RuntimeError("redis is down")

    response = client.post(
        f"/services/{service.id}/active",
        data={"is_active": "false"},
        headers=HX_HEADERS,
    )

    assert_toast(response, 500, "Failed to schedule the service check.")
    assert get_stored_service(session, service.id).is_active is True


# GET /services/new, /services/new-tile


@pytest.mark.usefixtures("logged_in")
def test_new_form_returns_empty_form_with_defaults(client):
    response = client.get("/services/new")

    html = get_html(response)
    assert response.status_code == 200
    assert 'hx-post="/services"' in html
    assert 'name="interval_in_seconds" min="1" step="1" value="10"' in html
    assert 'name="timeout_in_seconds" min="0.1" step="0.1" value="5.0"' in html
    assert re.search(r'<input type="checkbox" name="is_active"\s+checked>', html)


@pytest.mark.usefixtures("logged_in")
def test_new_tile_returns_tile_that_opens_form(client):
    response = client.get("/services/new-tile")

    html = get_html(response)
    assert response.status_code == 200
    assert 'class="new-service-tile"' in html
    assert 'hx-get="/services/new"' in html


# POST /services


def service_form(**overrides) -> dict:
    form = {
        "name": "api",
        "type": "http",
        "url": "https://api.example.com",
        "interval_in_seconds": "30",
        "timeout_in_seconds": "2.5",
        "is_active": "on",
    }
    form.update(overrides)
    return {key: value for key, value in form.items() if value is not None}


def get_only_service(session) -> Service:
    session.expunge_all()
    return session.query(Service).one()


def test_create_saves_service_and_returns_card_tile_and_stats(
    client, session, scheduler, logged_in
):
    response = client.post("/services", data=service_form())

    service = get_only_service(session)
    assert (
        service.name,
        service.type,
        service.url,
        service.interval_in_seconds,
        service.timeout_in_seconds,
        service.is_active,
        service.user_id,
    ) == (
        "api",
        ServiceType.HTTP,
        "https://api.example.com/",
        30,
        2.5,
        True,
        logged_in.id,
    )
    scheduler.create_task.assert_called_once()

    html = get_html(response)
    assert response.status_code == 200
    assert (
        html.index(f'id="service-{service.id}"')
        < html.index("new-service-tile")
        < html.index('id="account-stats" hx-swap-oob="true"')
    )
    assert "1 services · 1 active" in get_text(response)


@pytest.mark.usefixtures("logged_in")
def test_create_with_unchecked_active_creates_paused_service(
    client, session, scheduler
):
    client.post("/services", data=service_form(is_active=None))

    assert get_only_service(session).is_active is False
    scheduler.create_task.assert_not_called()


@pytest.mark.usefixtures("logged_in")
def test_create_with_empty_interval_and_timeout_uses_defaults(client, session):
    client.post(
        "/services", data=service_form(interval_in_seconds="", timeout_in_seconds="")
    )

    service = get_only_service(session)
    assert (service.interval_in_seconds, service.timeout_in_seconds) == (10, 5.0)


@pytest.mark.usefixtures("logged_in")
def test_create_tcp_service_with_host_and_port(client, session):
    client.post("/services", data=service_form(type="tcp", url="db.example.com:5432"))

    service = get_only_service(session)
    assert (service.type, service.url) == (ServiceType.TCP, "db.example.com:5432")


@pytest.mark.parametrize(
    ("overrides", "field_error"),
    [
        ({"name": ""}, "Field required"),
        ({"url": "not-a-url"}, "Input should be a valid URL"),
        ({"type": "tcp", "url": "db.example.com"}, "TCP address must be host:port"),
        ({"interval_in_seconds": "0"}, "greater than 0"),
        ({"timeout_in_seconds": "abc"}, "valid number"),
    ],
    ids=["no-name", "bad-url", "tcp-without-port", "zero-interval", "text-timeout"],
)
@pytest.mark.usefixtures("logged_in")
def test_create_with_invalid_form_returns_form_with_errors(
    client, session, scheduler, overrides, field_error
):
    response = client.post("/services", data=service_form(**overrides))

    assert response.status_code == 200
    assert any(field_error in error for error in get_field_errors(response))
    assert session.query(Service).count() == 0
    scheduler.create_task.assert_not_called()


@pytest.mark.usefixtures("logged_in")
def test_create_with_timeout_above_interval_shows_form_error(client, session):
    response = client.post(
        "/services", data=service_form(interval_in_seconds="5", timeout_in_seconds="10")
    )

    assert get_field_errors(response) == [
        "timeout_in_seconds must not be greater than interval_in_seconds"
    ]
    assert session.query(Service).count() == 0


@pytest.mark.usefixtures("logged_in")
def test_create_when_scheduling_fails_shows_form_error(client, session, scheduler):
    scheduler.create_task.side_effect = RuntimeError("redis is down")

    response = client.post("/services", data=service_form())

    assert response.status_code == 200
    assert get_field_errors(response) == ["Failed to schedule the service check."]
    assert session.query(Service).count() == 0


# GET /services/<id>/update


def test_update_form_is_filled_with_current_values(client, session, logged_in):
    service = create_service(
        session,
        logged_in,
        name="api",
        interval_in_seconds=60,
        timeout_in_seconds=5.0,
        is_active=False,
    )

    response = client.get(f"/services/{service.id}/update")

    html = get_html(response)
    assert response.status_code == 200
    assert 'class="modal"' in html
    assert f'hx-post="/services/{service.id}/update"' in html
    assert 'name="name" value="api"' in html
    assert 'name="interval_in_seconds" min="1" step="1" value="60"' in html
    assert 'name="timeout_in_seconds" min="0.1" step="0.1" value="5.0"' in html
    assert not re.search(r'name="is_active"\s+checked', html)


@pytest.mark.usefixtures("logged_in")
def test_update_form_for_foreign_service_returns_404_toast(client, session):
    foreign_service = create_service(session, create_user(session))

    response = client.get(f"/services/{foreign_service.id}/update", headers=HX_HEADERS)

    assert_toast(response, 404, "Service not found")


# POST /services/<id>/update


def update_form(**overrides) -> dict:
    form = {
        "name": "renamed",
        "interval_in_seconds": "30",
        "timeout_in_seconds": "2.5",
        "is_active": "on",
    }
    form.update(overrides)
    return {key: value for key, value in form.items() if value is not None}


def test_update_updates_service_and_returns_page_card_out_of_band(
    client, session, logged_in
):
    service = create_service(
        session, logged_in, name="api", interval_in_seconds=60, timeout_in_seconds=5.0
    )

    response = client.post(f"/services/{service.id}/update", data=update_form())

    stored_service = get_stored_service(session, service.id)
    assert (
        stored_service.name,
        stored_service.interval_in_seconds,
        stored_service.timeout_in_seconds,
    ) == ("renamed", 30, 2.5)

    html = get_html(response).strip()
    assert response.status_code == 200
    assert "renamed" in html


def test_update_with_unchecked_active_pauses_service(
    client, session, scheduler, logged_in
):
    service = create_service(session, logged_in, is_active=True)

    client.post(f"/services/{service.id}/update", data=update_form(is_active=None))

    assert get_stored_service(session, service.id).is_active is False
    scheduler.delete_task.assert_called_once_with(service.id)


def test_update_with_timeout_above_interval_shows_error_under_timeout(
    client, session, logged_in
):
    service = create_service(
        session, logged_in, interval_in_seconds=60, timeout_in_seconds=5.0
    )

    response = client.post(
        f"/services/{service.id}/update",
        data=update_form(interval_in_seconds="10", timeout_in_seconds="20"),
    )

    html = get_html(response)
    assert response.status_code == 200
    assert 'class="modal"' in html
    assert get_field_errors(response) == [
        "timeout_in_seconds must not be greater than interval_in_seconds."
    ]
    assert html.index('name="timeout_in_seconds"') < html.index("field-error")
    assert get_stored_service(session, service.id).interval_in_seconds == 60


def test_update_with_invalid_interval_shows_field_error(client, session, logged_in):
    service = create_service(session, logged_in, interval_in_seconds=60)

    response = client.post(
        f"/services/{service.id}/update", data=update_form(interval_in_seconds="0")
    )

    assert any("greater than 0" in error for error in get_field_errors(response))
    assert 'value="0"' in get_html(response)
    assert get_stored_service(session, service.id).interval_in_seconds == 60


@pytest.mark.usefixtures("logged_in")
def test_update_for_foreign_service_returns_404_toast(client, session):
    foreign_service = create_service(session, create_user(session), name="foreign")

    response = client.post(
        f"/services/{foreign_service.id}/update", data=update_form(), headers=HX_HEADERS
    )

    assert_toast(response, 404, "Service not found")
    assert get_stored_service(session, foreign_service.id).name == "foreign"


# POST /services/<id>/delete


def test_delete_removes_service_and_redirects_home(
    client, session, scheduler, logged_in
):
    service = create_service(session, logged_in)
    create_check_result(session, service)

    response = client.post(f"/services/{service.id}/delete", headers=HX_HEADERS)

    assert response.status_code == 200
    assert response.headers["HX-Redirect"] == "/"
    assert get_stored_service(session, service.id) is None
    assert session.query(CheckResult).count() == 0
    scheduler.delete_task.assert_called_once_with(service.id)


@pytest.mark.usefixtures("logged_in")
def test_delete_for_foreign_service_returns_404_toast(client, session, scheduler):
    foreign_service = create_service(session, create_user(session))

    response = client.post(f"/services/{foreign_service.id}/delete", headers=HX_HEADERS)

    assert_toast(response, 404, "Service not found")
    assert get_stored_service(session, foreign_service.id) is not None
    scheduler.delete_task.assert_not_called()


def test_delete_when_scheduling_fails_returns_500_toast_and_keeps_service(
    client, session, scheduler, logged_in
):
    service_id = create_service(session, logged_in).id
    scheduler.delete_task.side_effect = RuntimeError("redis is down")

    response = client.post(f"/services/{service_id}/delete", headers=HX_HEADERS)

    assert_toast(response, 500, "Failed to schedule the service check.")
    assert get_stored_service(session, service_id) is not None
