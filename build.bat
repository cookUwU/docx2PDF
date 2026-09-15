@echo off
chcp 65001 >nul 2>&1
REM 把 Word2PDF 打包成独立的 exe（双击即用，无需 Python 环境）
REM 自动查找本机已安装的 Python，不依赖系统 PATH。

set "PYTHON_EXE="
REM 1. 常见安装路径（按优先级排列）
for %%p in (
    "%LOCALAPPDATA%\Programs\Python\python.exe"
    "%LOCALAPPDATA%\Programs\Python3*\python.exe"
    "C:\Program Files\Python*\python.exe"
    "C:\Program Files (x86)\Python*\python.exe"
    "D:\Program Files\Python*\python.exe"
    "D:\Program Files (x86)\Python*\python.exe"
    "D:\Python*\python.exe"
) do (
    if exist %%~dpf set "PYTHON_EXE=%%~dpf" && goto :found_python
)

REM 2. 尝试 PATH 中的 python（排除 WindowsApps 占位符）
where /r "%LOCALAPPDATA%" python.exe >nul 2>&1 && for /f "delims=" %%a in ('where /r "%LOCALAPPDATA%" python.exe 2^>nul ^| findstr /v WindowsApps') do if not defined PYTHON_EXE set "PYTHON_EXE=%%a"

:found_python
if not defined PYTHON_EXE (
    echo.
    echo [错误] 未找到 Python！请先安装：
    echo   https://www.python.org/downloads/
    echo.
    echo 安装时务必勾选 "Add Python to PATH"。
    pause
    exit /b 1
)

echo [OK] 找到 Python：%PYTHON_EXE%
%PYTHON_EXE% --version

echo.
echo [1/4] 创建虚拟环境...
"%PYTHON_EXE%" -m venv venv
if errorlevel 1 (
    echo [警告] venv 创建失败，尝试直接使用当前 Python 进行打包...
    goto :skip_venv
)
call venv\Scripts\activate

:skip_venv
echo [2/4] 安装 pyinstaller...
pip install --upgrade pip pyinstaller

echo [3/4] 开始打包（可能需要 1-2 分钟）...
pyinstaller --onefile --windowed --name Word2PDF main.py
if errorlevel 1 (
    echo.
    echo [错误] 打包失败，请检查上面的错误信息。
    pause
    exit /b 1
)

echo.
echo [4/4] 清理临时文件...
if exist dist\Word2PDF.exe rmdir /s /q build spec 2>nul

echo ========================================
echo   打包完成！
echo   exe 位于: %cd%\dist\Word2PDF.exe
echo ========================================
pause
