"""
test_04_smoke.py — 把它们串起来：跑一次「发版冒烟守门」
================================================================
这一节是综合练习，也最贴近 OTA QA / 发版方向的真实工作：
    规则 → 扫日志 → 汇总 → 判定 PASS / FAIL → 卡住不合格的版本

新知识点：
    - @pytest.mark.smoke ：给用例打标记，可以只跑标记的这一批
    - pytest.skip()      ：主动跳过某条用例
    - @pytest.mark.xfail ：标记"已知会失败"，不阻塞流水线
    - 边界值：阈值是"超过才失败"还是"达到就失败"

运行：
    .\\run_tests.ps1 -m smoke        ← 只跑冒烟那批
    .\\run_tests.ps1                 ← 跑全部
"""

import pytest

from adas.smoke import DEFAULT_RULES, SmokeResult, run_smoke


# ======================================================================
# 一、真实数据：样本版本应该通过
# ======================================================================

@pytest.mark.smoke
def test_sample_version_passes_default_rules(sample_logs_dir):
    """样本日志应该能过默认冒烟规则。"""
    result = run_smoke(sample_logs_dir)

    # 把 summary 作为断言消息传进去：失败时输出里直接看到原因，不用再翻代码
    assert isinstance(result, SmokeResult)
    assert result.passed is True, result.summary
    assert result.violations == []
    assert result.total["ERROR"] == 5
    assert result.total["FAIL"] == 4


@pytest.mark.smoke
def test_tightening_rules_blocks_the_same_version(sample_logs_dir):
    """同一个版本、同一批日志，只把阈值收紧，就该被卡住。

    这条用例点出了"守门"的实质：
        结论不取决于数据本身，而取决于你定的标准。
    这也正是 OTA QA 这个岗位存在的意义 —— 标准由你把关。
    """
    result = run_smoke(sample_logs_dir, rules={"ERROR": 3, "FAIL": 2})

    assert result.passed is False
    assert len(result.violations) == 2
    assert "ERROR" in result.summary
    assert "FAIL" in result.summary


# ======================================================================
# 二、造假数据：验证守门真的能拦住坏版本
# ======================================================================

@pytest.mark.smoke
def test_bad_version_is_blocked(make_log, temp_log_dir):
    """故意造一批"坏"日志，冒烟必须判 FAIL。

    这就是守门的意义：如果坏版本也能过，那这套自动化就是摆设。
    写自动化测试时，一定要有"反例"用例 —— 只测通过路径的测试是假的安全感。
    """
    make_log("bad_01.log", "[ERROR] a", "[ERROR] b", "[ERROR] c")
    make_log("bad_02.log", "[FAIL] safety_check failed")

    result = run_smoke(temp_log_dir, rules={"ERROR": 1, "FAIL": 0})

    assert result.passed is False
    assert len(result.violations) == 2
    assert "超过上限" in result.summary


def test_clean_logs_pass(make_log, temp_log_dir):
    """干净的日志应该通过，且 pass 时 violations 是空的。"""
    make_log("clean.log", "[INFO] boot ok", "[INFO] self check ok")

    result = run_smoke(temp_log_dir, rules={"ERROR": 0, "FAIL": 0})

    assert result.passed is True
    assert result.violations == []
    assert result.summary == "PASS"
    assert result.total == {"ERROR": 0, "FAIL": 0}


# ======================================================================
# 三、边界值：阈值到底怎么算
# ======================================================================

def test_threshold_is_exclusive(make_log, temp_log_dir):
    """阈值是「超过才失败」：正好等于上限算通过（代码里用的是 > 而不是 >=）。

    这类"边界上算不算过"的歧义，必须用测试钉死，
    否则开发改一次、测试改一次，永远说不清。
    """
    make_log("edge.log", "[ERROR] a", "[ERROR] b")

    at_limit = run_smoke(temp_log_dir, rules={"ERROR": 2})
    assert at_limit.passed is True, "正好等于上限应该是通过"

    over_limit = run_smoke(temp_log_dir, rules={"ERROR": 1})
    assert over_limit.passed is False, "超过上限应该失败"


# ======================================================================
# 四、规则可配置 & 无副作用
# ======================================================================

def test_rules_are_configurable(make_log, temp_log_dir):
    """规则可以外部传入：同一个文件夹，换个规则结论就变。"""
    make_log("one_error.log", "[ERROR] boom")

    strict = run_smoke(temp_log_dir, rules={"ERROR": 0})
    loose = run_smoke(temp_log_dir, rules={"ERROR": 5})

    assert strict.passed is False
    assert loose.passed is True


def test_default_rules_are_not_mutated(make_log, temp_log_dir):
    """传入 rules 不应该改到全局的 DEFAULT_RULES。

    这类"函数偷偷改了全局变量"的副作用 bug 很难靠人眼发现，
    但用一条测试就能永久钉住。
    """
    before = dict(DEFAULT_RULES)

    make_log("x.log", "[ERROR] boom")
    run_smoke(temp_log_dir, rules={"ERROR": 0})

    assert DEFAULT_RULES == before


# ======================================================================
# 五、跳过 & 已知失败（流水线里的实用技巧）
# ======================================================================

def test_skip_example():
    """暂时不跑的用例用 pytest.skip 标记，而不是注释掉。

    好处：报告里能看到"有 1 条被跳过"，而不是悄无声息地少测了一块。
    注释掉的代码 = 没人记得它存在。
    """
    pytest.skip("演示用：这条用例故意跳过，报告里会显示 s")


@pytest.mark.skipif(True, reason="演示：条件跳过，例如只在 Linux 上跑")
def test_conditional_skip_example():
    """按条件跳过：比如某些用例只能在车端 Linux 环境跑，在 Windows 上自动跳过。"""
    raise AssertionError("这行不会被执行")


@pytest.mark.xfail(reason="演示：已知未修复的缺陷，先标记为 xfail，不阻塞流水线")
def test_known_bug_example():
    """xfail = 预期失败。

    报告里显示 x 而不是 F，流水线不会因此变红。
    等 bug 修好之后，它会变成 XPASS，提醒你"该把 xfail 标记摘掉了"。
    """
    assert 1 == 2
