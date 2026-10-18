"""
test_03_version.py — 版本号比较（OTA 发版方向的核心逻辑）
================================================================
这一节练的是测试设计里最重要的两种手法：
    - 等价类划分：把无限种输入，归成有限几"类"，每类挑代表
    - 边界值分析：专门测"刚好在边界上"的输入，bug 最爱藏在那里

被测对象：adas/version.py
"""

import pytest

from adas.version import can_upgrade, compare_versions, is_newer, parse_version


# ======================================================================
# 一、正常输入：等价类划分 + 参数化
# ======================================================================

@pytest.mark.parametrize(
    "text, expected",
    [
        ("1.2.3", (1, 2, 3)),          # 标准三段
        ("v1.2.3", (1, 2, 3)),         # 带 v 前缀
        ("V2.0", (2, 0)),              # 大写 V
        ("1.2", (1, 2)),               # 两段
        ("1", (1,)),                   # 一段
        ("1.2.3-rc1", (1, 2, 3)),      # 预发布后缀被忽略
        ("1.2.3+hotfix", (1, 2, 3)),   # 构建后缀被忽略
        ("  1.0  ", (1, 0)),           # 两端空格
        ("10.20.30", (10, 20, 30)),    # 多位数
    ],
)
def test_parse_version_normal(text, expected):
    assert parse_version(text) == expected


# ======================================================================
# 二、非法输入：异常等价类
# ======================================================================
# 全都要抛 ValueError，一个都不能漏 —— 版本号解析错了，OTA 会装错包。

@pytest.mark.parametrize(
    "bad",
    [
        "",         # 空字符串
        "v",        # 只有前缀
        "-rc1",     # 只有后缀
        "abc",      # 完全不是版本号
        "1.2.x",    # 含非数字段
        "1..2",     # 空段
        "1.2.3.",   # 结尾多余的点
    ],
)
def test_parse_version_invalid(bad):
    with pytest.raises(ValueError):
        parse_version(bad)


def test_parse_version_rejects_non_string():
    """传了非字符串也应该报 ValueError，而不是抛 TypeError 或静默通过。"""
    with pytest.raises(ValueError):
        parse_version(None)


# ======================================================================
# 三、边界值分析：比较版本号
# ======================================================================

@pytest.mark.parametrize(
    "a, b, expected",
    [
        # 普通大小关系
        ("1.2.4", "1.2.3", 1),
        ("1.2.3", "1.2.4", -1),
        ("1.2.3", "1.2.3", 0),
        # 边界：位数不同但其实是同一个版本 —— 这是最容易出 bug 的地方
        ("1.2", "1.2.0", 0),
        ("1.2.0", "1.2", 0),
        # 边界：前缀/后缀不影响
        ("v1.2.3", "1.2.3", 0),
        ("1.2.3-rc1", "1.2.3", 0),
        # 边界：跨段进位
        ("2.0", "1.9.9", 1),
        ("1.0.0", "0.99.99", 1),
        # 关键：不能按字符串比！"1.10" 在字符串里小于 "1.9"
        ("1.10.0", "1.9.0", 1),
        ("1.9.0", "1.10.0", -1),
    ],
)
def test_compare_versions(a, b, expected):
    assert compare_versions(a, b) == expected


def test_is_newer():
    assert is_newer("1.2.4", "1.2.3") is True
    assert is_newer("1.2.3", "1.2.4") is False
    assert is_newer("1.2.3", "1.2.3") is False
    # 1.2 和 1.2.0 是同一个版本，所以不算"更新"
    assert is_newer("1.2", "1.2.0") is False


# ======================================================================
# 四、业务逻辑：OTA 升级准入
# ======================================================================
# 相关用例可以放进以 Test 开头的类里分组（类名不必继承任何东西）。
# 注意：类里不能写 __init__，那是 pytest 的规矩。

class TestCanUpgrade:

    def test_higher_target_is_allowed(self):
        """目标版本更高 → 允许升级。"""
        allowed, reason = can_upgrade("1.2.3", "1.2.4")

        assert allowed is True
        assert "允许" in reason
        assert "1.2.3" in reason and "1.2.4" in reason   # 原因里带上下文，方便看日志

    def test_same_version_is_rejected(self):
        """目标版本等于当前 → 拒绝（重复刷写没有意义）。"""
        allowed, reason = can_upgrade("1.2.3", "1.2.3")

        assert allowed is False
        assert "相同" in reason

    def test_downgrade_is_rejected(self):
        """目标版本更低 → 拒绝（防降级，OTA 的硬要求）。"""
        allowed, reason = can_upgrade("1.3.0", "1.2.9")

        assert allowed is False
        assert "降级" in reason

    @pytest.mark.parametrize(
        "current, target, expected_reason_keyword",
        [
            ("2.0.0", "2.0.1", "允许"),
            ("2.0.1", "2.0.1", "相同"),
            ("2.0.1", "2.0.0", "降级"),
            ("1.2", "1.2.0", "相同"),      # 补零后相等，所以是"相同"而不是"降级"
            ("v1.0.0", "1.0.1", "允许"),   # 前缀不影响判断
        ],
    )
    def test_upgrade_matrix(self, current, target, expected_reason_keyword):
        """用一张表覆盖全部准入分支 —— 这就是"用例设计"的实际样子。"""
        allowed, reason = can_upgrade(current, target)

        assert expected_reason_keyword in reason
        assert allowed is (expected_reason_keyword == "允许")
