# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec：象胥 独立可执行（目录模式，便于兼容 PyAudio/自定义资源）

import os
from PyInstaller.utils.hooks import collect_data_files

# CustomTkinter 的 .json、.otf 等需一并打包
_ctk_datas = collect_data_files("customtkinter")
# certifi 的 cacert.pem，打包后 SSL 验证需要
_certifi_datas = collect_data_files("certifi")

# 项目资源：模板与图片（运行时从 RESOURCES_DIR / _MEIPASS 读取）
_app_datas = [
    (".env.example", "."),
    ("config.json.example", "."),
    ("images", "images"),
]

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=_ctk_datas + _certifi_datas + _app_datas,
    hiddenimports=[
        "certifi",
        "customtkinter",
        "PIL",
        "PIL._tkinter_finder",
        "PIL.Image",
        "dotenv",
        "websockets",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

# 图标使用基于 spec 所在目录的绝对路径，避免 cwd 导致找不到文件
_spec_dir = os.path.dirname(os.path.abspath(SPEC))
_icon_path = os.path.join(_spec_dir, "images", "logo.ico")

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="象胥",
    icon=_icon_path,  # 由 build.bat 从 images/logo.jpg 生成
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,  # 保留控制台便于看报错；打成正式版可改为 False
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="象胥",
)
