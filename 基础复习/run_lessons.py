"""
run_lessons.py — 课程运行器
================================================================
用法：
    python run_lessons.py            按顺序跑全部课程
    python run_lessons.py 05         只跑文件名以 05 开头的那一课
    python run_lessons.py --list     列出所有课程

平时你不用直接跑这个文件，双击 run.bat 就行。
"""

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SELF = Path(__file__).name


def find_lessons() -> list[Path]:
    """找出所有课程文件，按文件名排序（所以 01、02、03 会依次排好）。"""
    return sorted(p for p in HERE.glob("*.py") if p.name != SELF)


def main() -> None:
    args = sys.argv[1:]
    lessons = find_lessons()

    if "--list" in args or "-l" in args:
        print("可用的课程文件：")
        for p in lessons:
            print(f"   {p.name}")
        return

    if args:
        key = args[0]
        lessons = [p for p in lessons if p.name.startswith(key)]
        if not lessons:
            print(f"没找到以「{key}」开头的课程文件。")
            print("执行  run.bat --list  可以看到所有课程。")
            return

    if not lessons:
        print("这个文件夹里还没有课程文件。")
        return

    for i, path in enumerate(lessons, start=1):
        if i > 1:
            print("\n\n")
        print("=" * 72)
        print(f"  第 {i}/{len(lessons)} 个文件：{path.name}")
        print("=" * 72)

        # 用当前这个 Python 解释器去跑这一课，输出直接打到屏幕上
        # flush 一下，保证标题一定出现在这一课内容的前面
        sys.stdout.flush()
        subprocess.run([sys.executable, str(path)], cwd=str(HERE))

    print("\n" + "=" * 72)
    print("  全部课程跑完了。")
    print("=" * 72)


if __name__ == "__main__":
    main()
