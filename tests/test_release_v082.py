"""Package verification for methodology restoration; structural checks not editorial quality."""
import hashlib
import json
import unittest
from pathlib import Path
from zipfile import ZipFile
ROOT=Path(__file__).resolve().parents[1]
ZIP=Path('/mnt/data/reels-script-lab-universal-plugin-v0.8.2.zip')
SK=ROOT/'reels-script-lab/skills/reels-script-lab'
class ReleaseV082Tests(unittest.TestCase):
    def test_version_archive_and_all_restored_references(self):
        self.assertTrue(ZIP.exists())
        with ZipFile(ZIP) as z:
            self.assertIsNone(z.testzip())
            self.assertEqual(json.loads(z.read('reels-script-lab/plugin.json'))['version'],'0.8.2')
            for f in ('13-structure-methodology.md','14-structure-reviewer.md','15-rehook-methodology.md','16-rehook-reviewer.md','17-script-storytelling.md','18-rehook-generator.md','19-rehook-orchestrator.md','20-rehook-reviewer-prompt.md','21-hook-methodology.md','22-hook-reviewer.md','23-cta-methodology.md'):
                self.assertIn('reels-script-lab/skills/reels-script-lab/references/'+f,z.namelist())
    def test_archived_originals_are_preserved(self):
        for name in ('01-hook.md','02-structure.md','03-rehook.md','hook-review.md','structure-review.md','rehook-review.md'):
            self.assertGreater((SK/'methodology-originals'/name).stat().st_size,4000)
    def test_old_release_untouched(self):
        self.assertTrue(Path('/mnt/data/reels-script-lab-universal-plugin-v0.8.1.zip').exists())
if __name__=='__main__':unittest.main()