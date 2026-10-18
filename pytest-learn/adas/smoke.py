"""
adas/smoke.py — 发版冒烟守门（Release Gate）
================================================================
把"扫日志"升级成"给结论"：跑一遍样本日志，自动判断这个版本能不能发。

这就是 OTA QA / 发版方向每天在做的事：
    规则 → 执行 → 断言 → PASS / FAIL → 卡住不合格的版本

你原来手工做的事（打开日志、grep ERROR、数一数、判断"这个版本还行吧"），
在这里被固化成一条可重复执行的规则。这就是自动化测试的核心价值：
    把"人的判断"变成"代码的判断"，于是它可以被反复、免费、无遗漏地执行。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

from adas.log_analyzer import scan_logs, total_counts

# 默认冒烟规则：关键字 -> 允许出现的最大次数（超过就判失败）
#
# 这里刻意设得比较宽松（宽进严出是真实项目的常见做法：先让版本能过，
# 再随版本成熟逐步收紧阈值）。测试里会演示"同一个日志、收紧规则就判失败"。
DEFAULT_RULES: dict[str, int] = {
    "ERROR": 10,
    "FAIL": 5,
}


@dataclass
class SmokeResult:
    """冒烟结论。

    用 dataclass 把结果包成一个对象，好处是：
        result.passed        ← 直接断言布尔值
        result.violations    ← 失败原因，直接写进报告
        result.total         ← 原始数据，方便排查
    比让函数打印一堆文字然后靠人眼看强得多。
    """

    passed: bool
    total: dict[str, int]
    violations: list[str] = field(default_factory=list)

    @property
    def summary(self) -> str:
        if self.passed:
            return "PASS"
        return "FAIL: " + "; ".join(self.violations)


def run_smoke(
    folder: str | Path, rules: Mapping[str, int] | None = None
) -> SmokeResult:
    """对指定日志文件夹跑冒烟守门。

    参数:
        folder: 日志文件夹
        rules:  规则表 {关键字: 允许的最大次数}，不传就用 DEFAULT_RULES
    返回:
        SmokeResult
    """
    # 注意：这里用 dict(...) 拷一份，绝不原地修改调用方传进来的 rules，
    # 也绝不改到全局的 DEFAULT_RULES。这类"副作用"是常见 bug，
    # 后面的测试里专门有一条用例守着它。
    rules = dict(DEFAULT_RULES if rules is None else rules)
    keywords = list(rules)

    stats = scan_logs(folder, keywords)
    totals = total_counts(stats, keywords)

    violations = [
        f"{kw} 出现 {totals.get(kw, 0)} 次，超过上限 {limit}"
        for kw, limit in rules.items()
        if totals.get(kw, 0) > limit
    ]

    return SmokeResult(passed=not violations, total=totals, violations=violations)
