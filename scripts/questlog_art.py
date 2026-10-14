"""The approved RuneScape quest-log scene. Pure, deterministic SVG rendering.

Only the daily tiles, counts and date labels change. Pixel glyphs are embedded
as vector paths, so the image needs no downloaded fonts or other assets.
Native SVG/CSS motion is decorative only and respects reduced-motion settings.
"""
import random, math
from datetime import date
from calendar_layout import calendar_layout


def _track(duration, poses):
    """Every entry is a held pose, with an explicit repeat-boundary state."""
    return {"duration": duration, "poses": poses}


# Woodcut/casting poses were informed by decoded OSRS gameplay GIFs. Hammer
# geometry was checked against official equipped-hammer and normal-anvil stills;
# its timing is authored, not claimed as a captured normal-smithing cycle.
# GIF sample intervals are not engine timing. All tracks deliberately hold poses.
MOTION_TRACKS = {
    "woodcut-swing": _track(1.2, [
        (0, "rotate(0deg)", 1), (.12, "rotate(12deg)", 1),
        (.24, "rotate(28deg)", 1), (.42, "rotate(-38deg)", 1),
        (.66, "rotate(-16deg)", 1), (.78, "rotate(0deg)", 1),
        (1.2, "rotate(0deg)", 1)]),
    "smith-body": _track(2.4, [
        (0, "rotate(0deg)", 1), (.30, "rotate(3deg)", 1),
        (.45, "rotate(5deg)", 1), (.60, "rotate(-14deg)", 1),
        (.84, "rotate(-11deg)", 1), (1.02, "rotate(-5deg)", 1),
        (1.20, "rotate(0deg)", 1), (2.4, "rotate(0deg)", 1)]),
    "smith-arm": _track(2.4, [
        (0, "rotate(0deg)", 1), (.30, "rotate(14deg)", 1),
        (.45, "rotate(22deg)", 1), (.60, "rotate(-76deg)", 1),
        (.84, "rotate(-61deg)", 1), (1.02, "rotate(-26deg)", 1),
        (1.20, "rotate(0deg)", 1), (2.4, "rotate(0deg)", 1)]),
    "smith-spark": _track(2.4, [
        (0, "translate(0px,0px)", 0), (.60, "translate(0px,0px)", .8),
        (.72, "translate(-4px,-8px)", .65), (.84, "translate(-8px,-16px)", .3),
        (.96, "translate(-12px,-22px)", 0), (2.4, "translate(0px,0px)", 0)]),
    "pond-ripple": _track(2.4, [
        (0, "scale(.42)", 0), (.3, "scale(.62)", .85),
        (.6, "scale(.82)", 1), (.9, "scale(1.02)", .9),
        (1.2, "scale(1.22)", .75), (1.5, "scale(1.42)", .5),
        (1.8, "scale(1.62)", .2), (2.1, "scale(1.78)", 0),
        (2.4, "scale(.42)", 0)]),
    "furnace-flame": _track(1.2, [
        (0, "scale(1,1)", 1), (.15, "scale(.98,1.18)", 1),
        (.3, "scale(1.04,.86)", 1), (.45, "scale(.96,1.25)", 1),
        (.6, "scale(1.05,.93)", 1), (.75, "scale(.98,1.12)", 1),
        (.9, "scale(1.06,.79)", 1), (1.05, "scale(1,1.08)", 1),
        (1.2, "scale(1,1)", 1)]),
    "campfire-flame": _track(1.2, [
        (0, "scale(1,1) rotate(0deg)", 1), (.15, "scale(.96,1.2) rotate(-3deg)", 1),
        (.3, "scale(1.08,.82) rotate(2deg)", 1), (.45, "scale(.94,1.35) rotate(-2deg)", 1),
        (.6, "scale(1.03,.94) rotate(1deg)", 1), (.75, "scale(.95,1.25) rotate(2deg)", 1),
        (.9, "scale(1.06,.88) rotate(-2deg)", 1), (1.05, "scale(.98,1.1) rotate(0deg)", 1),
        (1.2, "scale(1,1) rotate(0deg)", 1)]),
    "furnace-ember": _track(1.2, [
        (0, "translate(0px,0px)", 0), (.15, "translate(0px,-3px)", .8),
        (.3, "translate(1px,-7px)", .8), (.45, "translate(1px,-11px)", .65),
        (.6, "translate(2px,-16px)", .5), (.75, "translate(3px,-20px)", .25),
        (.9, "translate(4px,-24px)", 0), (1.2, "translate(0px,0px)", 0)]),
    "hero-idle": _track(7.2, [
        (0, "rotate(0deg)", 1), (2.4, "rotate(.8deg)", 1),
        (3, "rotate(0deg)", 1), (5.4, "rotate(-.8deg)", 1),
        (6, "rotate(0deg)", 1), (7.2, "rotate(0deg)", 1)]),
    "cow-tail": _track(7.2, [
        (0, "rotate(0deg)", 1), (3.6, "rotate(-18deg)", 1),
        (3.72, "rotate(14deg)", 1), (3.96, "rotate(-8deg)", 1),
        (4.2, "rotate(4deg)", 1), (4.44, "rotate(0deg)", 1),
        (7.2, "rotate(0deg)", 1)]),
    "wizard-cast": _track(7.2, [
        (0, "rotate(0deg)", 1), (1.2, "rotate(48deg)", 1),
        (1.35, "rotate(100deg)", 1), (4.05, "rotate(0deg)", 1),
        (7.2, "rotate(0deg)", 1)]),
    "wizard-glow": _track(7.2, [
        (0, "scale(.2)", 0), (1.35, "scale(.35)", .55),
        (1.5, "scale(.65)", .6), (1.65, "scale(.95)", .65),
        (1.8, "scale(1.15)", .6), (1.95, "scale(.9)", .55),
        (2.1, "scale(.65)", .5), (2.25, "scale(.35)", .4),
        (2.4, "scale(.2)", 0), (2.55, "scale(.35)", .5),
        (2.7, "scale(.65)", .55), (2.85, "scale(.95)", .6),
        (3, "scale(1.15)", .6), (3.15, "scale(.9)", .55),
        (3.3, "scale(.65)", .5), (3.45, "scale(.35)", .4),
        (3.6, "scale(.2)", 0), (7.2, "scale(.2)", 0)])
}


def motion_css():
    css = ['<style>', '.motion { transform-box: view-box; transform-origin: 0px 0px; }',
           '.transient { opacity: 0; }', '@media (prefers-reduced-motion: no-preference) {']
    for name, track in MOTION_TRACKS.items():
        css.append(f'  .{name} {{ animation: quest-{name} {track["duration"]:g}s steps(1,end) infinite; }}')
    css += ['  .pond-ripple ellipse { stroke-width: 2; }',
            '  .firebox-motion-clip { clip-path: url(#firebox-clip); }', '}']
    for name, track in MOTION_TRACKS.items():
        css.append(f'@keyframes quest-{name} {{')
        for time, transform, opacity in track['poses']:
            css.append(f'  {time / track["duration"] * 100:.6g}% {{ transform: {transform}; opacity: {opacity:g}; }}')
        css.append('}')
    css += ['@media (prefers-reduced-motion: reduce) {',
            '  .motion { animation: none !important; }',
            '  .transient { opacity: 0 !important; }', '}', '</style>']
    return '\n'.join(css)


