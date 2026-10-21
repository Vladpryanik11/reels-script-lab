import json
import re
import unittest
from pathlib import Path
from zipfile import ZipFile

ARCHIVE=Path('/mnt/data/reels-script-lab-universal-plugin-v0.8.1.zip')

class ReleaseArchiveV081Tests(unittest.TestCase):
    def test_new_plugin_archive_contains_separate_agents_and_validator(self):
        self.assertTrue(ARCHIVE.is_file())
        with ZipFile(ARCHIVE) as z:
            self.assertIsNone(z.testzip())
            names=set(z.namelist())
            self.assertTrue(all(n.startswith('reels-script-lab/') for n in names))
            self.assertFalse(any('__pycache__' in n or n.endswith('.pyc') for n in names))
            base='reels-script-lab/skills/reels-script-lab/'
            m=json.loads(z.read('reels-script-lab/plugin.json'))
            self.assertEqual(m['version'],'0.8.1')
            for rel in ['references/11-human-language-agent.md',
                        'references/12-hook-formula-library.md',
                        'scripts/method_voice_gate.py']:
                self.assertIn(base+rel,names)
            for n in [n for n in names if n.startswith(base) and n.endswith('.md')]:
                content=z.read(n).decode('utf-8')
                for rel in re.findall(r'`((?:references|scripts|profiles)/[a-zA-Z0-9_./-]+\.(?:md|py))`',content):
                    self.assertIn(base+rel,names,(n,rel))

if __name__=='__main__':unittest.main()
