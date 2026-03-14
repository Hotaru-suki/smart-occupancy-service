def assert_keys_exist(data: dict, required_fields: list[str]):
    for field in required_fields:
        assert field in data, f"缺少字段: {field}"


def assert_non_negative_number(value, field_name: str):
    assert isinstance(value, (int, float)), f"{field_name} 不是数字类型"
    assert value >= 0, f"{field_name} 不能为负数"


def assert_bool_field(value, field_name: str):
    assert isinstance(value, bool), f"{field_name} 不是 bool 类型"