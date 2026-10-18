# pytest 自动化测试入门 —— 用你自己的车载日志工具练手
================================================================

这是配套 `python-learn` 的一套**可以真跑起来**的 pytest 学习示例。
被测对象就是你之前写的 `log_analyzer.py`（日志关键字统计工具），
所以我把它重构成了 `adas/log_analyzer.py`，又加了两个和 OTA/发版直接相关的模块。

**学完这套你能做到**：
- 看懂任何 Python 项目的测试代码在干什么
- 自己给一个功能写自动化测试（正常路径 + 异常路径 + 边界值）
- 在面试里把"自动化测试"讲出具体做法，而不是背概念

---

## 一、先搞清楚：自动化测试到底在做什么？

### 1.1 用你熟悉的场景对比

| | 手工测试（你过去 3 年做的） | 自动化测试 |
|---|---|---|
| 怎么做 | 上车、开一段、看现象、判断对不对 | 写代码定义"什么算对"，让机器去执行 |
| 判断 | 靠人的经验 | 靠 `assert` 断言（代码写的判据） |
| 一次耗时 | 一个冒烟来回 1-2 小时 | 0.19 秒（就是本示例 75 条用例的耗时） |
| 重复 100 遍 | 不可能 | 免费、结果完全一致 |
| 什么时候跑 | 你想起来的时候 | 每次发版自动跑（CI 流水线） |
| 谁来做 | 测试工程师 | 测试工程师（测试开发方向） |
| 适合什么 | 主观体验：乘坐舒适性、底盘质感、接管手感 | 客观规则：版本号对不对、日志里 ERROR 超没超阈值、接口字段齐不齐 |

**一句话**：手工测试负责"没有标准答案的判断"，自动化测试负责"有标准答案的重复劳动"。
两者不是替代关系，是分工关系。

### 1.2 自动化测试的核心就三步

任何一条自动化用例，拆开都是这三步：

```
    ① 准备输入 (Arrange)  →  ② 执行 (Act)  →  ③ 断言 (Assert)
    造数据 / 建环境           调用被测的函数        比对"实际"和"预期"
```

**断言（assert）是灵魂。** 没有断言的脚本只是一段"能跑的程序"，不是测试。
你之前的 `log_analyzer.py` 会打印一张表出来给人看 —— 那是工具；
加一句 `assert totals["ERROR"] == 5`，它才变成测试。

### 1.3 按颗粒度分，自动化测试一般有这几类

| 类型 | 测什么 | 谁写 | 你接触过的对应物 |
|---|---|---|---|
| **单元测试** | 一个函数、一个模块 | 开发为主，测试也写 | 本示例的 `test_03_version.py` |
| **集成/接口测试** | 两个模块对接、接口字段 | 测试 | 感知输出 → 规划输入的格式校验 |
| **数据/日志校验** | 跑完路测后离线扫日志判 PASS/FAIL | 测试 | **你原来的 `log_analyzer.py` 就是这个的雏形** |
| **回归 / 冒烟流水线** | 每次发版自动跑一整套，几分钟出结论 | 测试 | 本示例的 `test_04_smoke.py` |
| **UI / 端到端测试** | 从用户操作到结果的全链路 | 测试 | 车机界面点击、App 操作 |

对你现在投的 **OTA QA / 发版方向**，最重要的是后两类：
**数据校验** 和 **发版冒烟流水线**。

### 1.4 什么该自动化，什么不该

**该自动化**：
- 要反复跑的（每次发版都要做的冒烟）
- 判据明确的（阈值、字段、格式、版本号）
- 人做容易漏的（几百份日志里每一条 ERROR）
- 要留证据的（自动出报告，可追溯）

**不该自动化（或不该优先）**：
- 一次性的、只做一遍的
- 需要人主观打分的（"这个刹车感觉比较线性"）
- 界面还在天天改的（维护成本 > 收益）

> 记住一个判断标准：**"这件事我下个月还要再做一遍吗？"**
> 答案是要，就值得自动化。

---

## 二、pytest 是什么

