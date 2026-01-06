# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for 会計データ可視化ダッシュボード
"""

import sys
from pathlib import Path

block_cipher = None

# プロジェクトルート
project_root = Path(SPECPATH)

# データファイル
datas = [
    # データベースファイル
    (str(project_root / 'data' / 'accounting.db'), 'data'),
]

# 隠しインポート（自動検出されないモジュール）
hiddenimports = [
    # CustomTkinter関連
    'customtkinter',
    'CTkMessagebox',
    # matplotlib関連
    'matplotlib',
    'matplotlib.backends.backend_tkagg',
    'matplotlib.figure',
    'matplotlib.pyplot',
    # pandas関連
    'pandas',
    'pandas._libs.tslibs.base',
    # numpy関連
    'numpy',
    # sqlite関連
    'sqlite3',
    # tkinter関連
    'tkinter',
    'tkinter.ttk',
    'tkinter.filedialog',
    # PIL（CustomTkinterが使用）
    'PIL',
    'PIL._tkinter_finder',
]

a = Analysis(
    [str(project_root / 'app' / 'main.py')],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 不要なモジュールを除外（サイズ削減）
        'pytest',
        'setuptools',
        'wheel',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='会計ダッシュボード',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # コンソール非表示
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # アイコン設定（存在する場合）
    # icon=str(project_root / 'assets' / 'icon.ico'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='会計ダッシュボード',
)
