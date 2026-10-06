import re

import pytest

from app.models import ResultStatus
from tests.factories import create_check_result, create_service, create_user

HOME_URL = "/"


def get_html(response) -> str:
    return response.get_data(as_text=True)


def get_card_classes(html: str, service_id: int) -> list[str]:
    match = re.search(rf'<article class="([^"]*)"\s+id="service-{service_id}"', html)
    assert match, f"no card for service {service_id}"
    return match.group(1).split()


# auth


def test_home_without_login_redirects_to_login(client):
    response = client.get(HOME_URL)

    assert response.status_code == 302
    assert response.headers["Location"] == "/login"


def test_home_for_deleted_user_redirects_to_login(client, session, logged_in):
    session.delete(logged_in)
    session.commit()

    response = client.get(HOME_URL)

    assert response.status_code == 302
    assert response.headers["Location"] == "/login"


@pytest.mark.usefixtures("logged_in")
def test_home_is_not_stored_by_browser(client):
    response = client.get(HOME_URL)

    assert response.headers["Cache-Control"] == "no-store"


# content


def test_home_shows_only_own_services(client, session, logged_in):
    own_service = create_service(session, logged_in, name="own")
    foreign_service = create_service(session, create_user(session), name="foreign")

    html = get_html(client.get(HOME_URL))

    assert f'id="service-{own_service.id}"' in html
    assert f'id="service-{foreign_service.id}"' not in html


def test_home_shows_account_stats(client, session, logged_in):
    create_service(session, logged_in, is_active=True)
    create_service(session, logged_in, is_active=True)
    create_service(session, logged_in, is_active=False)

    html = get_html(client.get(HOME_URL))

    assert "3 services · 2 active" in " ".join(html.split())


@pytest.mark.usefixtures("logged_in")
def test_home_without_services_shows_only_new_service_tile(client):
    html = get_html(client.get(HOME_URL))

    assert "<article" not in html
    assert 'class="new-service-tile"' in html


def test_home_card_links_to_service_page(client, session, logged_in):
    service = create_service(session, logged_in)

    html = get_html(client.get(HOME_URL))

    link = re.search(r'<a class="service-card__link"\s+href="([^"]+)"', html)
    assert link.group(1) == f"/services/{service.id}"


@pytest.mark.parametrize(
    ("statuses", "expected_class"),
    [
        ([], None),
        ([ResultStatus.FAIL, ResultStatus.SUCCESS], "service-card--success"),
        ([ResultStatus.SUCCESS, ResultStatus.FAIL], "service-card--fail"),
    ],
    ids=["no-results", "last-success", "last-fail"],
)
def test_home_card_border_reflects_last_result(
    client, session, logged_in, statuses, expected_class
):
    service = create_service(session, logged_in)
    for status in statuses:
        create_check_result(session, service, status=status)

    classes = get_card_classes(get_html(client.get(HOME_URL)), service.id)

    status_classes = {"service-card--success", "service-card--fail"}
    assert set(classes) & status_classes == (
        {expected_class} if expected_class else set()
    )


def test_home_marks_inactive_service_card(client, session, logged_in):
    service = create_service(session, logged_in, is_active=False)

    classes = get_card_classes(get_html(client.get(HOME_URL)), service.id)

    assert "service-card--inactive" in classes
