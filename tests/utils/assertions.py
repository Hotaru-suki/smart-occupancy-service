def assert_keys_exist(data: dict, required_fields: list[str]):
    for field in required_fields:
        assert field in data, f"缺少字段: {field}"



def assert_non_negative_number(value, field_name: str):
    assert isinstance(value, (int, float)), f"{field_name} 不是数字类型"
    assert value >= 0, f"{field_name} 不能为负数"



def assert_bool_field(value, field_name: str):
    assert isinstance(value, bool), f"{field_name} 不是 bool 类型"



def assert_iso_datetime_like(value, field_name: str):
    assert value is None or isinstance(value, str), f"{field_name} 既不是 str 也不是 null"



def assert_event_item_schema(item: dict):
    assert_keys_exist(item, ["timestamp", "event", "people_count"])
    assert isinstance(item["timestamp"], str)
    assert isinstance(item["event"], str)
    assert isinstance(item["people_count"], int)
    assert item["people_count"] >= 0


def assert_no_redirect(response):
    assert response.status_code < 300 or response.status_code >= 400
    normalized_headers = {key.lower(): value for key, value in response.headers.items()}
    assert "location" not in normalized_headers
