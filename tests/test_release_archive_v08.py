import json
import re
import unittest
from pathlib import Path
from zipfile import ZipFile

ARCHIVE=Path('/mnt/data/reels-script-lab-universal-plugin-v0.8.0.zip')

class ReleaseArchiveV08Tests(unittest.TestCase):
    def test_archive_plugin_consistent(self):
        self.assertTrue(ARCHIVE.is_file())
        with ZipFile(ARCHIVE) as z:
            self.assertIsNone(z.testzip())
            names=set(z.namelist())
            self.assertTrue(all(n.startswith('reels-script-lab/') for n in names))
            self.assertFalse(any('__pycache__' in n or n.endswith('.pyc') for n in names))
            base='reels-script-lab/skills/reels-script-lab/'
            m=json.loads(z.read('reels-script-lab/plugin.json'))
            self.assertEqual(m['version'],'0.8.0')
            self.assertIn(base+'references/10-live-integration.md',names)
            self.assertIn(base+'scripts/integration_gate.py',names)
            for name in [n for n in names if n.startswith(base) and n.endswith('.md')]:
                contents=z.read(name).decode('utf-8')
                for rel in re.findall(r'`((?:references|scripts|profiles)/[a-zA-Z0-9_./-]+\.(?:md|py))`',contents):
                    self.assertIn(base+rel,names,(name,rel))

if __name__=='__main__':unittest.main()