Python 世界最主流的测试框架。特点：

- **零样板**：函数名 `test_` 开头就自动被发现，不用继承类、不用注册、不用写 `main()`
- **一个 `assert` 走天下**：不需要记 `assertEqual` / `assertTrue` 之类的几十个方法
- **fixture**：优雅地解决"测试前准备数据/环境"
- **参数化**：一份代码跑 N 组数据
- **生态强大**：报告、覆盖率、并行、重试、CI 集成全都有现成插件

### 五个必须记住的概念

| 概念 | 一句话解释 | 本示例在哪 |
|---|---|---|
| **测试发现** | 文件名 `test_*.py`、函数名 `test_*`，pytest 自动找到 | 所有 `tests/test_*.py` |
| **assert** | 断言，写"我预期是什么"，机器帮你比对 | `test_01_basics.py` |
| **fixture** | 测试前的准备工作，写一次到处用 | `tests/conftest.py` |
| **参数化** | 一份代码测 N 组数据 | `@pytest.mark.parametrize` |
| **conftest.py** | 放公共 fixture 的文件，同目录自动生效 | `tests/conftest.py` |

---

## 三、目录结构

```
python-learn/
├── log_analyzer.py            ← 你原来的脚本（保持原样，留作对照）
├── sample_logs/               ← 你原来的 3 份样本日志（保持原样）
└── pytest-learn/              ← 本次新增的学习工程
    ├── README.md              ← 本文件
    ├── pytest.ini             ← pytest 配置（测试目录、路径、标记）
    ├── requirements.txt       ← 依赖清单
    ├── run_tests.ps1          ← 一键运行脚本
    ├── adas/                  ← 【被测对象】相当于"开发写的产品代码"
    │   ├── log_analyzer.py    ←   你原脚本的重构版（抽成函数，才好测）
    │   ├── version.py         ←   版本号解析/比较 + OTA 升级准入判断
    │   └── smoke.py           ←   发版冒烟守门：日志 → PASS/FAIL 结论
    ├── data/sample_logs/      ← 3 份样本日志的副本（测试数据）
    └── tests/                 ← 【测试代码】相当于"测试写的自动化用例"
        ├── conftest.py        ←   公共 fixture（装备间）
        ├── test_01_basics.py      ← pytest 语法：断言、异常、参数化
        ├── test_02_log_analyzer.py← 给你的日志工具写测试
        ├── test_03_version.py     ← 版本比较：等价类 + 边界值
        └── test_04_smoke.py       ← 综合：发版冒烟守门
```

> **为什么要有 `adas/` 和 `tests/` 两个目录？**
> 这是真实项目的标准分层：产品代码和测试代码分开放。
> 重构前你的脚本只有"整体跑一遍"这一种用法，没法单独测某个行为 ——
> 这就是"可测试性"，代码怎么写，直接决定它好不好测。

---

## 四、怎么跑

需要先装 pytest（**已经帮你装好了**，装在 `python-learn/.venv` 里）。
如果换电脑要重装：

```powershell
cd D:\Desktop\python-learn
.\.venv\Scripts\python.exe -m pip install pytest
```

### 常用命令

```powershell
cd D:\Desktop\python-learn\pytest-learn

# 1. 跑全部（最简单）
.\run_tests.ps1

# 2. 直接调 pytest 也行
..\.venv\Scripts\python.exe -m pytest

# 3. 只跑某一个文件
..\.venv\Scripts\python.exe -m pytest tests/test_03_version.py

# 4. 只跑名字里含 version 的用例（-k 关键字筛选）
..\.venv\Scripts\python.exe -m pytest -k version

# 5. 只跑冒烟那批（自定义标记）
..\.venv\Scripts\python.exe -m pytest -m smoke

# 6. 失败时立刻停下，方便一个一个看
..\.venv\Scripts\python.exe -m pytest -x

# 7. 失败时进入交互式调试（进阶）
..\.venv\Scripts\python.exe -m pytest --pdb

# 8. 看每条用例的耗时（找慢用例）
..\.venv\Scripts\python.exe -m pytest --durations=5
```

