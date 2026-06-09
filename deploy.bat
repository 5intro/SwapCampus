@echo off
chcp 65001 >nul
echo ========================================
echo   SwapCampus 一键部署脚本
echo ========================================
echo.

:: 1. 还原 .env
echo [1/5] 还原环境变量...
copy /Y "%~dp0.env" "%~dp0backend\.env" >nul
if %errorlevel% neq 0 (
    echo [错误] .env 文件不存在！请把 .env 放在脚本同目录下
    pause
    exit /b 1
)
echo   OK

:: 2. 后端依赖更新
echo [2/5] 更新后端依赖...
call "%~dp0backend\venv\Scripts\activate.bat"
pip install -r "%~dp0backend\requirements\prod.txt" -q
if %errorlevel% neq 0 (
    echo [错误] 依赖安装失败
    pause
    exit /b 1
)
echo   OK

:: 3. 数据库迁移
echo [3/5] 执行数据库迁移...
python "%~dp0backend\manage.py" migrate
if %errorlevel% neq 0 (
    echo [错误] 迁移失败
    pause
    exit /b 1
)
echo   OK

:: 4. 前端构建
echo [4/5] 构建前端（可能需要1-2分钟）...
call npm install --prefix "%~dp0frontend" --registry=https://registry.npmmirror.com -q
call npm run build --prefix "%~dp0frontend"
if %errorlevel% neq 0 (
    echo [错误] 前端构建失败
    pause
    exit /b 1
)
echo   OK

:: 5. 重启后端
echo [5/5] 重启后端服务...
taskkill /fi "WINDOWTITLE eq waitress*" /f 2>nul
start "waitress" cmd /c "cd /d %~dp0backend && call venv\Scripts\activate.bat && waitress-serve --port=8000 config.wsgi:application"
echo   OK

echo.
echo ========================================
echo   部署完成！
echo   浏览器访问 https://geleme.online
echo ========================================
echo.
pause
