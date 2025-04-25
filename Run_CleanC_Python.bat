@echo off
chcp 936 >nul
title 启动 C盘清理工具 (Python版)

echo 正在以管理员权限启动 Python 清理脚本...
echo.

:: 检查 Python 是否可用
python --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo 错误：未找到 Python 环境！
    echo 请确保已正确安装 Python 并将其添加到了系统 PATH 环境变量。
    echo 您可以从 python.org 下载并安装。
    echo.
    echo 按任意键退出...
    pause >nul
    exit /b 1
)

:: 获取当前批处理文件所在的目录
set SCRIPT_DIR=%~dp0

:: 运行 Python 脚本
python "%SCRIPT_DIR%CleanC_v2_EnhancedUI.py"

if %errorlevel% neq 0 (
    color 0C
    echo.
    echo Python 脚本执行出错！请检查脚本内容或错误信息。
    echo.
)

echo.
echo 脚本执行完毕。
echo 按任意键退出此启动器...
pause >nul
exit /b %errorlevel% 