"""Private held-pose creature and shadow-clone rigs; no I/O or external assets."""
from xml.etree import ElementTree as ET
from .creatures import sprites as c
from . import refined_visitors as v
from .motion_runtime import motion,track

I='translate(0px,0px)'
def T(seq):
    return track([(0,I,1)]+seq+[(28.8,I,1)])
def visible(seq):
    return track([(0,I,0)]+[(t,I,o) for t,o in seq]+[(28.8,I,0)])
TRACKS={
 'world-alexander-tap':T([(4.4,'rotate(32deg)',1),(4.58,'rotate(78deg)',1),(4.82,'rotate(61deg)',1),(5.02,'rotate(82deg)',1),(5.24,'rotate(62deg)',1),(5.5,'rotate(28deg)',1),(5.7,I,1)]),
 'world-murloc-step':T([(10.8,'translate(3px,0px)',1),(11,'translate(7px,0px)',1),(11.2,'translate(9px,0px)',1),(12.02,'translate(6px,0px)',1),(12.22,'translate(3px,0px)',1),(12.4,I,1)]),
 'world-murloc-left-foot':T([(10.8,'translate(4px,-3px)',1),(11,I,1),(12.22,'translate(-4px,-3px)',1),(12.4,I,1)]),
 'world-murloc-right-foot':T([(11,'translate(3px,-2px)',1),(11.2,I,1),(12.02,'translate(-4px,-3px)',1),(12.22,I,1)]),
 'world-murloc-spear':T([(11.15,'rotate(-18deg)',1),(11.35,'rotate(-37deg)',1),(11.85,'rotate(-18deg)',1),(12.02,I,1)]),
 'world-creeper-peek':T([(21.8,'rotate(4deg)',1),(22,'rotate(9deg)',1),(22.9,'rotate(5deg)',1),(23.15,'rotate(2deg)',1),(23.4,I,1)]),
 'world-creeper-head':T([(22.2,'rotate(-9deg)',1),(22.65,'rotate(-4deg)',1),(22.9,I,1)]),
 'world-naruto-rest':track([(0,I,1),(12.8,I,0),(15.4,I,1),(28.8,I,1)]),
 'world-naruto-seal-a':visible([(12.8,1),(13.1,0),(13.4,1),(13.7,0),(14,1),(15.4,0)]),
 'world-naruto-seal-b':visible([(13.1,1),(13.4,0),(13.7,1),(14,0)]),
 'world-naruto-clone':visible([(14.2,.86),(15.08,0)]),
 'world-naruto-poof':track([(0,I,0),(14,'scale(.72)',.30),(14.1,'scale(1)',.48),(14.2,'scale(1.12)',.22),(14.3,I,0),(15.02,'scale(.8)',.24),(15.08,'scale(1)',.44),(15.2,'scale(1.12)',.2),(15.35,I,0),(28.8,I,0)]),
}
def xml(n):return ET.tostring(n,encoding='unicode')
def pieces(fn):return list(ET.fromstring(fn(0,0,1)))
def pack(nodes):return ''.join(xml(n) for n in nodes)
def outer(id,label,x,y,s,content):
    return f'<g id="{id}" aria-label="{label}" transform="translate({x:g} {y:g}) scale({s:g})">{content}</g>'
def poly(d,col):return f'<path d="{d}" fill="{col}"/>'

def alexander(x,y,s=1):
    a=pieces(c.alexander)
    # The whole right hand/forearm remains a single rigid shoulder assembly.
    # Bringing it in front of the jar makes each chest contact visible.
    body=pack(a[:9])+pack(a[13:])
    arm=motion('world-alexander-tap',pack(a[9:13]),28,-60)
    return outer('crossover-alexander','Alexander proudly taps his terracotta chest',x,y,s,body+arm)

