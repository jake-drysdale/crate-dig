# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(['sample_finder_SA_inter.py'],
             pathex=['.'],  # Current directory
             binaries=[],
             datas=[
                ('./traced_text_encoder_model.pt', '.'), 
                ('./traced_audio_encoder_model.pt', '.'), 
                ('./gpt2_tokenizer/', 'gpt2_tokenizer'),  # Assuming this is a directory
                ('./embeddings/embeddings_list.npy', 'embeddings'), 
                ('./embeddings/embeddings.ann', 'embeddings'), 
                ('./embeddings/path_map.json', 'embeddings')
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