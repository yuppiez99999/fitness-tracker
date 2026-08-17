@echo off
chcp 65001 >nul 2>&1
REM ══════════════════════════════════════════════════════════════
REM  体脂体重监控 v8.0 — 双击启动脚本
REM  解决 Windows 下 python 因 .pth(G特征BK) 编码问题无法启动的坑
REM ══════════════════════════════════════════════════════════════

REM 跳过用户 site-packages 中可能含非 ASCII 字符导致 GBK 解码失败的 .pth
set PYTHONUSERBASE=C:\NUL
set PYTHONIOENCODING=utf-8

REM 切换到脚本所在目录(保证数据文件相对路径正确)
cd /d "%~dp0"

REM 优先使用系统 Python 3.8
set PY="C:\Program Files\Python38\python.exe"
if not exist %PY% (
    set PY=python
)

REM 启动 GUI
start "" %PY% "%~dp0体脂体重监控_完整版.py"
