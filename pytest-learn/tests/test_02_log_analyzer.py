"""
test_02_log_analyzer.py — 给你的日志分析工具写自动化测试
================================================================
这一节练的是"自动化测试真正落地长什么样"：
    - 用 fixture 拿真实测试数据
    - 用 tmp_path 造隔离的测试数据，不依赖真实文件
    - 正常路径和异常路径都要测
    - 用参数化把"一批数据"变成"一批用例"

被测对象：adas/log_analyzer.py（由你原来的 log_analyzer.py 重构而来）
"""

import pytest

from adas.log_analyzer import (
    analyze_file,
    count_in_lines,
    iter_log_files,
    scan_logs,
    total_counts,
)


# ======================================================================
# 一、测纯函数：count_in_lines
# ======================================================================

def test_count_in_lines_counts_matching_lines():
    """一行里同一个关键字只算 1 次（按"日志条数"计，不是按出现次数）。"""
    lines = [
        "[ERROR] boom [ERROR] again",   # 同一行出现两次 error，只算 1
        "[INFO] fine",
        "[WARN] hmm",
    ]
    counter = count_in_lines(lines, ["error", "warn", "info"])

    assert counter["error"] == 1
    assert counter["warn"] == 1
    assert counter["info"] == 1


def test_keywords_are_case_insensitive():
    """关键字大小写不敏感：传 error 能匹配到 [ERROR]。"""
    assert count_in_lines(["[ERROR] x"], ["error"])["error"] == 1
    assert count_in_lines(["[error] x"], ["ERROR"])["ERROR"] == 1


def test_no_hit_returns_zero():
    """没命中时返回 0，而不是报错 —— 调用方不用先判断 key 存不存在。"""
    counter = count_in_lines(["[INFO] all good"], ["error", "fail"])

    assert counter["error"] == 0
    assert counter["fail"] == 0
    assert sum(counter.values()) == 0


def test_keyword_is_substring_match():
    """关键字是「子串匹配」：搜 fail 会把 failed 也算进去。

    这是本工具的当前行为。测试把它固定下来，等于给后来的人留了一句说明：
        「这是已知行为，不是 bug。要改成精确匹配，请先改这条测试。」
    这就是测试的第二个作用 —— 当文档用。
    """
    counter = count_in_lines(
        ["[WARN] map_load: retry failed", "[FAIL] safety_check: hard fail"],
        ["fail"],
    )
    assert counter["fail"] == 2


def test_empty_input():
    """边界情况：空输入不应崩溃。"""
    assert sum(count_in_lines([], ["error"]).values()) == 0
    assert sum(count_in_lines(["[ERROR] x"], []).values()) == 0


# ======================================================================
# 二、测文件扫描：用临时目录造假数据（隔离测试）
# ======================================================================

def test_iter_log_files_only_picks_log_and_txt(temp_log_dir):
    """只挑 .log / .txt，别把 .json / .md 也当成日志。"""
    (temp_log_dir / "a.log").write_text("x", encoding="utf-8")
    (temp_log_dir / "b.txt").write_text("x", encoding="utf-8")
    (temp_log_dir / "c.json").write_text("{}", encoding="utf-8")
    (temp_log_dir / "d.md").write_text("# 说明", encoding="utf-8")

    names = [p.name for p in iter_log_files(temp_log_dir)]

    # 返回值是排过序的，所以顺序固定、结果可重复
    assert names == ["a.log", "b.txt"]


def test_iter_log_files_walks_subfolders(tmp_path):
    """子文件夹里的日志也要能扫到（真实日志常按日期/车辆分目录）。"""
    sub = tmp_path / "2026-10-15" / "veh_001"
    sub.mkdir(parents=True)
    (sub / "run.log").write_text("x", encoding="utf-8")

    files = iter_log_files(tmp_path)

    assert len(files) == 1
    assert files[0].name == "run.log"


def test_iter_log_files_raises_on_missing_folder(tmp_path):
    """异常路径也要测：路径不存在就该明确报错，而不是悄悄返回空列表。

    "悄悄返回空列表"是测试里最怕的行为 —— 它会让上层以为"没有错误日志"，
    于是把一个有问题的版本判成通过。这种 bug 比崩溃危险得多。
    """
    with pytest.raises(NotADirectoryError):
        iter_log_files(tmp_path / "不存在的目录")


def test_analyze_file_with_generated_log(make_log):
    """用 make_log fixture 现场造一个日志文件，测单文件分析。"""
    path = make_log(
        "veh_x.log",
        "[INFO] start",
        "[WARN] low confidence",
        "[ERROR] mismatch",
        "[ERROR] lateral deviation",
    )

    counter = analyze_file(path, ["ERROR", "WARN", "FAIL"])

    assert counter["ERROR"] == 2
    assert counter["WARN"] == 1
    assert counter["FAIL"] == 0


def test_scan_logs_skips_files_without_hits(make_log, temp_log_dir):
    """没有任何关键字命中的文件，不应该出现在结果里。"""
    make_log("quiet.log", "[INFO] all good")
    make_log("noisy.log", "[ERROR] boom")

    stats = scan_logs(temp_log_dir, ["ERROR"])

    assert list(stats) == ["noisy.log"]
    assert stats["noisy.log"]["ERROR"] == 1


def test_scan_logs_on_empty_folder(temp_log_dir):
    """空文件夹不应崩溃，返回空结果。"""
    assert scan_logs(temp_log_dir, ["ERROR"]) == {}


# ======================================================================
# 三、用真实样本数据验证（数据驱动测试）
# ======================================================================
# 这里断言的具体数字，是从你的 data/sample_logs 里数出来的真实值。
# 注意 veh_003 的 FAIL 是 2 —— 因为 "[ERROR] map_load: chunk failed" 里的
# "failed" 也含 "fail"，被子串匹配算进去了。这就是上面那条
# test_keyword_is_substring_match 想说明的事。

@pytest.mark.parametrize(
    "fname, expected_error, expected_fail",
    [
        ("veh_001.log", 2, 1),
        ("veh_002.log", 1, 1),
        ("veh_003.log", 2, 2),
    ],
)
def test_real_sample_per_file(sample_logs_dir, fname, expected_error, expected_fail):
    """一个用例文件 × 3 组数据 = 3 条独立用例。"""
    counter = analyze_file(sample_logs_dir / fname, ["ERROR", "FAIL"])

    assert counter["ERROR"] == expected_error
    assert counter["FAIL"] == expected_fail


def test_real_sample_totals(sample_logs_dir):
    """全目录汇总。"""
    stats = scan_logs(sample_logs_dir, ["ERROR", "FAIL", "WARN", "INFO"])

    assert sorted(stats) == ["veh_001.log", "veh_002.log", "veh_003.log"]

    totals = total_counts(stats, ["ERROR", "FAIL", "WARN", "INFO"])
    assert totals == {"ERROR": 5, "FAIL": 4, "WARN": 6, "INFO": 14}
