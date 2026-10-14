"""Apply the approved animated crossover scene to freshly generated real data.

All artwork and choreography are self-contained SVG. Imports are mandatory;
missing characters or changed scene anchors must fail the update, never publish
an incomplete illustration. No files, network or credentials are accessed here.
"""
from . import refined_visitors as v
from . import companions_motion as cm
from . import world_motion as wm
from . import chest_motion as chest
from . import adventurers_motion as am
from .creatures import sprites as creatures
from .motion_runtime import motion_css
TRACKS={**cm.TRACKS,**wm.TRACKS,**chest.TRACKS,**am.TRACKS}

def apply(base_svg):
    scene = chest.apply(base_svg)
    replacements={
    'M1084.00 42.00L1160.00 26.00L1241.00 54.00L1271.00 100.00L1218.00 133.00L1123.00 120.00L1070.00 86.00Z':'M1084.00 42.00L1185.00 26.00L1322.00 49.00L1360.00 110.00L1290.00 167.00L1123.00 130.00L1070.00 86.00Z',
    'M1095.00 48.00L1163.00 36.00L1232.00 62.00L1256.00 100.00L1211.00 119.00L1125.00 109.00L1081.00 81.00Z':'M1095.00 48.00L1187.00 37.00L1313.00 60.00L1345.00 108.00L1284.00 153.00L1126.00 118.00L1081.00 81.00Z',
    'M1095.00 48.00L1163.00 36.00L1232.00 62.00L1194.00 91.00L1125.00 83.00Z':'M1095.00 48.00L1187.00 37.00L1313.00 60.00L1268.00 104.00L1125.00 83.00Z',
    '<g transform="translate(1230 179) scale(1.02)">':'<g transform="translate(1370 230) scale(1.02)">'}
    for a,b in replacements.items():
     assert scene.count(a)==1,(a,scene.count(a));scene=scene.replace(a,b,1)
    
    chunks=[]
    def put(fn,x,y,s=1):
     chunks.append(fn(x,y,s))
    put(cm.trainer,397,657,.84)
    put(cm.mudkip,492,654,.79)
    put(wm.naruto,873,842,1.02)
    put(am.gon,1017,169,.96)
    put(am.killua,949,187,.96)
    put(am.link,797,279,1.0)
    put(wm.alexander,167,823,1.0)
    put(creatures.nessie,1244,111,.9)
    put(wm.murloc,1172,160,.9)
    put(wm.creeper,62,581,1.0)
    put(cm.chao,559,650,.85)
    # Reeds in front of Nessie and a short fishing ripple finish the water interaction.
    v.parts=[]
    v.add('<ellipse cx="1244" cy="113" rx="24" ry="4" fill="none" stroke="#9bb7a7" stroke-width="1.1" opacity=".55"/>')
    for x,y in [(1251,116),(1264,120),(1283,123),(1265,133),(1300,130)]:
     v.path(f'M{x} {y}l-2-23m2 23 7-20m-6 18-9-12','none',stroke='#607b3e',stroke_width=2)
     v.path(f'M{x-3} {y-23}v-7','none',stroke='#827147',stroke_width=3)
    # Small shoreline rushes flank the murloc without hiding its silhouette.
    for x,y in [(1126,157),(1207,169),(1223,156)]:
     v.poly([(x,y),(x-4,y-14),(x+1,y-7),(x+5,y-18),(x+4,y)],'#657f3f')
    chunks.append(''.join(v.parts))
    
    overlay=motion_css(TRACKS)+'<g id="crossover-scene">'+''.join(chunks)+'</g>\n'
    marker='<rect x="0" y="0" width="1400" height="1000" fill="url(#vignette)" />'
    if scene.count(marker)!=1:
     raise ValueError('Expected exactly one scene overlay insertion point')
    scene=scene.replace(marker,overlay+marker,1)
    scene=scene.replace('<title id="title">RuneScape contribution garden — quest-log variant</title>','<title id="title">RuneScape contribution garden with crossover visitors</title>')
    scene=scene.replace('</desc>',' Featuring a Pokemon trainer, Mudkip, Naruto, Gon, Killua, Link, a Creeper, Chao, Alexander, Nessie and a murloc. Ten visitor actions use native held-pose animation; Nessie and the contribution statistics stay still.</desc>',1)
    return scene
