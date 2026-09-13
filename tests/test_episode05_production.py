import importlib.util
from pathlib import Path
import unittest

PACKAGE=Path(__file__).resolve().parents[1]/'production/05-worker-bottleneck'
spec=importlib.util.spec_from_file_location('ep05_produce',PACKAGE/'produce.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)


class ProductionTests(unittest.TestCase):
    def test_phrases_preserve_text(self):
        text="I just doubled the workers from 4 to 8. Does the processing speed double, or does the system choke? Lock in your guess."
        self.assertEqual(' '.join(p.phrases(text)),text)
        self.assertTrue(all(len(s)<=90 for s in p.phrases(text)))

    def test_three_ticks_and_three_seconds(self):
        from array import array
        rate=22050;pcm=array('h');pcm.frombytes(p.tick_pcm(rate))
        self.assertEqual(len(pcm),3*rate)
        for i in range(3):
            self.assertTrue(any(pcm[i*rate:i*rate+round(rate*.07)]))
            self.assertFalse(any(pcm[i*rate+round(rate*.07):(i+1)*rate]))

    def test_silence_cannot_be_accepted_as_speech(self):
        with self.assertRaises(ValueError):p.trim_pcm(b'\0\0'*22050,22050)

    def test_timecodes(self):
        self.assertEqual(p.srt_time(61.25),'00:01:01,250')


if __name__=='__main__':unittest.main()
