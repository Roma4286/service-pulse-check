from dataclasses import dataclass

from app.models import CheckResult, ResultStatus


@dataclass(frozen=True, slots=True)
class Uptime:
    slots: int
    results: list[CheckResult]
    empty_slots: int
    percent: str | None
    last_status: ResultStatus | None


def build_uptime(newest_first: list[CheckResult], slots: int) -> Uptime:
    results = list(reversed(newest_first))
    if not results:
        return Uptime(
            slots=slots, results=[], empty_slots=slots, percent=None, last_status=None
        )

    successes = sum(result.status == ResultStatus.SUCCESS for result in results)
    return Uptime(
        slots=slots,
        results=results,
        empty_slots=max(slots - len(results), 0),
        percent=format_percent(successes / len(results) * 100),
        last_status=results[-1].status,
    )


def format_percent(value: float) -> str:
    return f"{value:.1f}".removesuffix(".0")
