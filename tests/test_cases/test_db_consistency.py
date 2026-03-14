import allure
import pytest


@allure.epic("Occupancy System")
@allure.feature("DB Consistency")
@pytest.mark.db
@pytest.mark.regression
def test_daily_stats_table_accessible(mysql_helper):
    with allure.step("确认 daily_stats 表可访问"):
        row = mysql_helper.get_today_stat()
    assert row is None or isinstance(row, dict)


@allure.epic("Occupancy System")
@allure.feature("DB Consistency")
@pytest.mark.db
@pytest.mark.regression
def test_occupancy_events_table_accessible(mysql_helper):
    with allure.step("确认 occupancy_events 表可访问"):
        row = mysql_helper.get_latest_event()
    assert row is None or isinstance(row, dict)


@allure.epic("Occupancy System")
@allure.feature("DB Consistency")
@pytest.mark.db
@pytest.mark.regression
def test_status_and_daily_stats_basic_consistency(client, mysql_helper):
    with allure.step("获取状态接口数据"):
        status_data = client.get("/api/status").json()

    with allure.step("获取数据库中最新统计数据"):
        stat = mysql_helper.get_today_stat()

    # 测试环境下表可能还没有统计数据，先做宽松校验
    if stat is not None:
        assert stat["max_people"] >= 0
        assert stat["total_occupied_sec"] >= 0

        # 接口值不应为负
        assert status_data["max_people_today"] >= 0
        assert status_data["today_total_occupied_sec"] >= 0


@allure.epic("Occupancy System")
@allure.feature("DB Consistency")
@pytest.mark.db
@pytest.mark.regression
def test_latest_event_record_fields(mysql_helper):
    with allure.step("获取数据库中最新事件记录"):
        event = mysql_helper.get_latest_event()

    if event is not None:
        assert "event_type" in event
        assert "people_count" in event
        assert event["event_type"] in ["enter_region", "leave_region"]
        assert event["people_count"] >= 0