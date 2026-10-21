import json
import re
import unittest
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PKG=ROOT/'reels-script-lab'
SK=PKG/'skills/reels-script-lab'

class PackagingTests(unittest.TestCase):
    def test_manifest_and_skill_valid(self):
        m=json.loads((PKG/'plugin.json').read_text('utf-8'))
        self.assertEqual(m['$schema'],'https://agent-plugins.org/schemas/1.0.0/plugin.schema.json')
        self.assertEqual(m['name'],'reels-script-lab')
        self.assertEqual(m['version'],'0.8.2')
        self.assertLessEqual(len(m['extensions']['com.openai']['interface']['shortDescription']),30)
        skill=(SK/'SKILL.md').read_text('utf-8')
        self.assertTrue(skill.startswith('---\nname: reels-script-lab\n'))
        self.assertIn('description:',skill)

    def test_every_local_reference_resolves(self):
        texts=[(SK/'SKILL.md')]+list((SK/'references').glob('*.md'))
        missing=[]
        for f in texts:
            content=f.read_text('utf-8')
            for pointer in re.findall(r'`((?:references|scripts|profiles)/[a-zA-Z0-9_./-]+\.(?:md|py))`',content):
                if not (SK/pointer).is_file():missing.append((f.name,pointer))
        self.assertEqual(missing,[])

    def test_core_has_no_profile_leak(self):
        for f in list((SK/'references').glob('*.md'))+[(SK/'SKILL.md')]:
            content=f.read_text('utf-8').casefold()
            for forbidden in ('ирина', 'гоголаури','кпт','психологическ'):
                self.assertNotIn(forbidden,content,(str(f),forbidden))

    def test_single_plugin_no_unsafe_installation(self):
        self.assertFalse((PKG/'mcp.json').exists())
        self.assertFalse((PKG/'.app.json').exists())
        self.assertEqual(len(list((PKG/'skills').glob('*/SKILL.md'))),1)

if __name__=='__main__':unittest.main()
