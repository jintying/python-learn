"""
adas/version.py — 版本号解析与比较
================================================================
这是 OTA / 发版方向最基础的一块：判断"这个升级包到底能不能装"。

本示例的版本号约定：
    1.2.3          合法
    v1.2.3         合法（开头的 v/V 忽略）
    1.2            合法（等价于 1.2.0）
    1.2.3-rc1      合法（-rc/-beta/_x/+build 这类后缀本示例忽略）
    1.2.x / 1..2   非法（每一段必须是数字）
"""

from __future__ import annotations


def parse_version(text: str) -> tuple[int, ...]:
    """把版本号字符串解析成整数元组。

    >>> parse_version("v1.2.3")
    (1, 2, 3)
    >>> parse_version("1.2.3-rc1")
    (1, 2, 3)

    解析不了就抛 ValueError —— 宁可炸掉，也不要静默返回一个错的版本号。
    """
    if not isinstance(text, str):
        raise ValueError(f"版本号必须是字符串，收到 {type(text).__name__}")

    cleaned = text.strip().lstrip("vV")

    # 丢掉 -rc1 / _beta / +build 这类后缀
    for sep in ("-", "_", "+"):
        cleaned = cleaned.split(sep)[0]

    if not cleaned:
        raise ValueError(f"空的版本号: {text!r}")

    numbers: list[int] = []
    for part in cleaned.split("."):
        if not part.isdigit():
            raise ValueError(f"版本号里有非数字段: {text!r}")
        numbers.append(int(part))

    return tuple(numbers)


def compare_versions(a: str, b: str) -> int:
    """比较两个版本号。a > b 返回 1，a < b 返回 -1，相等返回 0。

    关键点：先补零再比。
        直接比元组会得到 (1, 2) < (1, 2, 0) → 判定 1.2 比 1.2.0 旧，这是错的。
        补零成 (1, 2, 0) 和 (1, 2, 0) 才能得到"相等"的正确结论。
    """
    va, vb = parse_version(a), parse_version(b)

    length = max(len(va), len(vb))
    va = va + (0,) * (length - len(va))
    vb = vb + (0,) * (length - len(vb))

    return (va > vb) - (va < vb)


def is_newer(candidate: str, base: str) -> bool:
    """candidate 是否比 base 新。"""
    return compare_versions(candidate, base) > 0


def can_upgrade(current: str, target: str) -> tuple[bool, str]:
    """OTA 升级准入判断。

    规则：
        - 目标版本比当前新  → 允许
        - 目标版本与当前相同 → 拒绝（重复刷写没有意义）
        - 目标版本比当前旧  → 拒绝（防降级，这是 OTA 的硬要求）

    返回 (是否允许, 原因说明)，原因用于写进日志/报告，方便追责。
    """
    diff = compare_versions(target, current)

    if diff > 0:
        return True, f"允许升级: {current} -> {target}"
    if diff == 0:
        return False, f"拒绝: 目标版本与当前版本相同 ({current})"
    return False, f"拒绝: 不允许降级 ({current} -> {target})"
