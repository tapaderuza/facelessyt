import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('episode04_publish',ROOT/'production/04-local-memory/publish_episode.py')
pub=importlib.util.module_from_spec(spec)
spec.loader.exec_module(pub)


class Episode04PublishTests(unittest.TestCase):
    def test_public_request_is_specific_to_episode_four(self):
        body=pub.upload_body('Verified chapter description')
        self.assertEqual(body['status']['privacyStatus'],'public')
        self.assertEqual(body['snippet']['title'],"Your AI Model Fits. Your Conversation Doesn't.")
        self.assertFalse(body['status']['selfDeclaredMadeForKids'])

    def test_long_description_fails_before_api_call(self):
        with self.assertRaises(ValueError):pub.upload_body('x'*5001)

    def test_wrong_channel_stops_before_listing_uploads(self):
        yt=Mock()
        yt.channels.return_value.list.return_value.execute.return_value={'items':[{'snippet':{'title':'Other channel'}}]}
        with self.assertRaises(RuntimeError):pub.check_channel(yt)
        yt.playlistItems.assert_not_called()

    def test_changed_asset_invalidates_qa(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            report={'technical_pass':True,'checks':{'test':True},'duration_seconds':360}
            for name,key in [('04-local-memory-final.mp4','video_sha256'),('thumbnail.jpg','thumbnail_sha256'),('description.txt','description_sha256')]:
                (root/name).write_bytes(b'test fixture')
                report[key]=hashlib.sha256(b'test fixture').hexdigest()
            (root/'render-qa.json').write_text(json.dumps(report))
            with patch.object(pub,'OUT',root):
                pub.validate_assets()
                (root/'thumbnail.jpg').write_bytes(b'changed')
                with self.assertRaisesRegex(RuntimeError,'hash mismatch'):pub.validate_assets()


if __name__=='__main__':unittest.main()
