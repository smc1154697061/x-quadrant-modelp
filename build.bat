@echo off
REM ===================================
REM PyInstaller 打包脚本 (Windows)
REM ===================================

echo [1/5] 清理旧的打包文件...
if exist "dist" rd /s /q dist
if exist "build" rd /s /q build
if exist "*.spec" del /q *.spec

echo [2/5] 检查依赖...
pip install pyinstaller
if %errorlevel% neq 0 (
    echo 错误: 安装 PyInstaller 失败
    pause
    exit /b 1
)

echo [3/5] 开始打包...
pyinstaller build_spec.py --clean --noconfirm
if %errorlevel% neq 0 (
    echo 错误: 打包失败
    pause
    exit /b 1
)

echo [4/5] 创建运行目录...
if not exist "dist\runtime" mkdir "dist\runtime"
if not exist "dist\runtime\data" mkdir "dist\runtime\data"
if not exist "dist\runtime\logs" mkdir "dist\runtime\logs"

REM 复制必要的文件
echo [5/5] 复制配置文件...
xcopy /E /I /Y "data" "dist\runtime\data"
if exist "logs" xcopy /E /I /Y "logs" "dist\runtime\logs"

echo.
echo ===================================
echo 打包完成！
echo ===================================
echo.
echo 可执行文件位置: dist\x-quadrant-modelp.exe
echo 运行目录: dist\runtime\
echo.
echo 部署到服务器:
echo 1. 将 dist\x-quadrant-modelp.exe 上传到服务器
echo 2. 将 dist\runtime\ 目录上传到服务器
echo 3. 在服务器上运行: x-quadrant-modelp.exe
echo.
pause

