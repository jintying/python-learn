# python-learn

Python 学习与自动化测试练习仓库。

主线是一个**车载日志关键字统计工具**（`log_analyzer.py`）：路测跑完一堆日志后，自动扫出 `error` / `warn` / `fail` 各出现多少次，省掉手工 grep。围绕这个工具，仓库里做了三层练习 —— Python 基础复习、pytest 自动化测试、以及测试工程师日常会用到的日志校验与发版冒烟。

> 所有示例都可以直接运行，不需要额外准备数据。

---

## 快速开始

```powershell
git clone git@github.com:jintying/python-learn.git
cd python-learn

# 创建虚拟环境并安装依赖
python -m venv .venv
.venv\Scripts\activate
pip install -r pytest-learn\requirements.txt
```

环境要求：Python 3.9+（本仓库在 3.14 下验证通过）。

---

## 三个子项目

| 目录 | 内容 | 适合谁 |
|---|---|---|
| `log_analyzer.py` + `sample_logs/` | 车载日志关键字统计工具，递归扫描目录、按文件统计命中次数并汇总 | 想练「用脚本解决重复劳动」 |
| `pytest-learn/` | 把上面的工具改造成可测试的 `adas` 包，配 4 组测试和一份 300 行讲义 | 想学会给功能写自动化测试 |
| `基础复习/` | 从「函数是什么」讲起的复习课，13 个可直接运行的脚本 | Python 基础不牢、卡在函数和返回值 |

---

## 目录结构

```
python-learn/
├── log_analyzer.py            日志关键字统计工具（命令行入口）
├── sample_logs/               演示日志 ×3
│
├── pytest-learn/              pytest 教学项目
│   ├── adas/                  被测代码包
│   │   ├── log_analyzer.py    重构版日志分析
│   │   ├── version.py         OTA 版本号校验（语义化版本比较）
│   │   └── smoke.py           发版冒烟检查项
│   ├── tests/                 4 组用例：基础 / 日志 / 版本 / 冒烟
│   ├── data/sample_logs/      测试专用日志
│   ├── pytest.ini             测试发现路径与默认参数
│   ├── run_tests.ps1          一键跑测试
│   └── README.md              讲义：pytest 从入门到能写
│
└── 基础复习/
    ├── 00_先看这个.md          学习路线和三句核心结论
    ├── 01 ~ 11 系列脚本        参数、return、报错阅读、f-string、自测题
    ├── run.bat                一键跑课程（双击即可）
    └── run_lessons.py         课程调度脚本
```

---

## 怎么跑

### 1. 日志分析工具

```powershell
.venv\Scripts\python.exe log_analyzer.py sample_logs error warn fail
```

输出（演示数据）：

```
日志文件                        error       warn        fail
------------------------------------------------------------------
veh_001.log                    2           2           1
veh_002.log                    1           2           1
veh_003.log                    2           2           2

===== 汇总 =====
error: 共 5 次
warn: 共 6 次
fail: 共 4 次
```

关键字可以随便换，数量不限，匹配不区分大小写。

### 2. 自动化测试

```powershell
cd pytest-learn
..\.venv\Scripts\python.exe -m pytest
```

或者用封装好的脚本（自动找上层虚拟环境）：

```powershell
.\run_tests.ps1                # 全部
.\run_tests.ps1 -m smoke       # 只跑冒烟
.\run_tests.ps1 tests\test_03_version.py   # 只跑某个文件
```

**当前结果：72 passed, 2 skipped, 1 xfailed，耗时 0.21 秒。**

其中 2 个 skipped 和 1 个 xfailed 是讲义里有意的设计，用来演示 `skip` / `xfail` 用法。

### 3. 基础复习课程

双击 `基础复习\run.bat` 直接跑，或者在终端里：

```powershell
基础复习\run.bat            # 全部
基础复习\run.bat 05         # 只跑第 05 课
基础复习\run.bat --list     # 列出所有课程
```

---

## 一点说明

- `sample_logs/` 里的日志是**构造的演示数据**，不含任何真实车辆或客户信息。
- `.venv/`、`__pycache__/`、`.pytest_cache/` 已在 `.gitignore` 中排除，不进入版本库。
- Windows 终端出现中文乱码时，先执行 `chcp 65001` 切到 UTF-8；`基础复习\run.bat` 内部已经帮你做了。
