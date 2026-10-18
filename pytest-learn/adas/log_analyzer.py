"""
adas/log_analyzer.py — 被测对象（产品代码）
================================================================
这是把你之前写的 python-learn/log_analyzer.py 做了一次「重构」：
把逻辑从 main() 里抽成独立函数，这样 pytest 才能直接调用它们做测试。

为什么要重构？
    原来的写法，所有逻辑都在 main() 里，只能"整体运行一遍看输出"。
    测试没法只测其中一小块，也没法传入不同的输入看结果。
    抽成函数之后：
        count_in_lines([...], ["error"])   ← 可以只测这一个行为
    这就是"可测试性"（testability）：代码的写法直接决定它好不好测。

重构后保留的行为（和原脚本一致）：
    - 递归扫描文件夹
    - 只处理 .log / .txt
    - 关键字不区分大小写
    - 一行里同一个关键字只算 1 次（按"日志条数"计，和 grep -c 的直觉一致）
    - 没有命中的文件不记录
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Iterable, Sequence

# 只处理这些后缀的文件
LOG_SUFFIXES = (".log", ".txt")


def iter_log_files(folder: str | Path) -> list[Path]:
    """递归找出文件夹下所有日志文件。

    两个刻意的设计，都是为了「好测」：
      1. 路径不存在时抛 NotADirectoryError —— 明确报错，不要悄悄返回空列表
      2. 返回值排序 —— 顺序稳定，测试结果不会时好时坏（flaky test）
    """
    folder = Path(folder)
    if not folder.is_dir():
        raise NotADirectoryError(f"不是文件夹: {folder}")

    files = [
        p
        for p in folder.rglob("*")
        if p.is_file() and p.suffix.lower() in LOG_SUFFIXES
    ]
    return sorted(files)


def count_in_lines(lines: Iterable[str], keywords: Sequence[str]) -> Counter:
    """统计每一行里命中的关键字，一行里同一个关键字只记 1 次。

    例：'[ERROR] a [ERROR] b' 这一行里，error 算 1 次而不是 2 次。

    纯函数：同样的输入永远给同样的输出，不读文件、不依赖全局状态 —— 最好测。
    """
    counter: Counter = Counter()
    for line in lines:
        lowered = line.lower()
        for kw in keywords:
            if kw.lower() in lowered:
                counter[kw] += 1
    return counter


def analyze_file(file_path: str | Path, keywords: Sequence[str]) -> Counter:
    """分析单个日志文件。

    文件不存在 / 没权限时直接抛异常，交给调用方决定怎么处理。
    encoding + errors='ignore' 是为了防止乱码中断扫描（和原脚本一致）。
    """
    path = Path(file_path)
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        return count_in_lines(f, keywords)


def scan_logs(folder: str | Path, keywords: Sequence[str]) -> dict[str, Counter]:
    """扫描整个文件夹，返回 {文件名: Counter}，只保留有命中的文件。"""
    result: dict[str, Counter] = {}
    for path in iter_log_files(folder):
        counter = analyze_file(path, keywords)
        if sum(counter.values()) > 0:
            result[path.name] = counter
    return result


def total_counts(
    stats: dict[str, Counter], keywords: Sequence[str]
) -> dict[str, int]:
    """把 scan_logs 的结果汇总成"每个关键字总共出现多少次"。"""
    return {kw: sum(c.get(kw, 0) for c in stats.values()) for kw in keywords}
