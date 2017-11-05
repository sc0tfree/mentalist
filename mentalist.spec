# -*- mode: python -*-

'''
PyInstaller build specification for building a stand-alone application
on the current platform
'''

import sys

block_cipher = None


a = Analysis(['pyinstaller_stub.py'],
             pathex=['.'],
             binaries=[],
             datas=[ ('mentalist/data/*.txt', 'mentalist/data' ),
                     ('mentalist/data/*.psv', 'mentalist/data' ),
                     ('mentalist/icons/*.gif', 'mentalist/icons') ],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='Mentalist' + ('.exe' if sys.platform == 'win32' else ''),
          debug=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=False,
          icon='mentalist/icons/mentalist_icon.ico' )

if sys.platform == 'darwin':
    app = BUNDLE(exe,
                 name='Mentalist.app',
                 icon='mentalist/icons/Mentalist-Icon-mac.icns',
                 info_plist={'NSHighResolutionCapable': 'True'},
                 bundle_identifier=None)
    
