"""Regression guardrails for the native, decorative SVG animation."""
from fractions import Fraction
import json
from pathlib import Path
import re
import sys
import unittest
from xml.etree import ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from questlog_art import render

NS={'s':'http://www.w3.org/2000/svg'}

class AnimationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads((ROOT/'assets/questlog-data.json').read_text())
        cls.svg=render(cls.data)
        cls.root=ET.fromstring(cls.svg)
        cls.css=cls.root.find('s:style',NS).text

    def test_native_self_contained_svg(self):
        ids=[]
        for node in self.root.iter():
            self.assertNotIn(node.tag.rsplit('}',1)[-1],('script','foreignObject','image'))
            if 'id' in node.attrib:ids.append(node.attrib['id'])
            for attr,value in node.attrib.items():
                self.assertFalse(attr.lower().startswith('on'))
                if attr.rsplit('}',1)[-1]=='href':self.assertTrue(value.startswith('#'))
        self.assertEqual(len(ids),len(set(ids)))
        self.assertNotRegex(self.css,r'@import|url\((?!#)')

    def test_data_and_ui_have_no_animated_ancestors_or_descendants(self):
        def walk(node,moving=False):
            moving=moving or 'motion' in node.get('class','').split()
            if 'data-date' in node.attrib or node.get('id')=='quest-log':
                self.assertFalse(moving)
                self.assertTrue(all('motion' not in n.get('class','').split() for n in node.iter()))
            for child in node:walk(child,moving)
        walk(self.root)
        cells=self.root.findall('.//s:g[@data-date]',NS)
        self.assertEqual(len(cells),182)
        self.assertEqual({c.get('data-date'):int(c.get('data-count')) for c in cells},
                         {d['date']:d['count'] for d in self.data['last26Weeks']})

    def test_all_motion_has_bounded_cycle_and_reduced_motion_fallback(self):
        motions=[n for n in self.root.iter() if 'motion' in n.get('class','').split()]
        self.assertEqual(len(motions),9)
        self.assertIn('@media (prefers-reduced-motion: no-preference)',self.css)
        self.assertIn('@media (prefers-reduced-motion: reduce)',self.css)
        self.assertIn('.motion { animation: none !important; }',self.css)
        self.assertIn('.transient { opacity: 0; }',self.css)
        for cls,seconds in re.findall(r'\.([\w-]+) \{ animation: [\w-]+ ([\d.]+)s',self.css):
            self.assertGreaterEqual(float(seconds),3.6)
            self.assertEqual((Fraction('14.4')/Fraction(seconds)).denominator,1)
        for node in motions:
            self.assertRegex(self.css,r'\.'+node.get('class').split()[-1]+r' \{ animation:')

    def test_rotating_and_scaling_parts_use_local_fixed_pivots(self):
        pivots=self.root.findall('.//s:g[@data-motion-pivot]',NS)
        self.assertEqual(len(pivots),7)
        for outer in pivots:
            animated=list(outer)[0]
            geometry=list(animated)[0]
            self.assertIn('motion',animated.get('class').split())
            self.assertNotIn('transform',animated.attrib)
            a=list(map(float,re.findall(r'-?[\d.]+',outer.get('transform'))))
            b=list(map(float,re.findall(r'-?[\d.]+',geometry.get('transform'))))
            self.assertEqual([x+y for x,y in zip(a,b)],[0,0])
        self.assertIn('transform-origin: 0px 0px',self.css)

if __name__=='__main__':unittest.main()
