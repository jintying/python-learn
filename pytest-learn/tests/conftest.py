"""
tests/conftest.py — pytest 的「公共装备间」
================================================================
放在 conftest.py 里的 fixture，同目录及子目录下所有测试文件都能直接当参数用，
不需要 import。这是 pytest 组织测试代码最核心的机制。

什么是 fixture？
    就是"测试开始前先替你准备好东西"：
        - 准备测试数据（这里：一份真实的样本日志目录）
        - 准备干净的环境（这里：一个临时文件夹，测试完自动删）
    fixture 解决了自动化测试最烦人的两件事：
        1. 重复的准备代码（每个用例都写一遍"先创建目录再建文件"）
        2. 用例之间互相污染（上一个用例改的文件影响下一个用例）

    fixture 的名字写成测试函数的参数，pytest 自动把值喂进来 —— 这叫依赖注入。
"""

import sys
from pathlib import Path

import pytest

# 项目根目录（tests/ 的上一级）
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 双保险：pytest.ini 里已经写了 pythonpath = .
# 这里再兜一次，保证不管从哪个目录启动都能 import 到 adas 包。
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

SAMPLE_LOGS = PROJECT_ROOT / "data" / "sample_logs"


# ----------------------------------------------------------------------
# 1. 准备"真实数据"
# ----------------------------------------------------------------------
@pytest.fixture(scope="session")
def sample_logs_dir() -> Path:
    """真实样本日志目录（data/sample_logs，就是你那 3 份车载日志）。

    scope="session"：整个测试会话只执行一次，所有用例共用同一个值。
    适合这种"只读、准备起来略贵"的资源。
    """
    assert SAMPLE_LOGS.is_dir(), f"样本日志目录不存在: {SAMPLE_LOGS}"
    return SAMPLE_LOGS


# ----------------------------------------------------------------------
# 2. 准备"干净环境"
# ----------------------------------------------------------------------
@pytest.fixture
def temp_log_dir(tmp_path: Path) -> Path:
    """一个干净的临时日志目录，每个用例一个，互不干扰。

    tmp_path 是 pytest 内置 fixture：自动创建临时目录，测试结束后自动清理。
    默认 scope 是 function，也就是"每个测试函数都重新来一份"。
    """
    d = tmp_path / "logs"
    d.mkdir()
    return d


# ----------------------------------------------------------------------
# 3. 准备"造数据的工具"
# ----------------------------------------------------------------------
@pytest.fixture
def make_log(temp_log_dir: Path):
    """返回一个"现场造日志文件"的小工具。

    用法：
        def test_xxx(make_log):
            make_log("veh_a.log", "[ERROR] boom", "[WARN] hmm")
            # 这时 temp_log_dir/veh_a.log 已经存在了

    为什么要把"造数据"也做成 fixture？
        因为真实车载日志动辄几百 MB，拿真实数据跑单元测试又慢又不可控。
        自动化测试的标准做法是：用最小的假数据，精准命中要验证的那个行为。
    """

    def _make(name: str, *lines: str) -> Path:
        path = temp_log_dir / name
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path

    return _make
