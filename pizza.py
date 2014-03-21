#! /usr/bin/python
from parser import Parser
from interface import Interface
import pocketsphinx
import sys


tts = False
sr = False

for arg in sys.argv:
    if arg == '--tts':
        tts = True
    if arg == '--sr':
        sr = True

io = Interface(TTS=tts, SR=sr)
p = Parser('dialog1.vxml', io)

p.walk()





