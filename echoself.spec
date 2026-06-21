# PyInstaller spec - build EchoSelf into a standalone desktop app.
#
# run from the echoself/ dir:   pyinstaller echoself.spec
# the build lands in dist/EchoSelf/ ; ship that whole folder. user data is written
# to %APPDATA%/EchoSelf (or ~/.local/share/EchoSelf), so it survives between runs
# and isn't lost in the bundle.
#
# this builds the OFFLINE app. the optional layers (the api-key voice, the local
# transformer, the webcam mirror, the voice) are deliberately left out so the build
# stays small - a user who wants them installs the matching requirements and runs
# from source. see the requirements-*.txt files.

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    # the read-only content the app loads at runtime, bundled at the same relative
    # paths core/paths.resource_root() expects
    datas=[
        ('lessons', 'lessons'),
        ('characters', 'characters'),
        ('exchange', 'exchange'),
        ('arcs', 'arcs'),
        ('frontend', 'frontend'),
    ],
    # sklearn is imported lazily (inside the brain's wake), so PyInstaller can't see
    # it by following imports - name it here, with matplotlib for the charts
    hiddenimports=[
        'sklearn.pipeline', 'sklearn.preprocessing', 'sklearn.linear_model',
        'sklearn.utils._cython_blas', 'scipy.special.cython_special',
    ],
    hookspath=[],
    runtime_hooks=[],
    # keep the heavy opt-in layers out of the offline build
    excludes=['torch', 'transformers', 'mediapipe', 'cv2', 'vosk', 'piper',
              'sounddevice', 'anthropic'],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='EchoSelf',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,        # a windowed app - flip to True to see errors while debugging
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name='EchoSelf',
)
