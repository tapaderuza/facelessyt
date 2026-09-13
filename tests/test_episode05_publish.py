import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('episode05_publish', ROOT / 'production/05-worker-bottleneck/publish_episode.py')
pub = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pub)


class Episode05PublishTests(unittest.TestCase):
    def test_public_request_is_specific_to_episode_five(self):
        body = pub.upload_body('Verified chapters')
        self.assertEqual(body['status']['privacyStatus'], 'public')
        self.assertEqual(body['snippet']['title'], "I Doubled the Workers. The Bottleneck Didn't Move.")

    def test_wrong_channel_stops_before_listing_uploads(self):
        yt = Mock()
        yt.channels.return_value.list.return_value.execute.return_value = {'items': [{'snippet': {'title': 'Other channel'}}]}
        with self.assertRaises(RuntimeError):
            pub.check_channel(yt)
        yt.playlistItems.assert_not_called()

    def test_long_description_rejected(self):
        with self.assertRaises(ValueError):
            pub.upload_body('x' * 5001)

    def test_release_requires_matching_assets_external_thumbnail_and_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = {'technical_pass': True, 'checks': {'test': True}, 'duration_seconds': 231}
            for name, key in [('05-worker-bottleneck-final.mp4', 'video_sha256'), ('thumbnail.jpg', 'thumbnail_sha256'), ('description.txt', 'description_sha256')]:
                (root / name).write_bytes(b'test fixture')
                report[key] = hashlib.sha256(b'test fixture').hexdigest()
            (root / 'render-qa.json').write_text(json.dumps(report))
            provenance = {'generated_by_renderer': False, 'sha256': report['thumbnail_sha256']}
            (root / 'thumbnail-provenance.json').write_text(json.dumps(provenance))
            approval = {'approved': True, 'video_sha256': report['video_sha256'], 'thumbnail_sha256': report['thumbnail_sha256']}
            with patch.object(pub, 'OUT', root):
                with self.assertRaises(FileNotFoundError):
                    pub.validate_assets()
                (root / 'visual-review.json').write_text(json.dumps(approval))
                pub.validate_assets()
                provenance['generated_by_renderer'] = True
                (root / 'thumbnail-provenance.json').write_text(json.dumps(provenance))
                with self.assertRaisesRegex(RuntimeError, 'provenance'):
                    pub.validate_assets()
                (root / 'thumbnail.jpg').write_bytes(b'changed')
                with self.assertRaisesRegex(RuntimeError, 'hash mismatch'):
                    pub.validate_assets()


if __name__ == '__main__':
    unittest.main()