def render_base(DATA):
    random.seed(42)
    S=[]
    def add(s): S.append(s)
    def rect(x,y,w,h,c,**a):
     attrs=' '.join(f'{k.replace("_","-")}="{v}"' for k,v in a.items()); add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{c}" {attrs}/>')
    def path(d,c,**a):
     attrs=' '.join(f'{k.replace("_","-")}="{v}"' for k,v in a.items()); add(f'<path d="{d}" fill="{c}" {attrs}/>')
    def text(x,y,t,size=12,c='#b1c2ba',**a):
     attrs=' '.join(f'{k.replace("_","-")}="{v}"' for k,v in a.items()); add(f'<text x="{x}" y="{y}" font-size="{size}" fill="{c}" {attrs}>{t}</text>')
    def use(id,x,y,scale=1,**a):
     attrs=' '.join(f'{k.replace("_","-")}="{v}"' for k,v in a.items()); add(f'<use href="#{id}" transform="translate({x} {y}) scale({scale})" {attrs}/>')
    def motion(name, x, y, delay=None, transient=False):
     # Keep placement on an outer group and animate only in a local coordinate
     # frame. A translated origin prevents CSS transforms from replacing the
     # character's placement/scale or orbiting around the SVG canvas.
     add(f'<g data-motion-pivot="{name}" transform="translate({x} {y})">')
     phase=f' style="animation-delay:{delay}s"' if delay is not None else ''
     transient_class="transient " if transient else ""
     add(f'<g class="motion {transient_class}{name}"{phase}><g transform="translate({-x} {-y})">')
    def endmotion(): add('</g></g></g>')
    def sparkle(x,y,c='#c8b3ec',s=2):
     rect(x-s,y,s*3,s,c);rect(x,y-s,s,s*3,c)
    def tree(x,y,s=1):
     add(f'<g transform="translate({x} {y}) scale({s})">')
     rect(-7,48,14,40,'#584852');rect(-3,48,5,39,'#9b735e');path('M-7 79h-12v5h38v-5h-12z','#263e41')
     path('M-9 0h18v8h16v10h13v16h12v22H34v14H13v9h-30v-8h-22V56h-13V35h11V21h15V9h17z','#163f45')
     path('M-9 0h18v8h16v10h13v16h7v13H23v11H-9V48h-25V34h9V20h16z','#267469')
     path('M-9 0h18v8h16v10h7v12H8v10H-9V30h-15V20h15z','#389c78')
     path('M-8 7H8v7h12v8H4v8h-13V20h-8v-6h9z','#78c18b')
     for xx,yy in [(24,34),(-25,38),(5,56),(-28,60)]:rect(xx,yy,5,3,'#4ea57c')
     add('</g>')
    def lantern(x,y,s=1):
     add(f'<g transform="translate({x} {y}) scale({s})">')
     add('<circle cx="0" cy="-37" r="26" fill="url(#lampGlow)"/>')
     rect(-2,-44,4,48,'#926f60');rect(-10,-47,22,3,'#967955');rect(8,-47,3,8,'#967955');rect(4,-40,11,15,'#37393f');rect(6,-38,7,11,'#ffda81');rect(8,-36,3,6,'#fff4c2');rect(4,-26,11,3,'#a97b48');rect(-6,4,12,4,'#435152');add('</g>')
    DAYS=DATA['last26Weeks']
    STATS=DATA['requestedWindow']
    START=date.fromisoformat(STATS['start'])
    END=date.fromisoformat(STATS['end'])
    STREAK_END=date.fromisoformat(STATS['currentStreakEnd']) if STATS['currentStreakEnd'] else None
    MONTHS='Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split()
    def shortdate(d): return f'{MONTHS[d.month-1]} {d.day}'
    DATE_RANGE=f'{shortdate(START)} - {shortdate(END)}, {END.year}' if START.year==END.year else f'{shortdate(START)}, {START.year} - {shortdate(END)}, {END.year}'
    STREAK_NOTE=f'through {shortdate(STREAK_END)}' if STREAK_END else 'No active streak'
    # An overhead orthographic game-world projection. u and v span the ground;
    # every block and ground object uses this common ground-space projection.
    U=(35.5,0); V=(-4,30.5); O=(251,337)
    def P(a,b,z=0):return (O[0]+a*U[0]+b*V[0],O[1]+a*U[1]+b*V[1]-z)
    def poly(points,c,**kw):path('M'+'L'.join(f'{x:.2f} {y:.2f}' for x,y in points)+'Z',c,**kw)
    def patch(a,b,w,d,c):poly([P(a,b),P(a+w,b),P(a+w,b+d),P(a,b+d)],c)
    def block(a,b,w,d,h,top,left,right):
     A,B,C,D=[P(*q,h) for q in [(a,b),(a+w,b),(a+w,b+d),(a,b+d)]]
     Ab,Bb,Cb,Db=[P(*q,0) for q in [(a,b),(a+w,b),(a+w,b+d),(a,b+d)]]
     poly([D,C,Cb,Db],left);poly([B,C,Cb,Bb],right);poly([A,B,C,D],top)
    def rock(x,y,s=1):
     add(f'<g transform="translate({x} {y}) scale({s})">')
     poly([(-18,9),(-15,-7),(0,-17),(20,-7),(27,9),(9,21)],'#71785d');poly([(-15,-7),(0,-17),(20,-7),(6,4)],'#a4a38a');poly([(6,4),(20,-7),(27,9),(9,21)],'#5b6854');poly([(-18,9),(-15,-7),(6,4),(9,21)],'#8a8e71');add('</g>')
    def oak(x,y,s=1):
     add(f'<g transform="translate({x} {y}) scale({s})">')
     add('<ellipse cx="12" cy="23" rx="49" ry="28" fill="#1d3520" opacity=".3"/>')
     path('M-7 27l3-56 12-5 8 62-12 5z','#746044');path('M-4-7l-17-24 5-4L2-17 18-35l6 6L8-1z','#8c7950')
     polys=[([(-55,-42),(-35,-68),(-1,-77),(17,-47),(-7,-15),(-46,-18)],'#577e32'),([(-35,-68),(-4,-95),(28,-74),(17,-47),(-1,-77)],'#6e8d37'), ([(17,-47),(28,-74),(56,-48),(61,-16),(35,1),(-7,-15)],'#456d2e'),([(-55,-42),(-46,-18),(-7,-15),(-15,10),(-49,-1),(-64,-19)],'#436b2b'),([(-7,-15),(17,-47),(35,1),(6,17),(-15,10)],'#729342'),([(-35,-68),(-1,-77),(17,-47),(-17,-43)],'#92a54c'), ([(28,-74),(56,-48),(17,-47)],'#7d9841')]
     for ps,c in polys:poly(ps,c)
     # Small foliage facets, sampled from OSRS's textured low-polygon canopy silhouette.
     rr=random.Random(int(x*37+y*7))
     for k in range(100):
      px=rr.uniform(-53,53);py=rr.uniform(-87,8)
      if (px/54)**2+((py+37)/56)**2>1:continue
      poly([(px,py),(px+rr.uniform(3,7),py-1),(px+rr.uniform(0,3),py+rr.uniform(2,5))],rr.choice(['#41602c','#567732','#698238','#7e9345','#8e9d4e']),opacity=.8)
     poly([(-4,20),(-20,29),(-9,29),(1,25),(14,33),(22,29),(11,19)],'#675333')
     path('M-1 23l4-27m5 26L6 5','none',stroke='#453c27',stroke_width=2)
     add('</g>')
    # Additional references: actual Draynor willow chopping, Lumbridge forestry and
    # sheep-pen screenshots, and the OSRS bank deposit chest object render.
    def willow(x,y,s=1):
     add(f'<g transform="translate({x} {y}) scale({s})">')
     add('<ellipse cx="8" cy="17" rx="49" ry="23" fill="#253820" opacity=".3"/>')
     poly([(-8,13),(-23,26),(-8,23),(0,18),(12,28),(24,22),(8,10),(6,-75),(-5,-91),(-13,-75)],'#514b30')
     poly([(-8,13),(0,18),(4,-70),(-5,-91),(-5,-35)],'#84714a')
     path('M-2-21l-21-35-18-13m40 20 25-30 10-11M0-45l6-56','none',stroke='#625634',stroke_width=8)
     rr=random.Random(411)
     for cx,cy,w,h in [(-32,-66,23,59),(-4,-104,31,72),(27,-88,28,68),(40,-43,20,46),(-22,-29,22,44)]:
      poly([(cx-w,cy+3),(cx-w*.82,cy-8),(cx,cy-14),(cx+w*.75,cy-7),(cx+w,cy+4),(cx+w*.78,cy+h*.7),(cx+w*.33,cy+h),(cx-w*.7,cy+h*.78)],'#3b5427')
      poly([(cx-w,cy+3),(cx-w*.82,cy-8),(cx,cy-14),(cx+w*.75,cy-7),(cx+w,cy+4),(cx,cy+11)],'#637439')
      for k in range(70):
       lx=cx+rr.uniform(-w*.85,w*.85);ly=cy+rr.uniform(1,h*.86);ll=rr.uniform(4,13)
       poly([(lx,ly),(lx+rr.uniform(1.5,3),ly+2),(lx+rr.uniform(-2,1),ly+ll)],rr.choice(['#546831','#70813b','#819344','#2e4823','#415d28']))
     add('</g>')
    def woodcutter(x,y,s=1):
     add(f'<g id="woodcutter" transform="translate({x} {y}) scale({s})">')
     add('<ellipse cx="0" cy="20" rx="23" ry="11" fill="#233b22" opacity=".28"/>')
     # Familiar default human: khaki tee, green trousers, brown boots; viewed side-on.
     poly([(-10,-10),(0,-8),(-3,10),(-10,24),(-17,20),(-12,6)],'#276640')
     poly([(0,-9),(10,-10),(9,8),(16,23),(9,25),(1,10)],'#3c8c53')
     poly([(-17,18),(-9,22),(-11,27),(-26,27),(-24,23)],'#70502d')
     poly([(8,21),(15,20),(23,27),(20,30),(9,28)],'#634529')
     poly([(-13,-41),(-4,-46),(9,-40),(14,-27),(8,-11),(-10,-10),(-15,-22)],'#999a57')
     poly([(-13,-41),(-4,-46),(0,-30),(-5,-11),(-10,-10),(-15,-22)],'#b5ae6c')
     poly([(0,-30),(9,-40),(14,-27),(8,-11),(-5,-11)],'#828b4c')
     path('M-10-11l18-1','none',stroke='#704124',stroke_width=3)
     # Back arm rests by the hip.
     poly([(8,-37),(14,-32),(17,-23),(11,-19),(6,-27)],'#aaa166')
     poly([(12,-21),(17,-23),(19,-10),(15,-4),(11,-9)],'#b99366')
     # Bald angular head and profile nose.
     poly([(-10,-58),(-7,-67),(3,-70),(11,-64),(10,-54),(4,-47),(-5,-47),(-13,-53)],'#c8aa7c')
     poly([(-10,-58),(-7,-67),(3,-70),(5,-61),(-1,-54),(-13,-53)],'#dfc494')
     poly([(-13,-57),(-17,-54),(-13,-52),(-10,-48),(-5,-47),(-4,-55)],'#b79262')
     poly([(-12,-57),(-9,-57),(-10,-55)],'#3d3727')
     # Sleeve, forearm, grip and axe rotate together around the shoulder.
     motion("woodcut-swing", -11, -35)
     # Forward sleeve and bent forearm, both hands close to the upright handle.
     poly([(-13,-39),(-20,-33),(-18,-23),(-10,-23),(-6,-32)],'#b2aa67')
     poly([(-18,-25),(-12,-25),(-14,-20),(-29,-23),(-31,-28),(-26,-30)],'#d0ad7c')
     poly([(-30,-30),(-24,-28),(-24,-22),(-30,-23)],'#879194')
     # Rune axe: upright wooden shaft and blue-grey single-bit head, as in screenshots.
     path('M-30-21l1-40','none',stroke='#83601f',stroke_width=5)
     path('M-29-22v-38','none',stroke='#b09337',stroke_width=2)
     poly([(-30,-60),(-40,-67),(-46,-65),(-49,-58),(-42,-53),(-30,-56),(-23,-56),(-23,-61)],'#557987')
     poly([(-40,-67),(-46,-65),(-49,-58),(-44,-57),(-42,-62)],'#aec1be')
     poly([(-30,-60),(-40,-67),(-42,-62),(-30,-57),(-23,-58),(-23,-61)],'#719baa')
     poly([(-32,-28),(-26,-28),(-25,-23),(-28,-20),(-33,-23)],'#d4b07b')
     endmotion()
     add('</g>')
    def stump(x,y,s=1):
     add(f'<g transform="translate({x} {y}) scale({s})">')
     poly([(-17,-4),(-20,11),(-34,19),(-20,22),(-11,15),(0,24),(12,18),(31,21),(23,9),(14,-6)],'#4b3b24')
     poly([(-17,-4),(-18,10),(-8,16),(1,11),(14,16),(20,7),(14,-6)],'#745633')
     poly([(-17,-4),(-12,-11),(5,-14),(17,-7),(14,1),(2,7),(-11,3)],'#ba9e69')
     path('M-11-3l6-5 11 1 5 5-8 5-9-2zM-4-3l5-1 3 3-4 2z','none',stroke='#8c7147',stroke_width=1.2)
     path('M-13 4l-4 11m23-7 6 8m-10-1 1 7','none',stroke='#342d20',stroke_width=2)
     add('</g>')
    def logpile(x,y,s=1):
     add(f'<g transform="translate({x} {y}) scale({s})">')
     for xx,yy in [(0,4),(0,-5),(10,-12)]:
      poly([(xx,yy-6),(xx+40,yy-1),(xx+38,yy+12),(xx-2,yy+6)],'#604728')
      poly([(xx,yy-6),(xx+40,yy-1),(xx+35,yy+2),(xx+1,yy-2)],'#8b6b3d')
      add(f'<ellipse cx="{xx}" cy="{yy}" rx="7" ry="7" fill="#bda16a"/>')
      add(f'<ellipse cx="{xx}" cy="{yy}" rx="4.5" ry="4.5" fill="none" stroke="#80623a" stroke-width="1.2"/>')
      path(f'M{xx+12} {yy+1}l19 3m-14-1 9 4','none',stroke='#3e3422',stroke_width=1.2)
     add('</g>')
    def bankchest(x,y,s=1):
     add(f'<g transform="translate({x} {y}) scale({s})">')
     add('<ellipse cx="8" cy="22" rx="41" ry="16" fill="#243521" opacity=".28"/>')
     # The actual plain, open OSRS deposit chest: thick grey iron, weathered planks.
     poly([(-26,-7),(-14,-24),(39,-24),(27,-7)],'#453626',stroke='#737875',stroke_width=5)
     poly([(-14,-64),(39,-64),(39,-24),(-14,-24)],'#866848',stroke='#868986',stroke_width=5)
     for yy in [-51,-38]:path(f'M-11 {yy}h47','none',stroke='#584631',stroke_width=1.5)
     poly([(-11,-60),(34,-60),(34,-55),(-11,-55)],'#a08055',opacity=.65)
     poly([(-26,-7),(27,-7),(27,24),(-26,24)],'#755838',stroke='#858982',stroke_width=5)
     poly([(27,-7),(39,-24),(39,11),(27,24)],'#574631',stroke='#656e68',stroke_width=5)
     for xx in [-13,0,13]:path(f'M{xx}-4V21','none',stroke='#473d2d',stroke_width=1.5)
     rect(-26,20,54,5,'#9a9e92');rect(7,-67,9,5,'#767c75')
     rr=random.Random(29)
     for k in range(20):
      xx=rr.uniform(-10,33);yy=rr.uniform(-59,-29);rect(xx,yy,rr.uniform(2,6),1.3,'#a68a5f',opacity=.45)
     add('</g>')
    def fencepost(x,y):
     poly([(x-4,y+4),(x-3,y-24),(x+1,y-33),(x+5,y-24),(x+4,y+5)],'#54401f')
     poly([(x-3,y-24),(x+1,y-33),(x+2,y+3),(x-4,y+4)],'#8a682c')
    def flowers(x,y,s=1):
     add(f'<g transform="translate({x} {y}) scale({s})">')
     for xx,yy in [(-6,0),(2,-4),(9,2)]:
      path(f'M{xx} {yy+8}v-8','none',stroke='#6c8842',stroke_width=1.5)
      for dx,dy in [(-3,0),(0,-2),(3,0),(0,2)]:poly([(xx+dx-2,yy+dy),(xx+dx,yy+dy-2),(xx+dx+2,yy+dy),(xx+dx,yy+dy+2)],'#d9dcc4')
      rect(xx-1,yy-1,2,2,'#c3ae64')
     add('</g>')

    # Reference: the actual low-polygon OSRS cow model, inspected at
    # https://rpgstash-blog.s3.amazonaws.com/Image_2023-10-09_pasted-image-359.png
    # The same game model appears in https://www.rpgstash.com/blog/osrs-ironman-ultimate-p2p-and-f2p-guide .
    def cow(x,y,s=1):
     add(f'<g transform="translate({x} {y}) scale({s})">')
     add('<ellipse cx="-2" cy="54" rx="78" ry="17" fill="#263920" opacity=".3"/>')
     # Far legs and tail, behind the barrel-shaped torso.
     poly([(-30,11),(-20,15),(-20,38),(-25,53),(-32,55),(-30,35)],'#414536')
     poly([(-30,49),(-24,49),(-21,57),(-34,58)],'#30382e')
     poly([(46,13),(57,13),(54,35),(61,51),(53,55),(44,35)],'#34392a')
     poly([(53,49),(61,49),(65,58),(50,58)],'#353c31')
     motion('cow-tail', 62, -15)
     path('M62-15l12 15-1 29','none',stroke='#a9ad91',stroke_width=3)
     poly([(70,24),(76,25),(80,34),(72,36),(67,32)],'#353929')
     endmotion()
     # Large faceted body, with the silhouette and broken patches of the game model.
     poly([(-34,-28),(3,-38),(45,-34),(62,-23),(67,-3),(62,15),(44,28),(4,32),(-31,19),(-45,-4)],'#434731')
     poly([(-34,-28),(3,-38),(45,-34),(27,-18),(-6,-15),(-45,-4)],'#5d6045')
     poly([(27,-18),(45,-34),(62,-23),(67,-3),(48,3)],'#4e5139')
     poly([(-45,-4),(-6,-15),(0,7),(-13,25),(-31,19)],'#363d2a')
     poly([(0,7),(27,-18),(48,3),(62,15),(44,28),(4,32),(-13,25)],'#333b29')
     poly([(-13,25),(4,32),(44,28),(53,20),(33,19),(5,25)],'#939d85')
     # Broad off-white shoulder stripe and a crooked stripe across the hindquarters.
     poly([(-32,-27),(-18,-31),(-4,-20),(-7,-3),(-3,15),(-13,26),(-29,18),(-23,-4)],'#d4d4bb')
     poly([(-7,-3),(-3,15),(-13,26),(-29,18),(-23,9),(-13,12)],'#abb59d')
     poly([(17,-36),(31,-36),(42,-17),(38,-2),(45,17),(33,25),(27,8),(25,-2),(28,-15)],'#d9d9c3')
     poly([(38,-2),(45,17),(33,25),(27,8),(29,2)],'#a9b49c')
     poly([(-1,-37),(10,-40),(21,-37),(16,-30),(5,-27)],'#e1dfc8')
     # Pinkish udder, small angular teats.
     poly([(20,25),(37,21),(46,28),(37,37),(24,35)],'#b69a8e')
     poly([(20,25),(29,25),(36,29),(24,35)],'#c9ada0')
     for xx,yy in [(26,33),(33,35),(40,31)]:poly([(xx,yy),(xx+4,yy),(xx+3,yy+8),(xx,yy+8)],'#b69c91')
     # Near foreleg and hind leg: bent joints, white stockings and broad dark hooves.
     poly([(-34,12),(-19,18),(-23,37),(-33,56),(-42,55),(-35,35)],'#d1d2b8')
     poly([(-34,12),(-28,20),(-29,36),(-39,52),(-42,55),(-35,35)],'#929f8a')
     poly([(-29,35),(-23,37),(-33,56),(-39,56)],'#535c44')
     poly([(-42,51),(-33,54),(-31,63),(-48,62),(-49,58)],'#384332')
     poly([(44,17),(57,15),(53,37),(58,56),(48,59),(43,38)],'#434d34')
     poly([(44,17),(49,23),(47,39),(52,53),(48,59),(43,38)],'#657052')
     poly([(48,54),(58,53),(63,62),(48,64),(44,60)],'#30392d')
     # Low, long neck and broad tapered head facing left, with an OSRS white blaze.
     poly([(-39,-25),(-55,-35),(-69,-31),(-77,-17),(-74,0),(-57,7),(-38,-4),(-27,-19)],'#414832')
     poly([(-39,-25),(-55,-35),(-69,-31),(-65,-18),(-46,-15),(-27,-19)],'#5e6247')
     poly([(-74,0),(-57,7),(-38,-4),(-46,-15),(-65,-18),(-77,-17)],'#313a29')
     # Ears and short pale horn stubs, shaped from the inspected model.
     poly([(-49,-29),(-34,-31),(-32,-24),(-40,-18),(-49,-22)],'#474d32')
     poly([(-47,-27),(-36,-28),(-39,-22)],'#777952')
     poly([(-70,-30),(-78,-42),(-82,-40),(-80,-27),(-73,-21)],'#4a4d32')
     poly([(-66,-32),(-72,-42),(-68,-50),(-60,-45),(-58,-34)],'#d4d6c3')
     poly([(-68,-50),(-60,-45),(-58,-34),(-63,-37)],'#b0b8a5')
     poly([(-51,-31),(-53,-43),(-48,-47),(-42,-41),(-43,-32)],'#e1dfca')
     poly([(-53,-43),(-48,-47),(-49,-35),(-51,-31)],'#bfc5b1')
     poly([(-68,-30),(-59,-24),(-66,-10),(-74,-1),(-77,8),(-90,5),(-83,-6),(-76,-15)],'#e0dec8')
     poly([(-66,-10),(-74,-1),(-77,8),(-90,5),(-85,0),(-72,-9)],'#b9c2ad')
     # Angular eye and the pale, broad muzzle; tiny nostrils are not cartoon circles.
     poly([(-64,-20),(-57,-18),(-59,-12),(-65,-11),(-68,-15)],'#bdc4af')
     poly([(-64,-19),(-59,-18),(-61,-13),(-65,-13)],'#1d281e')
     poly([(-91,-7),(-82,-10),(-72,-5),(-68,2),(-73,10),(-89,11),(-96,5)],'#bfb6aa')
     poly([(-91,-7),(-82,-10),(-72,-5),(-74,2),(-90,4),(-96,5)],'#d8d0be')
     poly([(-90,3),(-86,1),(-84,5),(-89,6)],'#454a39')
     poly([(-75,2),(-72,1),(-71,4),(-75,5)],'#454a39')
     path('M-88 9l12-1','none',stroke='#878c74',stroke_width=1)
     add('</g>')

    add(f'''<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="1000" viewBox="0 0 1400 1000" role="img" aria-labelledby="title desc"><title id="title">RuneScape contribution garden — quest-log variant</title><desc id="desc">A high overhead RuneScape-style garden, with 182 daily contribution tiles from Cameron's actual GitHub activity, {START.isoformat()} through {END.isoformat()}. {STATS['total']:,} contributions, {STATS['activeDays']} active days, a {STATS['bestStreak']}-day best streak, and a {STATS['currentStreakAllowTodayPending']}-day current streak. A player in full rune armour carries a dragon scimitar without a shield; a blue-robed wizard carries a staff of fire, and goblins wander near the trees. A third human chops a willow with a rune axe, beside a rooted stump and logs. A plain iron-bound bank deposit chest, pointed rail fencing, mining rocks fishing ripples and an angular white-patched cow evoke the skilling areas of RuneScape. A fourth human smith works a hot bar beside a tapered brick furnace. An OSRS-inspired stone-framed quest list presents the same real statistics at lower right. Calendar columns are Sunday-first weeks; blank edge slots fall outside the displayed 182-day window. The current day is partial.</desc><defs>
<radialGradient id="vignette"><stop offset=".55" stop-color="#132614" stop-opacity="0"/><stop offset="1" stop-color="#142417" stop-opacity=".35"/></radialGradient>
<radialGradient id="lamp"><stop stop-color="#ffd691" stop-opacity=".5"/><stop offset="1" stop-color="#ffc873" stop-opacity="0"/></radialGradient>
<g id="tuft"><path d="M-4 4l-5-9 8 4 3-10 3 10 8-4-5 9z" fill="#688740"/><path d="M0 3l2-9 2 9z" fill="#93a555"/></g>
<clipPath id="firebox-clip"><path d="M-29-55L-19-63 0-60 8-49 8-21-30-28Z"/></clipPath>
</defs>''')
    # Native, discrete pose changes; no interpolation between key poses.
    # A 7.2-second master loop closes every track and keeps the art stationary
    # for reduced-motion users. Data tiles and labels have no motion classes.
    add(motion_css())
    # Full-bleed world ground. No floating island, display frame, title, or quest card.
    rect(0,0,1400,1000,'#516e35')
    # Broad faceted earth polygons, like the untextured terrain in the actual game.
    for pts,c in [([(0,0),(420,0),(326,182),(0,279)],'#5e783b'), ([(420,0),(868,0),(1003,186),(326,182)],'#59763a'), ([(868,0),(1400,0),(1400,278),(1003,186)],'#4c6d34'), ([(0,279),(326,182),(242,598),(0,646)],'#547537'), ([(1003,186),(1400,278),(1400,693),(1199,591)],'#56763a'), ([(0,646),(242,598),(803,799),(581,1000),(0,1000)],'#476d32'), ([(803,799),(1199,591),(1400,693),(1400,1000),(581,1000)],'#4d7135')]:poly(pts,c)
    add('<g id="game-world" transform="translate(-38 0)">')
    # Worn dirt route around the allotment, plus approach roads.
    patch(-2,-1.55,30,10.5,'#9c936a');patch(-1.7,-1.25,29.4,9.9,'#a99c71')
    poly([(0,319),(205,362),(184,445),(0,405)],'#a99c71')
    poly([(852,606),(946,606),(958,1000),(865,1000)],'#a99c71')
    # Path edge texture, flat angular dirt flecks.
    for i in range(140):
     a=random.uniform(-1.6,27.5);b=random.choice([random.uniform(-1.3,-.4),random.uniform(7.5,8.5)])
     x,y=P(a,b);poly([(x,y),(x+5,y-2),(x+8,y+1),(x+2,y+4)],random.choice(['#b5a77b','#968964','#c0b085']),opacity=.45)
    # Stone perimeter around the actual garden. Avoid tall walls that occlude rows.
    patch(-.3,-.3,26.6,7.6,'#686e4f');patch(-.15,-.15,26.3,7.3,'#8b8f65');patch(0,0,26,7,'#4b583b')
    for c in range(27):
     block(c-.2,-.38,.8,.28,5,'#b4b092','#7c8362','#6c775b')
     block(c-.2,7.1,.8,.28,5,'#9d9f79','#6c7b54','#687353')
    for r in range(7):
     block(-.4,r+.05,.28,.8,5,'#a7aa83','#78845e','#667254')
     block(26.08,r+.05,.28,.8,5,'#a4a37c','#798057','#69724f')
    # A little pond and cattails, upper right.
    poly([(1084,42),(1160,26),(1241,54),(1271,100),(1218,133),(1123,120),(1070,86)],'#49624b')
    poly([(1095,48),(1163,36),(1232,62),(1256,100),(1211,119),(1125,109),(1081,81)],'#507a73')
    poly([(1095,48),(1163,36),(1232,62),(1194,91),(1125,83)],'#668d7c')
    path('M1095 66l38 6m43 35 34-3m-75-56 39 5','none',stroke='#a2b19a',stroke_width=2,opacity=.45)
    for x,y in [(1069,81),(1093,119),(1232,119),(1247,54)]:
     path(f'M{x} {y}l3-25m1 25 9-20m-8 19-7-15','none',stroke='#526f30',stroke_width=3)
     rect(x+1,y-28,4,9,'#745d31')
    for i,(xx,yy,rx,ry) in enumerate([(1160,77,13,5),(1176,91,18,6),(1190,75,9,4)]):
     motion("pond-ripple", xx, yy, delay=-.8*i)
     add(f'<ellipse cx="{xx}" cy="{yy}" rx="{rx}" ry="{ry}" fill="none" stroke="#bbc7b2" stroke-width="1.2" opacity=".7"/>')
     endmotion()
    path('M1175 83l4-8 3 8m-8 6h9','none',stroke='#d3d6bb',stroke_width=1.5)

    # Background copse and far-side objects, all outside the data bed.
    for x,y,s in [(50,100,1.2),(168,55,.83),(893,130,1.0),(1230,179,1.02),(1376,319,1.1),(45,633,.93)]:oak(x,y,s)
    willow(371,110,.75);willow(611,95,.78)
    # An overhead cottage: visible roof dominates; walls are shallow at this camera angle.
    # Level only the cottage in its own local frame, preserving its roof and wall depth.
    add('<g transform="rotate(-11.925 140 145)">')
    poly([(65,117),(224,151),(191,284),(30,250)],'#514e33',opacity=.3)
    poly([(52,123),(213,157),(200,241),(39,207)],'#ab9868')
    poly([(213,157),(236,71),(224,168),(200,241)],'#877b50')
    poly([(52,123),(213,157),(236,71),(75,37)],'#635842')
    poly([(52,123),(75,37),(146,58),(124,142)],'#89724a')
    poly([(124,142),(146,58),(236,71),(213,157)],'#72613f')
    path('M146 58l-22 84','none',stroke='#b09a67',stroke_width=5)
    for i in range(1,8):
     t=i/8;path(f'M{52+23*t} {123-86*t}L{213+23*t} {157-86*t}','none',stroke='#a18b5b',stroke_width=2)
    for i in range(1,8):
     t=i/8;path(f'M{52+161*t} {123+34*t}L{75+161*t} {37+34*t}','none',stroke='#524c36',stroke_width=1.5)
    poly([(173,53),(186,41),(205,47),(202,91),(184,94),(173,85)],'#818671');poly([(173,53),(186,41),(205,47),(190,59)],'#acaf98');poly([(190,59),(205,47),(202,91),(184,94)],'#616e5b')
    path('M47 172l160 34m-138-78-14 80m76-69-14 82m79-69-15 75','none',stroke='#594f34',stroke_width=6)
    poly([(137,179),(159,184),(153,227),(130,221)],'#504932');poly([(72,166),(94,171),(91,194),(68,189)],'#d5b276',stroke='#625636',stroke_width=3)
    poly([(126,221),(156,227),(160,236),(124,230)],'#bdb18b')
    add('</g>')
    # Small fencing and wheelbarrow by the building.
    path('M17 249l95 22m-95-10 95 22','none',stroke='#654b25',stroke_width=6)
    path('M17 247l95 22m-95-10 95 22','none',stroke='#9a7535',stroke_width=2)
    for x,y in [(17,269),(63,280),(112,291)]:fencepost(x,y)
    poly([(235,106),(265,112),(258,139),(229,132)],'#795f35');poly([(235,106),(241,97),(273,103),(265,112)],'#b59755');path('M249 132l-10 24m13-21 18 17','none',stroke='#725e38',stroke_width=4);add('<ellipse cx="238" cy="151" rx="7" ry="8" fill="#403f2b"/>')
    # Reference-based woodcutting corner, plain bank chest and weathered rail fence.
    willow(363,230,.92)
    stump(505,246,.77);logpile(537,246,.75)
    bankchest(751,244,.9)
    path('M790 218l241-5m-241 13 241-5','none',stroke='#5e4723',stroke_width=5)
    path('M790 216l241-5','none',stroke='#9b7737',stroke_width=1.5)
    for xx in [790,838,886,934,982,1031]:fencepost(xx,231-(xx-790)*.02)
    for xx,yy in [(282,260),(573,265),(834,243),(951,247),(1070,165),(68,452),(1293,389),(1040,706)]:flowers(xx,yy,.72)
    # Thin twigs and individual grass blades complement the larger ground facets.
    rr=random.Random(817)
    for k in range(150):
     xx=rr.randint(23,1370);yy=rr.randint(25,870)
     if 135<xx<1255 and 278<yy<613:continue
     if 1060<xx<1280 and 20<yy<140:continue
     if 210<xx<690 and 610<yy<847:continue
     if 730<xx<885 and 578<yy<792:continue
     poly([(xx,yy),(xx-rr.randint(1,4),yy-rr.randint(4,10)),(xx+1,yy-3)],rr.choice(['#748d43','#82964b','#39592e']),opacity=.8)
    for xx,yy in [(478,223),(484,270),(424,274),(312,238),(985,272),(112,559),(1270,637)]:
     path(f'M{xx} {yy}l14-4m-5 3 3 7','none',stroke='#705934',stroke_width=2)
    # Copper and tin-bearing mining rocks: angular gray shells, colored ore seams.
    for xx,yy,ore in [(1307,514,'#b17342'),(1342,525,'#a3afa6')]:
     poly([(xx-19,yy+11),(xx-21,yy-4),(xx-7,yy-24),(xx+12,yy-22),(xx+24,yy-5),(xx+20,yy+16),(xx,yy+22)],'#666d61')
     poly([(xx-21,yy-4),(xx-7,yy-24),(xx+12,yy-22),(xx+3,yy-3)],'#969b85')
     poly([(xx+3,yy-3),(xx+12,yy-22),(xx+24,yy-5),(xx+20,yy+16)],'#4f5c50')
     for dx,dy in [(-10,-8),(-3,3),(9,-10),(13,8)]:poly([(xx+dx-3,yy+dy),(xx+dx+2,yy+dy-4),(xx+dx+5,yy+dy+1),(xx+dx,yy+dy+4)],ore)
    # Keep the rolling 182 dates, but align real weeks Sunday through Saturday.
    # Partial edge weeks have unplanted slots, never synthetic zero counts.
    # Compress only the horizontal tile spacing to preserve the approved bed bounds.
    C=[('#494a34','#2b3427','#343c29'),('#3c7142','#254c30','#315b35'),('#5b9851','#35663c','#437d43'),('#90bb5a','#567e3a','#6c9444'),('#c6d475','#879c47','#a2b256'),('#e8bf68','#a48339','#c29e49')]
    H=[.8,4,7,11,16,21]
    LAYOUT=calendar_layout(DAYS)
    WEEK_WIDTH=26 / LAYOUT['columns']
    for cell in sorted(LAYOUT['cells'], key=lambda cell: (cell['row'], cell['column'])):
     d=cell['day'];col=cell['column'];row=cell['row'];n=d['count'];lv=0 if n==0 else 1 if n<=3 else 2 if n<=7 else 3 if n<=15 else 4 if n<=31 else 5
     add(f'<g data-date="{d["date"]}" data-count="{n}" data-calendar-column="{col}" data-calendar-row="{row}"><title>{d["date"]}: {n} contributions</title>')
     x0=(col+.09)*WEEK_WIDTH;x1=(col+.91)*WEEK_WIDTH
     top,left,right=C[lv];block(x0,row+.12,.82*WEEK_WIDTH,.76,H[lv],top,left,right)
     poly([P(x0,row+.12,H[lv]),P(x1,row+.12,H[lv]),P(x1,row+.88,H[lv]),P(x0,row+.88,H[lv])],'none',stroke='#304525',stroke_width=.65,stroke_opacity=.5)
     ps=[P(x0,row+.12,H[lv]),P(x1,row+.12,H[lv]),P(x1,row+.16,H[lv]),P(x0,row+.16,H[lv])]
     poly(ps,'#e1e6b0',opacity=.2)
     if n>=32:
      x,y=P((col+.3)*WEEK_WIDTH,row+.28,H[lv]);poly([(x,y),(x+5,y+1),(x+4,y+3),(x-1,y+2)],'#eff0bf',opacity=.35)
     add('</g>')
    # Low-poly rocks, reeds, herbs and flowers live around the plot, never cover cells.
    for x,y,s in [(1280,421,.6),(1308,460,1),(59,500,.6),(122,526,.7),(1090,771,.6),(744,751,.4),(670,828,.65),(470,168,.55)]:rock(x,y,s)
    for i in range(92):
     x=random.randint(0,1399);y=random.randint(0,844)
     # Keep exact data and path bounds clear.
     if 130<x<1250 and 140<y<738:continue
     if 1060<x<1280 and 20<y<140:continue
     if 210<x<690 and 610<y<847:continue
     use('tuft',x,y,random.choice([.7,1,1.2]))
    # Gnarled, brown/gold staff with a red fire orb, matching the actual OSRS item.
    def firestaff(x,y,s=1):
     add(f'<g transform="translate({x} {y}) scale({s})">')
     path('M0 19l-4-22-11-16-2-21','none',stroke='#654a21',stroke_width=5)
     path('M0 19l-4-22-11-16-2-21','none',stroke='#a58a35',stroke_width=2)
     poly([(-22,-39),(-11,-41),(-10,-35),(-18,-30)],'#989180')
     poly([(-24,-47),(-21,-55),(-13,-57),(-6,-51),(-7,-43),(-15,-37),(-21,-40)],'#bc3020')
     poly([(-24,-47),(-21,-55),(-13,-57),(-12,-48),(-21,-43)],'#ec5d32')
     poly([(-12,-48),(-13,-57),(-6,-51),(-7,-43),(-15,-37)],'#871e16')
     add('</g>')
    # Actual Rune full helm silhouette: blue-grey dome and upright PURPLE plume;
    # vertical black visor slots. Human proportions, articulated armour, no shield.
    def player(x,y,s=1):
     add(f'<g transform="translate({x} {y}) scale({s})">')
     add('<ellipse cx="6" cy="13" rx="24" ry="13" fill="#263b26" opacity=".32"/>')
     # platelegs, feet, parted stance
     poly([(-11,-4),(-1,-5),(-2,9),(-8,20),(-15,17),(-11,6)],'#4d6f7a');poly([(1,-5),(11,-4),(14,10),(12,21),(5,21),(4,6)],'#3c5f6e')
     poly([(-11,-4),(-4,-4),(-5,8),(-11,14),(-14,11)],'#7897a0');poly([(4,-4),(10,-4),(12,10),(7,14),(5,7)],'#638792')
     poly([(-14,15),(-8,18),(-11,25),(-23,23),(-21,20)],'#344a50');poly([(7,18),(13,18),(20,23),(18,27),(7,26)],'#344a50')
     # skirt plates, leather belt
     poly([(-13,-15),(12,-15),(14,-2),(5,4),(-1,-2),(-8,4),(-15,0)],'#577d86');poly([(-13,-15),(-1,-13),(-1,-2),(-8,4),(-15,0)],'#75949a')
     path('M-12-16l11 3 13-3','none',stroke='#483e30',stroke_width=4)
     # A tiny upper-body weight shift; legs, feet and shadow stay planted.
     motion("hero-idle", 0, -14)
     # torso: actual peaked angular platebody, not a square robot
     poly([(-12,-37),(-5,-43),(7,-41),(16,-33),(12,-17),(0,-13),(-12,-18),(-18,-31)],'#527684')
     poly([(-12,-37),(-5,-43),(0,-33),(-1,-19),(-12,-18),(-18,-31)],'#81a0a7')
     poly([(0,-33),(7,-41),(16,-33),(12,-17),(-1,-19)],'#486c7a')
     poly([(-12,-29),(0,-33),(13,-27),(8,-23),(-1,-19),(-10,-23)],'#668a96')
     # rounded low polygon shoulders, upper arms and bracers
     poly([(-16,-37),(-23,-33),(-24,-23),(-18,-19),(-11,-30)],'#72949f');poly([(14,-35),(21,-32),(25,-23),(19,-20),(12,-28)],'#71919a')
     poly([(-23,-23),(-18,-21),(-19,-10),(-24,-7),(-27,-14)],'#587987');poly([(21,-22),(26,-20),(28,-10),(24,-6),(20,-13)],'#587987')
     poly([(-27,-15),(-19,-13),(-18,-7),(-23,-3),(-29,-8)],'#456c7c');poly([(23,-14),(30,-14),(32,-7),(26,-4),(21,-8)],'#4f7b88')
     poly([(-24,-5),(-18,-5),(-16,0),(-20,5),(-25,1)],'#628592');poly([(27,-6),(32,-4),(33,1),(28,4),(25,0)],'#527583')
     # helm with faceted upper hemisphere seen from above
     add('<g transform="translate(0 -6.8) scale(.8)">')
     poly([(-12,-51),(-5,-60),(6,-61),(14,-55),(16,-44),(10,-35),(-2,-33),(-12,-40)],'#567984')
     poly([(-12,-51),(-5,-60),(6,-61),(4,-49),(-8,-44)],'#829da4');poly([(6,-61),(14,-55),(16,-44),(4,-49)],'#456977')
     poly([(-12,-43),(2,-45),(16,-43),(12,-34),(-2,-30),(-12,-35)],'#658591')
     for off in [-9,-4,1,6]:poly([(off,-41),(off+2,-41),(off+2,-34),(off,-35)],'#142a31')
     # correct purple plume flowing back from crown
     poly([(0,-59),(0,-68),(8,-77),(15,-76),(17,-70),(13,-62),(8,-55)],'#442775');poly([(0,-68),(8,-77),(15,-76),(9,-68),(7,-58)],'#703fa1')
     add('</g>')
     # Dragon scimitar: trace the equipped idle silhouette in the user-supplied Sever.gif.
     # The grip stays low at the waist. Cutting edge faces outward; the broad hooked
     # back of the blade rises above the wrist, like the first and last GIF frames.
     # Grip shaft and quillons are drawn first; the gauntlet is redrawn over the grip.
     path('M31-4l-10 11','none',stroke='#514e4d',stroke_width=3.5)
     poly([(18,6),(22,6),(23,8),(19,10),(16,9)],'#6f6c68')
     poly([(29,-1),(42,-10.4),(48.8,-21.7),(49.5,-32.7),(55.8,-32.9),(60.5,-35),(65,-38.8),(61.4,-29.4),(59.8,-23.3),(51.9,-12.5),(38.4,-3.7),(30.8,1.7)],'#a62a19')
     poly([(29,-1),(42,-10.4),(48.8,-21.7),(49.5,-32.7),(55.8,-32.9),(60.5,-35),(65,-38.8),(48,-17),(30.8,1.7)],'#c13a23')
     poly([(48,-17),(65,-38.8),(61.4,-29.4),(59.8,-23.3),(51.9,-12.5),(38.4,-3.7),(30.8,1.7)],'#8e2017')
     poly([(23,-10),(24,-8),(28,-7),(35,0),(40,1),(39,5),(36,4),(29,-2),(24,-4),(21,-4),(21,-7)],'#686765')
     poly([(23,-10),(24,-8),(28,-7),(35,0),(40,1),(39,2),(33,-1),(27,-5),(22,-6)],'#85827c')
     poly([(25,-1),(27,-4),(31,-2),(32,1),(28,4),(25,2)],'#618793')
     path('M27-1l3 2','none',stroke='#3d616e',stroke_width=.8)
     endmotion()
     add('</g>')
    # Wizard: familiar bent blue hat, blue robe/skirt, grey beard, brown boots.
    def wizard(x,y,s=1):
     add(f'<g transform="translate({x} {y}) scale({s})">')
     add('<ellipse cx="4" cy="16" rx="22" ry="11" fill="#263b26" opacity=".3"/>')
     poly([(-10,12),(-4,14),(-7,23),(-17,23),(-15,19)],'#594329');poly([(5,12),(12,14),(18,20),(15,24),(5,22)],'#594329')
     poly([(-12,-12),(11,-13),(17,14),(3,21),(-17,13)],'#244f85');poly([(-12,-12),(-2,-10),(-5,17),(-17,13)],'#366b9a');poly([(-2,-10),(11,-13),(17,14),(3,21)],'#1b4278')
     poly([(-1,-1),(3,16),(-5,17)],'#3b74b5')
     poly([(-13,-34),(-3,-39),(10,-37),(16,-29),(10,-11),(-11,-11),(-17,-28)],'#25577f');poly([(-13,-34),(-3,-39),(-2,-12),(-11,-11),(-17,-28)],'#3b7397')
     path('M-11-11l11 2 9-3','none',stroke='#65371e',stroke_width=3)
     for yy in [-31,-27,-23]:path(f'M-3 {yy}l5 3m-5 0 5-3','none',stroke='#693b24',stroke_width=1.4)
     poly([(-16,-30),(-23,-24),(-27,-8),(-18,-6),(-11,-23)],'#2c608b')
     poly([(-25,-9),(-19,-7),(-19,-2),(-25,1),(-28,-3)],'#bd9767')
     path('M-25-8l6 2m-3 0 5-1','none',stroke='#8d9189',stroke_width=3)
     poly([(-9,-49),(1,-55),(10,-49),(9,-39),(1,-32),(-8,-38)],'#c59b68');poly([(2,-47),(10,-49),(9,-39),(1,-32),(2,-41)],'#99734c')
     poly([(-7,-39),(1,-40),(7,-38),(4,-32),(-2,-31),(-6,-34)],'#bd9362')
     # distinctive soft, bent conical wizard hat with wide floppy brim
     poly([(-17,-49),(-8,-57),(-4,-65),(0,-78),(8,-82),(12,-76),(7,-65),(8,-57),(18,-49),(9,-44),(-5,-47)],'#205c8a')
     poly([(-17,-49),(-8,-57),(-4,-65),(0,-78),(8,-82),(5,-71),(-1,-57),(-4,-48)],'#357cac');poly([(5,-71),(8,-82),(12,-76),(7,-65),(8,-57),(18,-49),(9,-44),(3,-54)],'#17446f')
     motion('wizard-cast', 13, -31)
     poly([(13,-31),(20,-26),(23,-9),(15,-6),(10,-23)],'#1c466f')
     poly([(16,-7),(22,-7),(24,-2),(18,2),(15,-1)],'#bc9568')
     endmotion()
     # Faceted spell states follow the inspected High Alchemy capture: the
     # character holds one casting pose while polygonal light changes size.
     motion('wizard-glow', -15, -29, transient=True)
     poly([(-34,-29),(-28,-43),(-14,-48),(0,-40),(5,-27),(-3,-14),(-19,-10),(-32,-17)],'#d7b52e',opacity=.35)
     poly([(-28,-29),(-24,-39),(-15,-42),(-5,-36),(-2,-27),(-8,-18),(-18,-16),(-27,-21)],'#f0d64b',opacity=.5)
     poly([(-22,-30),(-16,-36),(-8,-31),(-11,-23),(-20,-23)],'#fff3a0',opacity=.8)
     endmotion()
     add('</g>');firestaff(x-24*s,y-4*s,s)
    # Hunched goblin with green nose/ears, topknot, grey armour and beige tunic.
    def goblin(x,y,s=1,flip=False):
     add(f'<g transform="translate({x} {y}) scale({-s if flip else s} {s})">')
     add('<ellipse cx="4" cy="16" rx="24" ry="12" fill="#263b26" opacity=".27"/>')
     poly([(-14,-2),(-4,1),(-10,10),(-12,20),(-19,20),(-21,11)],'#6b9946');poly([(7,-1),(17,-3),(22,9),(17,19),(10,17),(13,8)],'#608e3d')
     poly([(-18,16),(-10,18),(-11,24),(-27,24),(-23,20)],'#7fac4a');poly([(11,15),(18,15),(24,20),(26,25),(11,23)],'#6d9c40')
     poly([(-18,-18),(8,-25),(22,-8),(17,4),(-2,7),(-19,-1)],'#b1a88b');poly([(-18,-18),(-7,-15),(-2,7),(-19,-1)],'#8f856c');poly([(-2,7),(17,4),(18,9),(-4,13),(-20,4),(-19,-1)],'#775524')
     poly([(-20,-30),(-28,-24),(-32,-10),(-26,-1),(-22,-15),(-12,-24)],'#679c48');poly([(17,-26),(26,-18),(29,-5),(22,5),(19,-4),(19,-14)],'#719f47')
     poly([(-28,-12),(-21,-8),(-25,1),(-30,3),(-34,-5)],'#8c9185');poly([(22,-5),(30,-5),(29,4),(21,8),(18,3)],'#888e81')
     poly([(-30,1),(-24,0),(-22,9),(-26,14),(-30,7)],'#6a9d43');poly([(21,7),(27,4),(26,14),(21,18),(19,13)],'#6a9d43')
     poly([(-18,-33),(-8,-41),(7,-39),(14,-27),(8,-15),(-6,-17),(-20,-25)],'#7bab4e');poly([(-8,-41),(7,-39),(14,-27),(8,-15),(-3,-20)],'#669745')
     # broad nose, very long pointy ears and narrowed white eyes
     poly([(-19,-30),(-6,-24),(-14,-17),(-27,-23)],'#83b350');poly([(-6,-24),(-14,-17),(-8,-14),(4,-21)],'#507f38')
     poly([(-17,-33),(-28,-43),(-25,-27),(-17,-24)],'#76a648');poly([(8,-36),(21,-44),(15,-27),(10,-25)],'#5c8f3a')
     poly([(-17,-28),(-9,-27),(-13,-24)],'#d9e2cb');poly([(-1,-27),(5,-30),(4,-25)],'#d9e2cb')
     # angular steel shoulders and brown topknot
     poly([(-15,-24),(-26,-30),(-27,-22),(-22,-16),(-13,-18)],'#93968c');poly([(11,-31),(20,-29),(27,-19),(23,-13),(13,-18)],'#92948a')
     poly([(-6,-40),(-10,-50),(-5,-59),(2,-59),(7,-50),(3,-40)],'#605a28');poly([(-5,-59),(2,-59),(7,-50),(3,-40),(1,-49)],'#433d1f')
     add('</g>')
    # Characters occupy normal game-world scale and do not overlap any day tiles.
    woodcutter(425,242,1.04)
    goblin(699,148,.85);goblin(1257,335,.85,True)
    wizard(1125,278,1.10)
    player(780,684,1.4)
    cow(709,867,.88)
    # Foreground scenery, modest context and no dashboard frame.
    for x,y,s in [(109,798,1.02),(1356,552,.85),(170,936,.75),(861,952,.67)]:oak(x,y,s)
    # A campfire, log and stones by the player's path.
    for x,y,s in [(797,750,.4),(827,743,.35),(840,766,.38),(808,781,.32)]:rock(x,y,s)
    path('M800 769l32-10m-25-11 21 29','none',stroke='#72512d',stroke_width=8)
    motion('campfire-flame', 817, 771, delay=-.3)
    poly([(804,762),(808,748),(816,740),(814,754),(827,746),(830,759),(822,771),(811,772)],'#c57431');poly([(811,765),(816,751),(818,760),(823,756),(821,768)],'#e1b454')
    endmotion()
    # Smithing corner fills the previous statistics clearing.
    # A weathered working apron paved with uneven gray slabs.
    poly([(248,676),(613,691),(641,886),(221,871)],'#676d54')
    poly([(253,682),(605,697),(632,877),(230,863)],'#82846a')
    rr=random.Random(133)
    for row in range(5):
     for col in range(8):
      xx=242+col*47+row*1.3;yy=686+row*35
      poly([(xx,yy),(xx+43,yy+2),(xx+45,yy+32),(xx-3,yy+29)],rr.choice(['#7c8067','#898973','#777e67','#8c8c73']))
    # The rear rail makes this read as a village smithing station rather than a card.
    path('M226 663l353 13m-353 0 353 13','none',stroke='#5c4729',stroke_width=5)
    path('M226 661l353 13','none',stroke='#927145',stroke_width=1.7)
    for xx in [226,296,366,436,506,579]:fencepost(xx,681+(xx-226)*.037)
    # Actual-style tapered brick furnace: dark open chimney, gray bands, glowing firebox.
    add('<g transform="translate(324 799)">')
    poly([(-62,19),(-15,41),(64,26),(39,-10)],'#34472c',opacity=.35)
    poly([(-47,-83),(23,-71),(27,14),(-44,0)],'#7f452b')
    poly([(23,-71),(58,-94),(61,-9),(27,14)],'#633922')
    poly([(-47,-83),(-12,-106),(58,-94),(23,-71)],'#aaa893')
    poly([(-44,-79),(20,-68),(23,8),(-41,-4)],'#713d29')
    for yy in [-59,-38,-17]:path(f'M-44 {yy}l66 12','none',stroke='#985c39',stroke_width=2)
    for xx,yy in [(-22,-78),(2,-57),(-21,-38),(2,-17)]:path(f'M{xx} {yy}v19','none',stroke='#945634',stroke_width=2)
    for yy in [-80,-58,-36]:path(f'M26 {yy}l32-20','none',stroke='#885236',stroke_width=1.6)
    poly([(-34,-58),(-22,-70),(4,-65),(14,-51),(14,-15),(-36,-24)],'#99958a')
    poly([(-29,-55),(-19,-63),(0,-60),(8,-49),(8,-21),(-30,-28)],'#282a22')
    add('<g class="firebox-motion-clip">')
    motion('furnace-flame', -11, -25)
    poly([(-28,-28),(-28,-40),(-23,-47),(-17,-39),(-10,-56),(-1,-42),(5,-49),(6,-23)],'#c96a23')
    poly([(-23,-29),(-18,-43),(-11,-36),(-7,-51),(-1,-39),(3,-26)],'#efb735')
    poly([(-16,-31),(-10,-42),(-7,-33),(-1,-28)],'#ffe775')
    endmotion()
    add('</g>')
    add('<g clip-path="url(#firebox-clip)">')
    for xx,yy,delay in [(-15,-33,0),(-3,-32,-1.8)]:
     add(f'<g class="motion transient furnace-ember" style="animation-delay:{delay}s">')
     rect(xx,yy,2.5,3,'#ffd979')
     add('</g>')
    add('</g>')
    path('M-35-21l48 9','none',stroke='#575c55',stroke_width=3)
    # Tall tapering flue with a clearly visible square chimney opening.
    poly([(-38,-89),(-19,-160),(13,-152),(27,-77)],'#78482e')
    poly([(13,-152),(37,-170),(49,-96),(27,-77)],'#583a28')
    poly([(-19,-160),(4,-177),(37,-170),(13,-152)],'#a09d91')
    poly([(-12,-160),(5,-171),(28,-167),(12,-157)],'#20251f')
    path('M-31-118l51 10m-44-37 39 9M-5-154l-5 69','none',stroke='#925d3e',stroke_width=2)
    path('M20-125l24-18','none',stroke='#795137',stroke_width=1.5)
    poly([(-50,-86),(-13,-110),(61,-98),(60,-92),(24,-69),(-49,-81)],'#8e9187')
    poly([(-50,-86),(23,-74),(61,-98),(24,-69),(-49,-81)],'#b0ad96')
    add('</g>')
    # Coal lumps, wooden-handled shovel and a stack of newly cast bars.
    poly([(381,786),(393,768),(417,762),(441,776),(448,794),(412,804)],'#363b32')
    for xx,yy in [(395,782),(414,777),(431,785),(414,792)]:
     poly([(xx-7,yy+3),(xx-5,yy-7),(xx+3,yy-10),(xx+8,yy-2),(xx+4,yy+6)],'#53584c')
    path('M447 789l-4-55','none',stroke='#826127',stroke_width=5)
    path('M442 737l-7-8 2-10 10-1 4 8-8 10','none',stroke='#947032',stroke_width=3)
    poly([(442,781),(451,780),(454,796),(447,805),(438,799)],'#adb0a0')
    for xx,yy in [(274,840),(295,844),(284,828)]:
     poly([(xx,yy),(xx+7,yy-5),(xx+28,yy-1),(xx+24,yy+5)],'#adbfc0')
     poly([(xx,yy),(xx+24,yy+5),(xx+24,yy+10),(xx,yy+5)],'#658187')
     poly([(xx+24,yy+5),(xx+28,yy-1),(xx+28,yy+5),(xx+24,yy+10)],'#50666d')
    # A compact blue-gray anvil on the rooted block from Otto's Grotto.
    add('<g transform="translate(487 831)">')
    add('<ellipse cx="0" cy="26" rx="49" ry="20" fill="#32432d" opacity=".3"/>')
    poly([(-25,0),(-35,16),(-28,32),(-4,40),(24,33),(31,13),(24,-1)],'#63472c')
    poly([(-25,0),(-35,16),(-28,32),(-18,21),(-14,4)],'#8c6337')
    poly([(-25,0),(-5,-9),(24,-1),(31,13),(11,23),(-18,21),(-35,16)],'#b69960')
    path('M-24 11l17-11 21 8 2 10-17 1-13-7z','none',stroke='#8c7148',stroke_width=1.5)
    poly([(-23,-4),(15,-1),(26,8),(20,14),(-18,10),(-28,3)],'#434d54')
    poly([(-11,-26),(10,-24),(9,-9),(21,3),(-20,0),(-10,-10)],'#55616a')
    poly([(-9,-25),(-2,-24),(-1,-8),(-19,0),(-10,-10)],'#7c8790')
    poly([(-30,-38),(13,-35),(38,-30),(21,-20),(-27,-24),(-52,-29)],'#7b8b94')
    poly([(-52,-29),(-27,-24),(21,-20),(21,-12),(-27,-16),(-43,-22)],'#48555e')
    poly([(-30,-38),(13,-35),(38,-30),(18,-28),(-25,-31)],'#a1afb3')
    # A hot blank and two tiny sparks catch the light.
    poly([(-10,-34),(10,-31),(8,-27),(-14,-29)],'#d77334')
    poly([(-9,-34),(10,-31),(7,-29),(-11,-32)],'#f4b94b',id='smith-hot-blank')
    add('</g>')
    # Horvik-inspired human smith: ochre cap, leather apron, gloves and raised hammer.
    add('<g transform="translate(555 804) scale(1.27)">')
    add('<ellipse cx="3" cy="27" rx="26" ry="12" fill="#2b3c27" opacity=".3"/>')
    poly([(-12,-3),(-1,0),(-7,22),(-14,28),(-20,23)],'#4d432b')
    poly([(0,0),(13,-5),(13,17),(21,26),(14,30),(5,19)],'#655335')
    poly([(-18,22),(-11,25),(-16,32),(-30,31),(-29,28)],'#4a3826')
    poly([(13,25),(20,24),(29,31),(26,35),(13,32)],'#4d3927')
    # Lean into the stroke around the waist; feet and shadow remain planted.
    motion('smith-body', 0, -5)
    poly([(-14,-47),(-4,-53),(11,-48),(19,-33),(13,-8),(-12,-7),(-21,-30)],'#64462b')
    poly([(-10,-48),(3,-48),(12,-7),(17,8),(-12,13),(-17,-5)],'#9b682c')
    poly([(-10,-48),(-6,-49),(-7,-15),(-12,13),(-17,-5)],'#b3823b')
    path('M-8-45l4 21m8-22 2 16','none',stroke='#c99543',stroke_width=2)
    poly([(10,-46),(20,-36),(24,-24),(17,-20),(9,-32)],'#b08a5b')
    poly([(17,-23),(24,-24),(21,-8),(14,-1),(10,-6)],'#6f4b2b')
    # Shoulder and waist together bring the hammer down onto the hot blank.
    motion("smith-arm", -17, -45)
    # Raised, bent left arm and hammer above the glowing blank.
    poly([(-16,-41),(-24,-34),(-30,-42),(-26,-49),(-17,-50)],'#b48d5c')
    # A long wooden shaft passes through the palm. Its short butt extends
    # below the fist; the steel head is a separate object at the far end.
    add('<g id="smith-hammer" data-local-grip="0 0" transform="translate(-29 -53) rotate(-27)">')
    path('M0 5V-29','none',stroke='#6e4c28',stroke_width=4.5,stroke_linecap='square',data_part='handle')
    path('M-.7 4V-28','none',stroke='#ae854b',stroke_width=1.4)
    poly([(-11,-31),(-8,-35),(9,-33),(11,-26),(7,-23),(-10,-25)],'#78848b',data_part='head')
    poly([(-11,-31),(-8,-35),(9,-33),(7,-29),(-10,-28)],'#bac1b6')
    poly([(7,-29),(9,-33),(11,-26),(7,-23)],'#4e5e65')
    add('</g>')
    # Draw the glove last so fingers visibly wrap around the shaft.
    poly([(-29,-44),(-35,-50),(-32,-58),(-27,-58),(-23,-51)],'#6e4c2c',data_hand_grip='-29 -53')
    path('M-32-54l5-1m-4 4 5-1','none',stroke='#a27a48',stroke_width=1.2)
    endmotion()
    poly([(-10,-65),(-4,-71),(6,-70),(12,-61),(7,-50),(-3,-49),(-13,-56)],'#c49f68')
    poly([(-10,-65),(-4,-71),(6,-70),(2,-60),(-8,-54),(-13,-56)],'#d6b47b')
    poly([(-12,-65),(-8,-78),(5,-83),(14,-75),(11,-65),(2,-69),(-5,-66)],'#b18a2f')
    poly([(-8,-78),(5,-83),(14,-75),(2,-75),(-12,-65)],'#d3ad42')
    poly([(-12,-62),(-15,-58),(-10,-57),(-5,-51),(-3,-57)],'#b48c5b')
    path('M-10-62l3 1','none',stroke='#3b3426',stroke_width=1.5)
    endmotion()
    add('</g>')
    # A small pair of warm chips follows the actual contact, then fades away.
    for xx,yy in [(487,798),(490,799)]:
     add('<g class="motion transient smith-spark">')
     rect(xx,yy,2.5,2,'#ffcd66')
     add('</g>')
    # Small plain smithy supply barrel and ingot crate.
    add('<g transform="translate(613 733)">')
    poly([(-17,-23),(-20,-12),(-18,18),(-6,25),(13,22),(20,12),(18,-18)],'#76572f')
    poly([(-17,-23),(-4,-28),(12,-25),(18,-18),(7,-11),(-11,-13)],'#a2854d')
    path('M-18-8l10 5 24-5m-33 20 12 6 23-6','none',stroke='#646c5a',stroke_width=4)
    path('M-7-12v33m12-32v31','none',stroke='#503d27',stroke_width=1.5)
    add('</g>')
    for xx,yy in [(227,900),(636,923),(730,942)]:flowers(xx,yy,.8)

    add('</g>')
    # A separate, reference-based quest-tab interface, without hiding any day tiles.
    rect(0,0,1400,1000,'url(#vignette)')
    # Self-contained pixel glyphs: no font downloads, embedded rasters or script dependencies.
    FONT={
    'A':['01110','10001','10001','11111','10001','10001','10001'],
    'B':['11110','10001','10001','11110','10001','10001','11110'],
    'C':['01111','10000','10000','10000','10000','10000','01111'],
    'D':['11110','10001','10001','10001','10001','10001','11110'],
    'E':['11111','10000','10000','11110','10000','10000','11111'],
    'F':['11111','10000','10000','11110','10000','10000','10000'],
    'G':['01111','10000','10000','10111','10001','10001','01111'],
    'H':['10001','10001','10001','11111','10001','10001','10001'],
    'I':['111','010','010','010','010','010','111'],
    'J':['00111','00010','00010','00010','10010','10010','01100'],
    'K':['10001','10010','10100','11000','10100','10010','10001'],
    'L':['10000','10000','10000','10000','10000','10000','11111'],
    'M':['10001','11011','10101','10101','10001','10001','10001'],
    'N':['10001','11001','11001','10101','10011','10011','10001'],
    'O':['01110','10001','10001','10001','10001','10001','01110'],
    'P':['11110','10001','10001','11110','10000','10000','10000'],
    'Q':['01110','10001','10001','10001','10101','10010','01101'],
    'R':['11110','10001','10001','11110','10100','10010','10001'],
    'S':['01111','10000','10000','01110','00001','00001','11110'],
    'T':['11111','00100','00100','00100','00100','00100','00100'],
    'U':['10001','10001','10001','10001','10001','10001','01110'],
    'V':['10001','10001','10001','10001','10001','01010','00100'],
    'W':['10001','10001','10001','10101','10101','10101','01010'],
    'X':['10001','10001','01010','00100','01010','10001','10001'],
    'Y':['10001','10001','01010','00100','00100','00100','00100'],
    'Z':['11111','00001','00010','00100','01000','10000','11111'],
    'a':['00000','00000','01110','00001','01111','10001','01111'],
    'b':['10000','10000','10110','11001','10001','10001','11110'],
    'c':['0000','0000','0111','1000','1000','1000','0111'],
    'd':['00001','00001','01101','10011','10001','10001','01111'],
    'e':['00000','00000','01110','10001','11111','10000','01111'],
    'f':['0011','0100','1110','0100','0100','0100','0100'],
    'g':['00000','00000','01111','10001','01111','00001','11110'],
    'h':['10000','10000','10110','11001','10001','10001','10001'],
    'i':['1','0','1','1','1','1','1'],
    'j':['001','000','001','001','001','101','010'],
    'k':['1000','1000','1001','1010','1100','1010','1001'],
    'l':['10','10','10','10','10','10','01'],
    'm':['00000','00000','11010','10101','10101','10101','10101'],
    'n':['00000','00000','10110','11001','10001','10001','10001'],
    'o':['00000','00000','01110','10001','10001','10001','01110'],
    'p':['00000','00000','11110','10001','11110','10000','10000'],
    'q':['00000','00000','01111','10001','01111','00001','00001'],
    'r':['0000','0000','1011','1100','1000','1000','1000'],
    's':['00000','00000','01111','10000','01110','00001','11110'],
    't':['0100','0100','1110','0100','0100','0101','0010'],
    'u':['00000','00000','10001','10001','10001','10011','01101'],
    'v':['00000','00000','10001','10001','10001','01010','00100'],
    'w':['00000','00000','10001','10001','10101','10101','01010'],
    'x':['00000','00000','10001','01010','00100','01010','10001'],
    'y':['00000','00000','10001','10001','01111','00001','11110'],
    'z':['00000','00000','11111','00010','00100','01000','11111'],
    '0':['01110','10001','10011','10101','11001','10001','01110'],
    '1':['010','110','010','010','010','010','111'],
    '2':['01110','10001','00001','00010','00100','01000','11111'],
    '3':['11110','00001','00001','01110','00001','00001','11110'],
    '4':['00010','00110','01010','10010','11111','00010','00010'],
    '5':['11111','10000','10000','11110','00001','00001','11110'],
    '6':['01110','10000','10000','11110','10001','10001','01110'],
    '7':['11111','00001','00010','00100','01000','01000','01000'],
    '8':['01110','10001','10001','01110','10001','10001','01110'],
    '9':['01110','10001','10001','01111','00001','00001','01110'],
    ' ':['000']*7,',':['00','00','00','00','00','01','10'],
    '-':['000','000','000','111','000','000','000'],
    '+':['00000','00100','00100','11111','00100','00100','00000'],
    ':':['0','1','1','0','1','1','0'],
    '/':['00001','00001','00010','00100','01000','10000','10000']}
    def pxwidth(t,u):return sum((len(FONT[c][0])+1)*u for c in t)-u
    def pxtext(x,y,t,u,c,align='left'):
     if align=='right':x-=pxwidth(t,u)
     if align=='center':x-=pxwidth(t,u)/2
     p=[];xx=x
     for ch in t:
      glyph=FONT[ch]
      for iy,row in enumerate(glyph):
       ix=0
       while ix<len(row):
        if row[ix]=='0':ix+=1;continue
        end=ix+1
        while end<len(row) and row[end]=='1':end+=1
        bx=xx+ix*u;by=y+iy*u;ww=(end-ix)*u
        p.append(f'M{bx:.2f} {by:.2f}h{ww:.2f}v{u:.2f}h{-ww:.2f}z');ix=end
      xx+=(len(glyph[0])+1)*u
     add(f'<g role="img" aria-label="{t}" data-ui-text="{t}"><title>{t}</title>')
     path(''.join(p),'#16130d',transform='translate(1.6 1.8)')
     path(''.join(p),c)
     add('</g>')
    def bevel(x,y,w,h,fill='#554d3c',light='#a19a7d',dark='#272921',b=3):
     rect(x,y,w,h,dark)
     poly([(x,y),(x+w,y),(x+w-b,y+b),(x+b,y+b),(x+b,y+h-b),(x,y+h)],light)
     poly([(x+w,y),(x+w,y+h),(x,y+h),(x+b,y+h-b),(x+w-b,y+h-b),(x+w-b,y+b)],dark)
     rect(x+b,y+b,w-2*b,h-2*b,fill)
    def queststar(x,y,s,c):
     pts=[]
     for i in range(16):
      a=-math.pi/2+i*math.pi/8;r=s if i%2==0 else s*.47
      pts.append((x+math.cos(a)*r,y+math.sin(a)*r))
     poly(pts,'#1f2221',stroke='#191d17',stroke_width=3)
     poly(pts,c)
     poly([(x,y-s*.75),(x+s*.3,y-s*.15),(x+s*.75,y),(x,y+s*.2),(x-s*.3,y)],'#dee4cb',opacity=.42)
     path(f'M{x} {y-s*.65}v{s*1.3}m{-s*.65} {-s*.65}h{s*1.3}','none',stroke='#182338',stroke_width=1,opacity=.5)
    # OSRS quest sidebar, drawn after the world like the real in-game interface.
    add('<g id="quest-log" aria-label="Quest-list-styled contribution statistics">')
    rect(966,608,417,376,'#18241b',opacity=.38)
    bevel(957,597,418,376,'#514b3d','#a4a18c','#24271f',5)
    # Pillared stone side rails with tiny bevels and mortar joints.
    for xx in [958,1358]:
     bevel(xx,610,17,348,'#746f5c','#a09b80','#3a3c31',3)
     for yy in range(643,950,41):
      path(f'M{xx+2} {yy}h13','none',stroke='#393e32',stroke_width=2)
      path(f'M{xx+3} {yy+2}h10','none',stroke='#9c987e',stroke_width=1)
     for dx in [5,12]:path(f'M{xx+dx} 618V950','none',stroke='#514f40',stroke_width=1)
    # Four category tabs; the blue quest star is selected.
    for i,cc in enumerate(['#728bed','#5dba66','#bf5149','#8842b8']):
     xx=976+i*95
     bevel(xx,606,94,40,'#665b45' if i==0 else '#494637','#9a9071','#292d25',3)
     if i==0:rect(xx+5,640,84,6,'#665b45')
     queststar(xx+47,625,12,cc)
    pxtext(1166,658,'Quest List',3.1,'#ffb83f','center')
    # Dark recessed list field, with worn metal/stone edge.
    bevel(978,691,375,218,'#252a24','#302f27','#9a9279',3)
    bevel(983,696,365,208,'#3f392d','#171d19','#77735f',2)
    rr=random.Random(77)
    for i in range(200):
     xx=rr.randint(987,1322);yy=rr.randint(700,900)
     rect(xx,yy,rr.choice([1,2,3]),1,rr.choice(['#464032','#4a4334','#342f27']),opacity=.35)
    # Scrollbar in the exact quest-panel idiom: bronze thumb, inset rail, black arrows.
    bevel(1327,699,18,202,'#26271f','#11180f','#a39773',2)
    bevel(1328,700,16,19,'#8b8264','#b2a889','#3e4032',2)
    poly([(1331,711),(1336,705),(1341,711),(1338,711),(1338,715),(1334,715),(1334,711)],'#22291e')
    bevel(1329,721,14,43,'#807b5d','#b4ac89','#484b38',2)
    path('M1332 738h8m-8 4h8m-8 4h8','none',stroke='#aaa17e',stroke_width=1)
    bevel(1328,881,16,19,'#8b8264','#b2a889','#3e4032',2)
    poly([(1331,887),(1334,887),(1334,883),(1338,883),(1338,887),(1341,887),(1336,894)],'#22291e')
    # Four genuine statistics as readable quest-list entries, not invented game progress.
    for yy,label,value,col in [(710,'Contributions',f"{STATS['total']:,}",'#5fdf32'),(758,'Active days',str(STATS['activeDays']),'#5fdf32'),(806,'Best streak',str(STATS['bestStreak']),'#5fdf32'),(854,'Current streak',str(STATS['currentStreakAllowTodayPending']),'#fff253')]:
     pxtext(994,yy+6,label,2.7,col)
     pxtext(1314,yy,value,min(4.2, 137 / pxwidth(value,1)),'#e9ef77' if yy!=854 else '#ffec52','right')
     if yy in [806,854]:pxtext(1314,yy+32,'days',1.35,'#c4b994','right')
    pxtext(994,885,STREAK_NOTE,1.45,'#cbbd91')
    pxtext(1165,921,DATE_RANGE,min(1.55, 355 / pxwidth(DATE_RANGE,1)),'#e6b45b','center')
    # Discreet legend retains the six count bins for reading the garden's heights/colors.
    pxtext(990,946,'Per day',1.15,'#c4b88f')
    for i,lab in enumerate(['0','1-3','4-7','8-15','16-31','32+']):
     xx=1049+i*47
     rect(xx,944,9,9,C[i][0],stroke='#b2a577',stroke_width=.6)
     pxtext(xx+13,945,lab,1.02,'#d5cda9')
    add('</g>')
    add('</svg>')
    return '\n'.join(S)



def render(DATA):
    """Render current contribution data, then apply approved crossover scenery."""
    from crossover import apply
    return apply(render_base(DATA))
