@echo off
chcp 65001 >nul 2>&1
REM ══════════════════════════════════════════════════════════════
REM  体脂体重监控 v9.0 — 双击启动脚本
REM  解决 Windows 下 python 因 .pth(GBK) 编码问题无法启动的坑
REM  v3.0 GUI解析版: 启动菜单（默认 GUI，可选打开居家平替训练计划）
REM  v3.0.1 增补: 海豹徒手 + 囚徒健身(CC) 两大补位体系已并入计划文档
REM ══════════════════════════════════════════════════════════════

REM 跳过用户 site-packages 中可能含非 ASCII 字符导致 GBK 解码失败的 .pth
set PYTHONUSERBASE=C:\NUL
set PYTHONIOENCODING=utf-8

REM 切换到脚本所在目录(保证数据文件相对路径正确)
cd /d "%~dp0"

REM 居家平替计划 Markdown 路径(相对脚本目录)
REM 注意: v3.0 实际文件名为 *_GUI解析.md, 与代码 fitness_modules.PLAN_MD 保持一致
set PLAN_MD=%~dp0体重体脂监控\居家平替计划_v3.0_单杠哑铃版_GUI解析.md

REM ══════════════════════════════════════════════════════════════
REM  启动菜单: 5 秒不选默认启动 GUI
REM ══════════════════════════════════════════════════════════════
echo.
echo ═══════════════════════════════════════════════════════
echo  体脂体重监控 v9.0 — 启动菜单
echo ═══════════════════════════════════════════════════════
echo  [1] 启动监控 GUI （默认，5 秒后自动启动）
echo  [2] 打开居家平替训练计划（单杠+哑铃版 v3.0 GUI解析版）
echo       主线: 单杠+哑铃 6练1休 22周三阶段周期化
echo       补位: 海豹徒手(Navy SEAL) + 囚徒健身(CC) 两大体系
echo  [3] 退出
echo ═══════════════════════════════════════════════════════
choice /c 123 /n /t 5 /d 1 /m "请选择 [1/2/3]: "
if errorlevel 3 goto :eof
if errorlevel 2 goto open_plan
goto start_gui

:start_gui
REM 优先使用系统 Python 3.8
set PY="C:\Program Files\Python38\python.exe"
if not exist %PY% (
    set PY=python
)

REM 启动 GUI
start "" %PY% "%~dp0体脂体重监控_完整版.py"
goto :eof

:open_plan
REM 用默认关联程序打开 Markdown（Typora / VSCode / 浏览器等）
if not exist "%PLAN_MD%" (
    echo [错误] 找不到平替计划文件:
    echo   %PLAN_MD%
    pause
    goto :eof
)
start "" "%PLAN_MD%"
goto :eof
