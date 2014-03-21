from __future__ import print_function
from time import sleep
import gobject
import pygst
gobject.threads_init()
import gst
import pyttsx



class Interface(object): 
    def __init__(self, SR, TTS):
        if TTS:
            self.output = TTSOut()
        else:
            self.output = DummyOut()
        if SR:
            self.input = Asr()
        else:
            self.input = DummyIn()

class TTSOut(object):
    def __init__(self):
        self.engine = pyttsx.init()
        self.engine.rate = 150
    def __call__(self, s):
        s.strip()
        self.engine.say(s)
    def flush(self):
        self.engine.runAndWait()
class DummyOut(object):
    def __call__(self, s):
        print (s)
    def flush(self):
        pass

class DummyIn(object):
    def read(self):
        return raw_input('')

class Asr(object):
    def __init__(self):
        self.pipeline = gst.parse_launch('gconfaudiosrc ! audioconvert ! audioresample '
                                         + '! vader name=vad auto_threshold=true '
                                         + '! pocketsphinx name=asr ! fakesink')
        asr = self.pipeline.get_by_name('asr')
        asr.connect('partial_result', self.asr_partial_result)
        asr.connect('result', self.asr_result)
        asr.set_property('configured', True)
        asr.set_property('fsg', 'pizza.fsg')
        asr.set_property('dict', 'pizza.dict')
        self.placeHolder = ''
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect('message::application', self.application_message)
        self.pipeline.set_state(gst.STATE_PAUSED)
    def read(self):
        self.pipeline.set_state(gst.STATE_PLAYING)
        sleep(8)
        return self.placeHolder.lower()
    def asr_partial_result(self, asr, text, uttid):
        # Ignore partials.
        struct = gst.Structure('partial_result')
        struct.set_value('hyp', text)
        struct.set_value('uttid', uttid)
        asr.post_message(gst.message_new_application(asr, struct))
        

    def asr_result(self, asr, text, uttid):
        self.placeHolder = text
        struct = gst.Structure('result')
        struct.set_value('hyp', text)
        struct.set_value('uttid', uttid)
        asr.post_message(gst.message_new_application(asr, struct))

    def application_message(self, bus, msg):        
        msgtype = msg.structure.get_name()
        if msgtype == 'partial_result':
            self.partial_result(msg.structure['hyp'], msg.structure['uttid'])
        elif msgtype == 'result':
            self.final_result(msg.structure['hyp'], msg.structure['uttid'])
            self.pipeline.set_state(gst.STATE_PAUSED)
            self.button.set_active(False)

