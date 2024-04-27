# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(['crateDigUI.py', 'utils/playlist.py', 'sample_finder_SA_inter.py', 'app.py'],
             pathex=['.'],  # Current directory
             binaries=[],
             datas=[
                ('./UserLibrary/models/traced_text_encoder_model.pt', 'UserLibrary/models'), 
                ('./UserLibrary/models/traced_audio_encoder_model.pt', 'UserLibrary/models'), 
                ('./gpt2_tokenizer/', 'gpt2_tokenizer'),
                ('./UserLibrary/embeddings/macsamples/embeddings_list.npy', 'UserLibrary/embeddings/macsamples/'), 
                ('./UserLibrary/embeddings/macsamples/embeddings.ann', 'UserLibrary/embeddings/macsamples/'), 
                ('./UserLibrary/embeddings/macsamples/path_map.json', 'UserLibrary/embeddings/macsamples/'), 
                ('./UserLibrary/playlists/', 'UserLibrary'),
                ('./UserLibrary/state/', 'UserLibrary'),
                ('./ableton.json', '.'),  # Place in the root of the dist folder
                ('./theme.json', '.'),
                ('./assets/logo.png', 'assets'),
                ('./assets/logo_purple.png', 'assets')
             ],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

pyz = PYZ(a.pure, a.zipped_data,
          cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='sample_finder',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=True )
