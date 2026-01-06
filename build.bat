@echo off
chcp 65001 > nul
echo ==========================================
echo 会計データ可視化ダッシュボード ビルドスクリプト
echo ==========================================
echo.

REM 仮想環境のアクティベート（必要に応じてパスを変更）
REM call venv\Scripts\activate

REM PyInstallerがインストールされているか確認
pip show pyinstaller > nul 2>&1
if errorlevel 1 (
    echo PyInstallerがインストールされていません。
    echo インストールしますか？ (Y/N)
    set /p choice=
    if /i "%choice%"=="Y" (
        pip install pyinstaller
    ) else (
        echo ビルドを中止します。
        pause
        exit /b 1
    )
)

echo.
echo ビルドを開始します...
echo.

REM 既存のビルドフォルダをクリーンアップ
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM PyInstallerでビルド
pyinstaller accounting_dashboard.spec --clean

if errorlevel 1 (
    echo.
    echo ==========================================
    echo ビルドに失敗しました。
    echo ==========================================
    pause
    exit /b 1
)

echo.
echo ==========================================
echo ビルドが完了しました！
echo ==========================================
echo.
echo 出力先: dist\会計ダッシュボード\
echo.
echo 実行ファイル: dist\会計ダッシュボード\会計ダッシュボード.exe
echo.

REM README.txtをdistフォルダにコピー
if exist README_配布用.txt (
    copy README_配布用.txt dist\会計ダッシュボード\README.txt
    echo README.txtをコピーしました。
)

pause
