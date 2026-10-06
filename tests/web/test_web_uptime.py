import pytest

from app.models import CheckResult, ResultStatus
from app.web_app.web.services.uptime import build_uptime

SUCCESS = ResultStatus.SUCCESS
FAIL = ResultStatus.FAIL


def make_results(*statuses: ResultStatus) -> list[CheckResult]:
    return [
        CheckResult(service_id=1, status=status, response_time=0.1)
        for status in statuses
    ]


def test_build_uptime_without_results_shows_only_empty_slots():
    uptime = build_uptime([], slots=100)

    assert uptime.slots == 100
    assert uptime.results == []
    assert uptime.empty_slots == 100
    assert uptime.percent is None
    assert uptime.last_status is None


def test_build_uptime_orders_results_oldest_first():
    newest_first = make_results(SUCCESS, FAIL, SUCCESS)

    uptime = build_uptime(newest_first, slots=100)

    assert uptime.results == newest_first[::-1]


def test_build_uptime_takes_last_status_from_newest_result():
    uptime = build_uptime(make_results(FAIL, SUCCESS, SUCCESS), slots=100)

    assert uptime.last_status == FAIL


def test_build_uptime_fills_missing_slots_with_empty_ones():
    uptime = build_uptime(make_results(SUCCESS, SUCCESS, FAIL), slots=10)

    assert uptime.slots == 10
    assert uptime.empty_slots == 7


def test_build_uptime_has_no_empty_slots_when_results_exceed_slots():
    uptime = build_uptime(make_results(*[SUCCESS] * 5), slots=3)

    assert uptime.empty_slots == 0


@pytest.mark.parametrize(
    ("statuses", "percent"),
    [
        ([SUCCESS, SUCCESS], "100"),
        ([FAIL, FAIL], "0"),
        ([SUCCESS, FAIL, SUCCESS, SUCCESS], "75"),
        ([SUCCESS, SUCCESS, FAIL], "66.7"),
    ],
    ids=["all-success", "all-fail", "three-of-four", "two-of-three"],
)
def test_build_uptime_computes_share_of_successful_checks(statuses, percent):
    uptime = build_uptime(make_results(*statuses), slots=100)

    assert uptime.percent == percent
