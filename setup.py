from setuptools import setup

APP = ['mac_sleep_switch.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': True,
    'plist': {
        'LSUIElement': True,  # 这会让应用只显示菜单栏图标，不出现在Dock栏
        'CFBundleName': 'Mac睡眠切换器',
        'CFBundleDisplayName': 'Mac睡眠切换器',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
    },
    'packages': ['rumps', 'keyring'],
    'iconfile': 'icon.icns',
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
