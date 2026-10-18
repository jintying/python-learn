"""
log_analyzer.py — 车载日志关键字自动分析工具
================================================
功能：扫描指定文件夹里的所有日志文件，统计你关心的关键字各出现多少次，
      并把结果打印成表格。

用途示例：平时排查问题要 grep 一堆日志，这个脚本可以一次扫完整个目录，
          自动汇总 error/warn/fail 等关键字的出现次数，帮你快速定位重点。

用法（在终端运行）：
    .venv/Scripts/python log_analyzer.py 日志文件夹路径  error warn fail

配套演示数据：脚本同目录下有个 sample_logs/ 文件夹，可直接拿来试。
"""

import os
import sys
from collections import Counter


def scan_logs(folder_path: str, keywords: list[str]) -> dict[str, Counter]:
    """
    遍历文件夹下的所有 .log 和 .txt 文件，统计每个关键字出现的次数。

    参数:
        folder_path: 日志文件夹路径
        keywords:   要统计的关键字列表
    返回:
        {文件名: Counter{关键字: 次数}}
    """
    result = {}

    # os.walk 递归遍历文件夹（含子文件夹），把文件一个个找出来
    for root, dirs, files in os.walk(folder_path):
        for fname in files:
            # 只处理文本类日志文件
            if not fname.endswith((".log", ".txt")):
                continue

            file_path = os.path.join(root, fname)
            counter = Counter()  # 用 Counter 自动计数

            # 逐行读取，避免大文件一次性读入内存
            try:
                # encoding="utf-8", errors="ignore" 防止乱码/报错中断
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        for kw in keywords:
                            # 不区分大小写统计
                            if kw.lower() in line.lower():
                                counter[kw] += 1
            except Exception as e:
                print(f"  跳过文件 {fname}: {e}")
                continue

            if sum(counter.values()) > 0:  # 有命中的文件才记录
                result[fname] = counter

    return result


def main():
    # 1. 解析命令行参数：至少需要 文件夹路径 + 1 个关键字
    if len(sys.argv) < 3:
        print("用法: python log_analyzer.py <日志文件夹> <关键字1> [关键字2] ...")
        print("示例: python log_analyzer.py sample_logs error warn fail")
        sys.exit(1)

    folder_path = sys.argv[1]
    keywords = sys.argv[2:]

    # 2. 检查文件夹是否存在
    if not os.path.isdir(folder_path):
        print(f"错误: 找不到文件夹 {folder_path}")
        sys.exit(1)

    # 3. 开始扫描
    print(f"正在扫描 {folder_path} ...")
    print(f"关键字: {keywords}\n")

    stats = scan_logs(folder_path, keywords)

    # 4. 打印汇总表格
    if not stats:
        print("未在日志中找到任何关键字命中。")
        return

    print(f"{'日志文件':<30} " + "  ".join(f"{kw:<10}" for kw in keywords))
    print("-" * (30 + 12 * len(keywords)))

    for fname, counter in stats.items():
        counts = [str(counter.get(kw, 0)) for kw in keywords]
        print(f"{fname:<30} " + "  ".join(f"{c:<10}" for c in counts))

    # 5. 汇总总数
    total = {kw: sum(c.get(kw, 0) for c in stats.values()) for kw in keywords}
    print("\n===== 汇总 =====")
    for kw, n in total.items():
        print(f"{kw}: 共 {n} 次")


if __name__ == "__main__":
    main()
