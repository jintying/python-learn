# run_tests.ps1 —— 一键跑全部自动化测试
#
# 用法（在 PowerShell 里）：
#     cd D:\Desktop\python-learn\pytest-learn
#     .\run_tests.ps1                 跑全部
#     .\run_tests.ps1 -m smoke        只跑冒烟那批
#     .\run_tests.ps1 tests/test_03_version.py   只跑某个文件

param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]] $PytestArgs
)

# 复用上层 python-learn 里已经建好的虚拟环境
$python = Join-Path $PSScriptRoot "..\.venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    Write-Host "找不到虚拟环境: $python" -ForegroundColor Red
    Write-Host "请先在 python-learn 目录里创建 .venv：python -m venv .venv" -ForegroundColor Yellow
    exit 1
}

& $python -m pytest @PytestArgs
exit $LASTEXITCODE