### 正常输出长这样

```
72 passed, 2 skipped, 1 xfailed in 0.19s
```

读法：
- `72 passed` —— 通过的用例数
- `2 skipped` —— 主动跳过的（`pytest.skip`）
- `1 xfailed` —— 预期失败（`xfail`，已知 bug，不阻塞流水线）
- `0.19s` —— 75 条用例跑了 0.19 秒。**这就是自动化测试的威力。**

> 提示：PowerShell 里中文可能显示成乱码（`��ʾ`）。
> 加一句 `$env:PYTHONIOENCODING='utf-8'` 再跑就正常了。

---

## 五、四个文件分别教什么

### `test_01_basics.py` —— pytest 语法（13 条用例）

| 知识点 | 关键写法 |
|---|---|
| 测试怎么写 | `def test_xxx():` + `assert` |
| 参数化 | `@pytest.mark.parametrize("a, b, expected", [...])` |
| 测异常 | `with pytest.raises(ZeroDivisionError) as e:` |
| 异常信息匹配 | `pytest.raises(ValueError, match="...")` |
| 浮点数比较 | `pytest.approx(0.3)` |

**要记住**：`pytest.raises` 是新手最容易漏的。异常路径不测，等于只测了一半。

### `test_02_log_analyzer.py` —— 给真实工具写测试（15 条用例）

这是最贴近你实际工作的一节：

```python
def test_real_sample_totals(sample_logs_dir):
    stats = scan_logs(sample_logs_dir, ["ERROR", "FAIL", "WARN", "INFO"])
    totals = total_counts(stats, ["ERROR", "FAIL", "WARN", "INFO"])
    assert totals == {"ERROR": 5, "FAIL": 4, "WARN": 6, "INFO": 14}
```

**学到了什么**：
1. 用 fixture 拿真实数据，用 `tmp_path` 造假数据 —— 真实数据验证结果，假数据验证逻辑
2. 异常路径也要测（`test_iter_log_files_raises_on_missing_folder` 那条用例解释了为什么）
3. **测试可以当文档用**：`test_keyword_is_substring_match` 把"搜 fail 会误伤 failed"这个行为固定下来，后面来的人一看就知道这是已知行为不是 bug
4. 一个真实发现：`veh_003.log` 的 FAIL 是 **2** 次不是 1 次，因为
   `[ERROR] map_load: chunk failed` 里的 `failed` 也含 `fail` —— 这就是子串匹配的副作用

### `test_03_version.py` —— 测试设计方法（37 条用例）

**等价类划分 + 边界值分析**，这是测试用例设计的两个基本功，也是面试必问：

```python
# 等价类：把无限输入归成几类，每类挑代表
@pytest.mark.parametrize("text, expected", [
    ("1.2.3", (1, 2, 3)),        # 标准
    ("v1.2.3", (1, 2, 3)),       # 带前缀
    ("1.2.3-rc1", (1, 2, 3)),    # 带预发布后缀
])

# 边界值：bug 最爱藏在边界上
("1.2", "1.2.0", 0),   # ← 补零！直接比元组会判定 1.2 < 1.2.0，这是错的
("1.10.0", "1.9.0", 1),# ← 不能按字符串比！"1.10" < "1.9" 是字符串的结果
```

### `test_04_smoke.py` —— 综合：发版守门（10 条用例）

把"扫日志"和"版本判断"串成一条守门流水线：

```python
result = run_smoke(sample_logs_dir, rules={"ERROR": 3, "FAIL": 2})
assert result.passed is False          # 收紧规则，同一个版本就被卡住了
assert len(result.violations) == 2
```

**新知识点**：
- `@pytest.mark.smoke` —— 打标记，`pytest -m smoke` 只跑这一批（发版前跑的就是这批）
- `pytest.skip()` —— 主动跳过，报告里能看到，比注释掉强
- `@pytest.mark.xfail` —— 已知 bug 先标记，不阻塞流水线，修好了会变 XPASS 提醒你
- **反例用例**：`test_bad_version_is_blocked` —— 只测通过路径的测试是假的安全感

