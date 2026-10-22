from datetime import datetime

from whoop_mcp.analytics import daily_evidence, local_bounds, summarize


def test_missingness_and_pending():
    result = summarize(
        "recovery",
        [
            {"score_state": "SCORED", "score": {"recovery_score": 0, "hrv_rmssd_milli": 50}},
            {"score_state": "SCORED", "score": {"recovery_score": 100}},
            {"score_state": "PENDING_SCORE", "score": {"recovery_score": 80}},
            {"score_state": "UNSCORABLE", "score": None},
        ],
    )
    assert result["metrics"]["recovery_score"]["mean"] == 50
    assert result["metrics"]["recovery_score"]["missing"] == 2
    assert result["metrics"]["hrv_rmssd_milli"]["observations"] == 1
    assert result["metrics"]["resting_heart_rate"]["mean"] is None


def test_dst_bounds():
    start, end = local_bounds("2026-03-08", "America/Los_Angeles")
    assert (
        datetime.fromisoformat(end) - datetime.fromisoformat(start)
    ).total_seconds() == 23 * 3600
    start, end = local_bounds("2026-11-01", "America/Los_Angeles")
    assert (
        datetime.fromisoformat(end) - datetime.fromisoformat(start)
    ).total_seconds() == 25 * 3600


def test_exact_cycle_join_and_local_date_filter():
    class API:
        def history(self, kind, *_):
            return {
                "records": [
                    {"id": 7, "start": "2026-10-22T15:00:00Z"},
                    {"id": 8, "start": "2026-10-22T01:00:00Z"},
                ],
                "complete": True,
            }

        def detail(self, kind, identifier):
            assert identifier == 7
            return {"data": {"cycle_id": identifier}}

    result = daily_evidence(API(), "2026-10-22", "America/Los_Angeles")
    assert len(result["cycles"]) == 1
    assert result["cycles"][0]["recovery"]["cycle_id"] == 7
    assert len(result["workouts"]["records"]) == 1
