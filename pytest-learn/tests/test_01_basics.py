"""
test_01_basics.py — pytest 最基础的四件事
================================================================
这一节不碰你的业务代码，只把 pytest 的"语法"讲清楚：
    1. 测试函数怎么写、pytest 怎么自动找到它
    2. assert 断言
    3. 测"应该报错"的代码：pytest.raises
    4. 参数化：一份代码测 N 组数据

运行：
    .\\run_tests.ps1 tests/test_01_basics.py
"""

import pytest


# ----------------------------------------------------------------------
# 被测的小函数（真实项目里这个函数在 adas/ 里，由开发写）
# ----------------------------------------------------------------------
def safe_divide(a: float, b: float) -> float:
    """除零时主动抛异常，而不是返回一个奇怪的值（比如 None 或 inf）。"""
    if b == 0:
        raise ZeroDivisionError("除数不能为 0")
    return a / b


# ======================================================================
# 1. 最简单的测试
# ======================================================================
# 只需遵守两条命名规则，pytest 就会自动发现并执行：
#     文件名：test_*.py  或  *_test.py
#     函数名：test_ 开头
# 不需要继承任何类，不需要写注册代码，不需要写 main()。

def test_simple_assert():
    """一个测试函数可以有多个 assert；第一个失败，后面的就不执行了。"""
    assert 1 + 1 == 2
    assert "error" in "[ERROR] boom".lower()
    assert [1, 2, 3][-1] == 3


def test_dict_and_list_assert():
    """断言不限于等于，任何返回 True/False 的表达式都行。"""
    data = {"ERROR": 2, "FAIL": 1}
    assert "ERROR" in data
    assert data["FAIL"] == 1
    assert sum(data.values()) == 3


def test_assert_with_message():
    """断言后面可以加说明文字，失败时会被打印出来 —— 排错时非常有用。"""
    expected_errors = 3
    actual_errors = 3
    assert actual_errors == expected_errors, (
        f"ERROR 次数不符：期望 {expected_errors}，实际 {actual_errors}"
    )


# ======================================================================
# 2. 参数化：一份代码，测 N 组数据
# ======================================================================
# 这是自动化测试最有价值的能力之一。
# 没有参数化，你要写 4 个几乎一样的函数；有了参数化，写 1 个 + 一张数据表。

@pytest.mark.parametrize(
    "a, b, expected",
    [
        (10, 2, 5),
        (9, 3, 3),
        (1, 4, 0.25),
        (-6, 3, -2),
    ],
)
def test_divide_normal_cases(a, b, expected):
    """参数里的每一行都会生成一条独立用例，失败时能精确定位是哪组数据。"""
    assert safe_divide(a, b) == expected


# ======================================================================
# 3. 测"应该报错"的代码
# ======================================================================
# 新手最容易漏的就是"异常路径"。
# 但真实项目里，"程序该报错时有没有正确报错"和"正常时结果对不对"同样重要。

def test_raises_when_divide_by_zero():
    """pytest.raises 捕获异常；如果代码没抛异常，这条用例反而会失败。"""
    with pytest.raises(ZeroDivisionError) as exc_info:
        safe_divide(1, 0)

    # exc_info.value 是抓到的异常对象，可以进一步断言它的内容
    assert "除数" in str(exc_info.value)


@pytest.mark.parametrize("b", [0, 0.0, -0])
def test_raises_for_all_kinds_of_zero(b):
    """参数化 + 异常：0、0.0、-0 都应该被同样拦住。"""
    with pytest.raises(ZeroDivisionError):
        safe_divide(3, b)


def test_raises_with_match():
    """match 用正则匹配异常信息，可以少写一层断言。"""
    with pytest.raises(ZeroDivisionError, match="除数不能为 0"):
        safe_divide(1, 0)


# ======================================================================
# 4. 浮点数不要用 == 比较
# ======================================================================

def test_float_comparison_needs_approx():
    """0.1 + 0.2 在计算机里不等于 0.3（浮点精度问题）。

    错误写法：assert 0.1 + 0.2 == 0.3        ← 必然失败
    正确写法：assert 0.1 + 0.2 == pytest.approx(0.3)
    """
    assert 0.1 + 0.2 != 0.3           # 这行本身就是个知识点
    assert 0.1 + 0.2 == pytest.approx(0.3)
    assert safe_divide(1, 3) == pytest.approx(0.3333, abs=1e-4)