---

## 六、建议的学习顺序（一周）

| 天 | 做什么 | 目标 |
|---|---|---|
| 第 1 天 | 跑通全部用例；读 `test_01_basics.py` | 知道 pytest 怎么用 |
| 第 2 天 | 读 `conftest.py` + `test_02`，把 `make_log` 改成造 5 行日志 | 理解 fixture |
| 第 3 天 | 读 `test_03`，自己加 3 组版本号数据 | 会写参数化 |
| 第 4 天 | **把 `adas/version.py` 里的补零那段删掉**，看哪些用例失败 | 体会"测试怎么抓 bug" |
| 第 5 天 | 给 `adas/log_analyzer.py` 加一个函数（比如"提取所有 ERROR 行"），自己写测试 | 会测新功能 |
| 第 6 天 | 改 `DEFAULT_RULES` 阈值，观察 `test_04` 的结果变化 | 理解守门标准 |
| 第 7 天 | 把 `test_04` 的规则改成从 JSON 文件读取 | 接近真实项目形态 |

**第 4 天那个练习最重要**：故意改坏产品代码，看测试能不能抓住它。
如果测试没抓住，说明你的测试有漏洞 —— 这个过程叫**变异测试**，
是检验"测试到底有没有用"的标准方法，面试里讲出来很加分。

---

## 七、面试怎么讲（这是你真正需要的）

被问"你了解自动化测试吗"，**不要背概念，讲你这套东西**：

> 我做过一个车载日志的自动化分析工具，用 pytest 写了一套用例。
> 产品代码那边把日志扫描逻辑抽成了函数，测试这边用 fixture 准备样本日志和临时目录。
> 用例覆盖三类：正常路径、异常路径（比如路径不存在要报错，而不是静默返回空列表）、
> 边界值（比如阈值是"超过才失败"还是"达到就失败"）。
> 另外我用参数化把版本号比较做成了一张数据表，包括 `1.2` 和 `1.2.0` 等价这种边界情况。
> 最后把日志分析和版本号判断串成了发版冒烟守门，跑一遍 0.2 秒出 PASS/FAIL 结论，
> 打上 `smoke` 标记，发版前只跑这一批。

这段话里有：**工具链、设计方法、异常思维、边界思维、CI 思路**。
比"我会 pytest"有信息量得多。

**可能被追问的问题**（先想好答案）：
1. fixture 的作用域有哪几种？ `function` / `class` / `module` / `package` / `session`
2. 怎么测一个会读文件的函数？ 用 `tmp_path` 造临时文件，或者把 IO 和逻辑拆开
3. 测试之间应该互相依赖吗？ 不应该，每条用例必须能独立跑、任意顺序跑
4. 怎么保证测试本身是可靠的？ 避免 flaky（比如依赖文件系统返回顺序 → 所以 `iter_log_files` 里做了 `sorted`）
5. 自动化测试覆盖率越高越好吗？ 不是，看覆盖的是不是关键路径

---

## 八、下一步可以加什么

按"离你工作最近"排序：

1. **接 CI**：用 GitHub Actions 或 GitLab CI，每次提交自动跑 `pytest`（面试高频话题）
2. **出报告**：装 `pytest-html`，`pytest --html=report.html`，生成可视化报告
3. **覆盖率**：装 `pytest-cov`，`pytest --cov=adas`，看哪一行代码没被测到
4. **从 JSON/YAML 读用例数据**：把用例数据从代码里挪到配置文件，让测试同学不用改代码就能加用例
5. **接口测试**：装 `requests`，测一个 HTTP 接口（这是测试岗面试最常见的实战题）
6. **对接真实数据格式**：把你工作里的真实日志格式（coredump、dcos_debug 输出）拿来当测试数据

---

*本示例全部用例实测通过：`72 passed, 2 skipped, 1 xfailed in 0.19s`*
*被测对象来自你原有的 `python-learn/log_analyzer.py`（原文件保留未改动）。*
