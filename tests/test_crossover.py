"""Fast, offline integration checks for the approved crossover illustration."""
import json
import math
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from xml.etree import ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from questlog_art import render, render_base
from crossover import apply, TRACKS
from crossover import adventurers_motion as am
from crossover import companions_motion as cm
from crossover import chest_motion as chest
from crossover.adventurers import sprites
from generate_questlog import summarize, validate_svg
NS={'s':'http://www.w3.org/2000/svg'}

def pose(track,t):
    value=track['poses'][0]
    for p in track['poses']:
        if p[0]<=t+1e-9:value=p
    return value[1:]

class CrossoverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads((ROOT/'assets/questlog-data.json').read_text())
        cls.base=ET.fromstring(render_base(cls.data))
        cls.svg=render(cls.data)
        cls.root=ET.fromstring(cls.svg)

    def test_all_eleven_visitors_and_approved_placements(self):
        expected={'preview-trainer':'translate(397 657) scale(0.84)',
          'preview-mudkip':'translate(492 654) scale(0.79)',
          'preview-naruto':'translate(873 842) scale(1.02)',
          'crossover-gon':'translate(1017 169) scale(0.96)',
          'crossover-killua':'translate(949 187) scale(0.96)',
          'crossover-link':'translate(797 279) scale(1)',
          'crossover-alexander':'translate(167 823) scale(1)',
          'crossover-nessie':'translate(1244 111) scale(0.9)',
          'crossover-murloc':'translate(1172 160) scale(0.9)',
          'crossover-creeper':'translate(62 581) scale(1)',
          'crossover-chao':'translate(559 650) scale(0.85)'}
        for name,transform in expected.items():
            node=self.root.find(f'.//s:g[@id="{name}"]',NS)
            self.assertIsNotNone(node,name)
            self.assertEqual(node.get('transform'),transform,name)
        self.assertEqual(self.root.get('viewBox'),'0 0 1400 1000')
        self.assertIsNotNone(self.root.find('.//s:g[@id="crossover-scene"]',NS))
        self.assertNotIn('data-preview-only',self.svg)
        self.assertNotIn('Private',self.root.find('s:title',NS).text)

    def test_data_ui_and_original_animation_are_preserved(self):
        for q in ['.//s:g[@data-date]','.//s:g[@id="quest-log"]']:
            self.assertEqual([ET.tostring(n) for n in self.base.findall(q,NS)],
                             [ET.tostring(n) for n in self.root.findall(q,NS)])
        self.assertEqual(ET.tostring(self.base.find('s:style',NS)),ET.tostring(self.root.find('s:style',NS)))
        validate_svg(self.svg,self.data)

    def test_fresh_changed_counts_are_never_replaced_by_preview_data(self):
        changed=json.loads(json.dumps(self.data))
        changed['last26Weeks'][0]['count']+=101
        changed['requestedWindow']=summarize(changed['last26Weeks'])
        result=render(changed);validate_svg(result,changed)
        actual=ET.fromstring(result);expected=ET.fromstring(render_base(changed))
        self.assertEqual(ET.tostring(actual.find('.//s:g[@id="quest-log"]',NS)),
                         ET.tostring(expected.find('.//s:g[@id="quest-log"]',NS)))
        self.assertNotEqual(result,self.svg)
        self.assertEqual(render(self.data),self.svg)

    def test_render_is_pure_and_fails_closed_on_changed_anchors(self):
        with (patch('pathlib.Path.read_text',side_effect=AssertionError('No file reads in render')),
             patch('pathlib.Path.write_text',side_effect=AssertionError('No file writes in render'))):
            self.assertEqual(render(self.data),self.svg)
        with self.assertRaises((AssertionError,ValueError)):
            apply('<svg/>')

    def test_all_46_tracks_have_unique_bindings_held_poses_and_closed_loops(self):
        used=[e.get('data-preview-track') for e in self.root.iter() if e.get('data-preview-track')]
        self.assertEqual(len(TRACKS),46)
        self.assertEqual(sorted(used),sorted(TRACKS))
        self.assertEqual(len(used),len(set(used)))
        css=''.join(e.text or '' for e in self.root.findall('s:style',NS))
        for name,t in TRACKS.items():
            ps=t['poses'];self.assertEqual(t['duration'],28.8)
            self.assertEqual(ps[0][0],0);self.assertEqual(ps[-1][0],28.8)
            self.assertEqual(ps[0][1:],ps[-1][1:])
            self.assertTrue(all(a[0]<b[0] for a,b in zip(ps,ps[1:])),name)
            self.assertIn(f'animation: {name} 28.8s steps(1,end) infinite',css)
        self.assertIn('.preview-motion { animation: none !important; }',css)
        self.assertIn('.preview-transient { opacity: 0 !important; }',css)

    def test_nessie_and_data_have_no_animation(self):
        def walk(e,moving=False):
            moving=moving or any('motion' in c for c in e.get('class','').split())
            if e.get('data-date') or e.get('id') in ['quest-log','crossover-nessie']:
                self.assertFalse(moving)
                self.assertFalse(any('motion' in n.get('class','') for n in e.iter()))
            for child in e:walk(child,moving)
        walk(self.root)

    def test_one_ball_and_one_adventurer_state_at_all_sampled_times(self):
        for i in range(2881):
            t=i/100
            self.assertEqual(pose(cm.TRACKS['companion-trainer-held-ball'],t)[1]+
                             pose(cm.TRACKS['companion-trainer-flight-ball'],t)[1],1)
            for actor in ['gon','killua','link']:
                self.assertEqual(sum(pose(v,t)[1] for k,v in am.TRACKS.items() if k.startswith('adventurer-'+actor+'-')),1)
            self.assertEqual(sum(pose(v,t)[1] for v in chest.TRACKS.values()),1)

    def test_link_hand_tracks_actual_chest_and_keeps_fixed_arm_lengths(self):
        for st,(lean,step,hand,rupee) in am.LINK_POSES.items():
            p=am._rotate(hand,lean,(0,-33));world=(797+step+p[0],279+p[1])
            elbow=am._link_elbow(hand)
            self.assertAlmostEqual(math.hypot(elbow[0]-14,elbow[1]+70),28)
            self.assertAlmostEqual(math.hypot(hand[0]-elbow[0],hand[1]-elbow[1]),30)
            if st in am.LINK_CONTACTS:
                for a,b in zip(world,am.LINK_CONTACTS[st]):self.assertAlmostEqual(a,b)

    def test_fishing_and_yoyo_endpoints_remain_attached(self):
        for state,(angle,endpoint,crank) in am.GON_POSES.items():
            nodes=list(ET.fromstring(sprites.gon(0,0)))
            n=ET.fromstring('<svg>'+am._gon_active(nodes,angle,endpoint,crank)+'</svg>')
            line=next(e for e in n.iter() if e.get('data-fishing-tip'))
            tip=tuple(map(float,line.get('data-fishing-tip').split(',')))
            for a,b in zip(tip,am._rotate((106,-121),angle)):self.assertAlmostEqual(a,b,places=3)
            self.assertEqual(tuple(map(float,line.get('data-fishing-endpoint').split(','))),endpoint)
        for hand,disc in am.KILLUA_POSES.values():
            n=ET.fromstring('<svg>'+am._yoyo_hand(hand,disc)+'</svg>')
            line=next(e for e in n.iter() if e.get('data-yoyo-hand'))
            self.assertEqual(line.get('d'),f'M{hand[0]:g} {hand[1]:g}L{disc[0]:g} {disc[1]:g}')

if __name__=='__main__':unittest.main()
