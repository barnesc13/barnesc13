"""Regression guardrails for the native, decorative SVG animation."""
from fractions import Fraction
import json
import math
from pathlib import Path
import re
import sys
import unittest
from xml.etree import ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from questlog_art import render, MOTION_TRACKS

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
        self.assertEqual(len(motions),16)
        self.assertIn('@media (prefers-reduced-motion: no-preference)',self.css)
        self.assertIn('@media (prefers-reduced-motion: reduce)',self.css)
        self.assertIn('.motion { animation: none !important; }',self.css)
        self.assertIn('.transient { opacity: 0; }',self.css)
        for cls,seconds in re.findall(r'\.([\w-]+) \{ animation: [\w-]+ ([\d.]+)s',self.css):
            self.assertGreaterEqual(float(seconds),1.2)
            self.assertEqual((Fraction('7.2')/Fraction(seconds)).denominator,1)
        for node in motions:
            self.assertRegex(self.css,r'\.'+node.get('class').split()[-1]+r' \{ animation:')

    def test_rotating_and_scaling_parts_use_local_fixed_pivots(self):
        pivots=self.root.findall('.//s:g[@data-motion-pivot]',NS)
        self.assertEqual(len(pivots),12)
        for outer in pivots:
            animated=list(outer)[0]
            geometry=list(animated)[0]
            self.assertIn('motion',animated.get('class').split())
            self.assertNotIn('transform',animated.attrib)
            a=list(map(float,re.findall(r'-?[\d.]+',outer.get('transform'))))
            b=list(map(float,re.findall(r'-?[\d.]+',geometry.get('transform'))))
            self.assertEqual([x+y for x,y in zip(a,b)],[0,0])
        self.assertIn('transform-origin: 0px 0px',self.css)


    def test_every_track_uses_explicit_held_poses(self):
        self.assertNotRegex(self.css, r'ease|cubic-bezier|linear')
        for name, track in MOTION_TRACKS.items():
            self.assertIn(f'quest-{name} {track["duration"]:g}s steps(1,end) infinite',self.css)
            poses=track['poses']
            self.assertEqual(poses[0][0],0)
            self.assertEqual(poses[-1][0],track['duration'])
            self.assertEqual(poses[0][1:],poses[-1][1:])
            for earlier,later in zip(poses,poses[1:]):
                self.assertGreaterEqual(round(later[0]-earlier[0],6),.09)
            for _,transform,opacity in poses:
                self.assertTrue(0<=opacity<=1)
                self.assertNotRegex(transform,r'nan|inf')

    def test_hammer_shaft_passes_through_glove_and_head_stays_separate(self):
        arm=next(n for n in self.root.iter() if n.get('class')=='motion smith-arm')
        tool=arm.find('.//s:g[@id="smith-hammer"]',NS)
        hand=arm.find('.//s:path[@data-hand-grip]',NS)
        self.assertIsNotNone(tool)
        self.assertIsNotNone(hand)
        self.assertEqual(tool.get('data-local-grip'),'0 0')
        self.assertEqual(hand.get('data-hand-grip'),'-29 -53')
        self.assertEqual(tool.get('transform'),'translate(-29 -53) rotate(-27)')
        handle=tool.find('s:path[@data-part="handle"]',NS)
        self.assertEqual(handle.get('d'),'M0 5V-29')
        head=tool.find('s:path[@data-part="head"]',NS)
        coordinates=list(map(float,re.findall(r'-?[\d.]+',head.get('d'))))
        vertices=list(zip(coordinates[::2],coordinates[1::2]))
        # Entire steel head lies at least 23 local units beyond the grip.
        self.assertTrue(all(y<=-23 for x,y in vertices))
        self.assertGreaterEqual(min(math.hypot(x,y) for x,y in vertices),23)

    def test_hammer_contact_pose_reaches_hot_blank(self):
        def rotate(point,origin,angle):
            x,y=point[0]-origin[0],point[1]-origin[1]
            c=math.cos(math.radians(angle));s=math.sin(math.radians(angle))
            return origin[0]+c*x-s*y,origin[1]+s*x+c*y
        def angle_at(name,time):
            values=[v for t,v,o in MOTION_TRACKS[name]['poses'] if t<=time]
            return float(re.search(r'-?[\d.]+',values[-1])[0])
        tool=self.root.find('.//s:g[@id="smith-hammer"]',NS)
        head=tool.find('s:path[@data-part="head"]',NS)
        numbers=list(map(float,re.findall(r'-?[\d.]+',head.get('d'))))
        points=[]
        for point in zip(numbers[::2],numbers[1::2]):
            x,y=rotate(point,(0,0),-27)
            p=rotate((x-29,y-53),(-17,-45),angle_at('smith-arm',.6))
            x,y=rotate(p,(0,-5),angle_at('smith-body',.6))
            points.append((555+1.27*x,804+1.27*y))
        contact=max(points,key=lambda p:p[1])
        self.assertTrue(477<=contact[0]<=497,contact)
        self.assertTrue(797<=contact[1]<=801,contact)
        self.assertIsNotNone(self.root.find('.//s:path[@id="smith-hot-blank"]',NS))

    def test_woodcut_strike_reaches_willow_bark(self):
        actor=self.root.find('.//s:g[@id="woodcutter"]',NS)
        self.assertEqual(actor.get('transform'),'translate(425 242) scale(1.04)')
        # The bright leading edge of the axe must meet the existing willow trunk.
        angle=math.radians(-38);c,s=math.cos(angle),math.sin(angle)
        points=[]
        for x,y in [(-46,-65),(-49,-58)]:
            dx,dy=x+11,y+35
            px,py=-11+c*dx-s*dy,-35+s*dx+c*dy
            points.append((425+1.04*px-38,242+1.04*py))
        self.assertTrue(all(327<=x<=331 and 200<=y<=214 for x,y in points),points)

    def test_woodcut_reference_holds_and_wizard_cast_reset(self):
        poses=MOTION_TRACKS['woodcut-swing']['poses']
        raised=next(i for i,p in enumerate(poses) if p[1]=='rotate(28deg)')
        strike=next(i for i,p in enumerate(poses) if p[1]=='rotate(-38deg)')
        self.assertAlmostEqual(poses[raised+1][0]-poses[raised][0],.18)
        self.assertAlmostEqual(poses[strike+1][0]-poses[strike][0],.24)
        wizard=MOTION_TRACKS['wizard-cast']['poses']
        held=next(i for i,p in enumerate(wizard) if p[1]=='rotate(100deg)')
        self.assertAlmostEqual(wizard[held+1][0]-wizard[held][0],2.7)
        self.assertEqual(wizard[held+1][1],'rotate(0deg)')

if __name__=='__main__':unittest.main()

