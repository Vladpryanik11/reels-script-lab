import json
import re
import unittest
from pathlib import Path
from zipfile import ZipFile

ARCHIVE=Path('/mnt/data/reels-script-lab-universal-plugin-v0.7.0.zip')

class ReleaseArchiveTests(unittest.TestCase):
    def test_usable_and_consistent_archive(self):
        self.assertTrue(ARCHIVE.is_file())
        with ZipFile(ARCHIVE) as z:
            self.assertIsNone(z.testzip())
            names=set(z.namelist())
            self.assertTrue(all(n.startswith('reels-script-lab/') for n in names))
            m=json.loads(z.read('reels-script-lab/plugin.json'))
            self.assertEqual(m['version'],'0.7.0')
            self.assertEqual(len([n for n in names if n.endswith('/SKILL.md')]),1)
            self.assertFalse(any('__pycache__' in n or n.endswith('.pyc') for n in names))
            root='reels-script-lab/skills/reels-script-lab/'
            docs=[n for n in names if n.startswith(root) and n.endswith('.md')]
            missing=[]
            for n in docs:
                content=z.read(n).decode('utf-8')
                if n.endswith('SKILL.md'):
                    self.assertTrue(content.startswith('---\nname: reels-script-lab'))
                for ref in re.findall(r'`((?:references|scripts|profiles)/[a-zA-Z0-9_./-]+\.(?:md|py))`',content):
                    if root+ref not in names:missing.append((n,ref))
            self.assertEqual(missing,[])

if __name__=='__main__':unittest.main()
