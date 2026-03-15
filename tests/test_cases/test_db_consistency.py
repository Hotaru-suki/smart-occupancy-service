import allure
import pytest


@allure.epic("Occupancy System")
@allure.feature("DB Consistency")
@pytest.mark.db
@pytest.mark.regression
def test_daily_stats_table_accessible(mysql_helper, attach_kv):
    with allure.step("确认 daily_stats 表可访问"):
        row = mysql_helper.get_today_stat()
        attach_kv("latest_daily_stat", row)
    assert row is None or isinstance(row, dict)


@allure.epic("Occupancy System")
@allure.feature("DB Consistency")
@pytest.mark.db
@pytest.mark.regression
def test_occupancy_events_table_accessible(mysql_helper, attach_kv):
    with allure.step("确认 occupancy_events 表可访问"):
        row = mysql_helper.get_latest_event()
        attach_kv("latest_event", row)
    assert row is None or isinstance(row, dict)


@allure.epic("Occupancy System")
@allure.feature("DB Consistency")
@pytest.mark.db
@pytest.mark.regression
def test_status_and_daily_stats_basic_consistency(client, mysql_helper, attach_kv):
    with allure.step("获取状态接口数据"):
        status_data = client.get("/api/status").json()
        attach_kv("status_api_data", status_data)

    with allure.step("获取数据库中最新统计数据"):
        stat = mysql_helper.get_today_stat()
        attach_kv("latest_daily_stat", stat)

    if stat is not None:
        assert stat["max_people"] >= 0
        assert stat["total_occupied_sec"] >= 0
        assert status_data["max_people_today"] >= 0
        assert status_data["today_total_occupied_sec"] >= 0


@allure.epic("Occupancy System")
@allure.feature("DB Consistency")
@pytest.mark.db
@pytest.mark.regression
def test_latest_event_record_fields(mysql_helper, attach_kv):
    with allure.step("获取数据库中最新事件记录"):
        event = mysql_helper.get_latest_event()
        attach_kv("latest_event", event)

    if event is not None:
        assert "event_type" in event
        assert "people_count" in event
        assert event["event_type"] in ["enter_region", "leave_region"]
        assert event["people_count"] >= 0


@allure.epic("Occupancy System")
@allure.feature("DB Consistency")
@pytest.mark.db
@pytest.mark.regression
def test_latest_event_and_events_api_basic_consistency(client, mysql_helper, attach_kv):
    with allure.step("获取事件接口第一条记录"):
        api_events = client.get("/api/events?limit=1").json().get("events", [])
        attach_kv("events_api_data", api_events)

    with allure.step("获取数据库最新事件"):
        latest_event = mysql_helper.get_latest_event()
        attach_kv("latest_event", latest_event)

    if api_events and latest_event is not None:
        first = api_events[0]
        assert latest_event["event_type"] == first["event"]
        assert latest_event["people_count"] == first["people_count"]