def murloc(x,y,s=1):
    a=pieces(c.murloc)
    # Wooden shaft runs through the fist at (22,-18); stone point is separate.
    spear='<path d="M2 2L44-47" fill="none" stroke="#6e5434" stroke-width="3.2"/>'
    spear+='<path d="M3 1L44-47" fill="none" stroke="#b0915b" stroke-width="1"/>'
    spear+=poly('M41-46L39-53L50-59L49-47L45-44Z','#85958a')
    spear+=poly('M41-46L39-53L50-59L43-50Z','#bac4ae')
    spear+='<path d="M39-45l3 3m-5-1 3 3m-5-1 3 3" fill="none" stroke="#c5b277" stroke-width="1.4"/>'
    # Arm is behind the shaft, the fingers are in front: a literal closed grip.
    arm=xml(a[16])+spear+poly('M18-22L24-23L26-19L24-15L19-15L16-19Z','#aab05b')+poly('M18-22L24-23L25-20L19-19L16-19Z','#c2be6a')
    upper=pack(a[1:4])+motion('world-murloc-left-foot',pack(a[4:7]))+motion('world-murloc-right-foot',pack(a[7:10]))+pack(a[10:16])+pack(a[18:])
    upper+=motion('world-murloc-spear',arm,18,-36)
    whole=xml(a[0])+upper
    return outer('crossover-murloc','Murloc shuffles along the bank and lifts its spear',x,y,s,motion('world-murloc-step',whole))

def creeper(x,y,s=1):
    a=pieces(c.creeper)
    feet=pack(a[:9])+pack(a[36:])
    body=pack(a[9:19])+motion('world-creeper-head',pack(a[19:36]),1,-51)
    return outer('crossover-creeper','A curious Creeper peeks around the garden',x,y,s,feet+motion('world-creeper-peek',body,1,-15))

def naruto(x,y,s=1):
    v.parts=[];v.naruto(0,0,1);a=list(ET.fromstring(''.join(v.parts)))
    # Shoulder endpoints remain unchanged in every arm drawing.
    rest=xml(a[18])+poly('M24-53L19-47L11-34L6-38L14-51Z','#c98432')
    rest+=poly('M11-36L7-39L2-36L2-31L8-29L13-32Z','#c3a174')
    rest+=xml(a[22])+poly('M-23-54L-18-48L-8-35L-11-30L-18-34L-25-46Z','#dc9340')
    rest+=poly('M-11-35L-6-37L0-33L0-29L-7-28L-13-31Z','#d6b684')
    seal_a=pack(a[18:25])
    # Second hand sign changes the hand silhouette, not a detached wrist offset.
    seal_b=pack(a[18:24])
    seal_b+=poly('M-5-57L-1-62L4-61L7-57L4-52L-1-51L-5-54Z','#c9a778')
    seal_b+=poly('M-2-59L-9-64L-9-67L-6-67L1-61L5-66L8-65L7-61L2-55Z','#dbbd89')
    seal_b+='<path d="M-5-63l7 7m3-7-4 6" fill="none" stroke="#a1845c" stroke-width=".8"/>'
    core=pack(a[:18])+motion('world-naruto-rest',rest)+motion('world-naruto-seal-a',seal_a,transient=True)+motion('world-naruto-seal-b',seal_b,transient=True)+pack(a[25:])
    clone=pack(a[:18])+rest+pack(a[25:])
    # The clone stands on clear grass left of Naruto, away from panel/campfire.
    clone=f'<g transform="translate(-50 18) scale(.9)">{clone}</g>'
    cloud=poly('M-76 20L-86 8L-83-14L-78-23L-82-43L-76-56L-66-72L-62-86L-52-93L-38-85L-33-68L-26-58L-24-37L-31-26L-26-6L-32 10L-44 12L-52 24L-65 21Z','#aaa88c')
    cloud+=poly('M-72 12L-79 1L-75-18L-71-24L-74-42L-68-54L-62-70L-56-83L-48-85L-41-72L-38-59L-32-49L-34-33L-39-23L-33-7L-40 3L-52 5L-59 16Z','#cbc4a2')
    effect=motion('world-naruto-poof',cloud,-54,-30,transient=True)
    return outer('preview-naruto','Naruto makes hand signs and briefly summons a shadow clone',x,y,s,effect+motion('world-naruto-clone',clone,transient=True)+core)
