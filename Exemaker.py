# -*- coding: utf-8 -*-
"""
Created on Sat Sep 20 20:42:27 2025

@author: mutlu
"""

# önce "pip install pyinstaller" yazarak  indir 
# çevirmek istediğin dosya ile aynı konumda çalıstır
import PyInstaller.__main__


PyInstaller.__main__.run([
    "VDMr.py",                              # bu çevireceğin py dosyası için
    "--clean",                              # bu daha önce yaptıysan eski verileri siliyor
    "--onefile",                            # tek dosya yapmanı sağlıyor
    "--noconsole",                          # arkada cmd ekrabaı olmasın diye
    "--name=Video Download Manager",         # çevirdikten sonra uygulama adı 
    "--icon=icon.ico",                   # icon yüklemek için 
    "--add-data=icon.png:.",             # uygulama içinde icon kullandıysan 
    ])