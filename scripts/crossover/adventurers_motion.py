"""Private native-SVG held-pose actions; source artwork remains read-only.

The motion language follows the discrete poses and long holds visible in the
Jagex net-fishing reference. The rod, yo-yo, and rupee choreography is an
original adaptation, not a copy of an OSRS animation or engine timing.
"""
from copy import deepcopy
from math import cos, sin, radians, hypot, sqrt
from xml.etree import ElementTree as ET
from .adventurers import sprites as base
from .motion_runtime import motion, track, DURATION

TRACKS = {}

def _xml(element, drop_ids=False):
    element = deepcopy(element)
    if drop_ids:
        for node in element.iter():
            node.attrib.pop('id', None)
    return ET.tostring(element, encoding='unicode')

def _parts(nodes, drop_ids=False):
    return ''.join(_xml(node, drop_ids) for node in nodes)

def _group(content, transform=''):
    return '<g'+(f' transform="{transform}"' if transform else '')+'>'+content+'</g>'

def _poly(points, fill, **attrs):
    a=' '.join(f'{k.replace("_","-")}="{v}"' for k,v in attrs.items())
    return '<path d="M'+'L'.join(f'{x:.4f} {y:.4f}' for x,y in points)+f'Z" fill="{fill}" {a}/>'

def _path(d, stroke, width=1, **attrs):
    a=' '.join(f'{k.replace("_","-")}="{v}"' for k,v in attrs.items())
    return f'<path d="{d}" fill="none" stroke="{stroke}" stroke-width="{width}" {a}/>'

def _ellipse(x,y,rx,ry,fill,**attrs):
    a=' '.join(f'{k.replace("_","-")}="{v}"' for k,v in attrs.items())
    return f'<ellipse cx="{x:g}" cy="{y:g}" rx="{rx:g}" ry="{ry:g}" fill="{fill}" {a}/>'

def _segment(a,b,wa,wb,color):
    dx,dy=b[0]-a[0],b[1]-a[1];d=hypot(dx,dy)
    nx,ny=-dy/d,dx/d
    return _poly([(a[0]+nx*wa,a[1]+ny*wa),(b[0]+nx*wb,b[1]+ny*wb),
                  (b[0]-nx*wb,b[1]-ny*wb),(a[0]-nx*wa,a[1]-ny*wa)],color)

def _rotate(point,angle,pivot=(22,-52)):
    x,y=point[0]-pivot[0],point[1]-pivot[1];a=radians(angle)
    return (pivot[0]+x*cos(a)-y*sin(a),pivot[1]+x*sin(a)+y*cos(a))

def _begin(name,x,y,s,label):
    return f'<g id="crossover-{name}" aria-label="{label}" transform="translate({x:g} {y:g}) scale({s:g})">'

def _state_tracks(name, schedule):
    """Mutually exclusive complete action states; idle is reduced-motion fallback."""
    states=sorted(set(state for sec,state in schedule))
    for state in states:
        TRACKS[f'adventurer-{name}-{state}']=track(
            [(sec,'none',1 if value==state else 0) for sec,value in schedule])

def _state(name,state,content):
    return motion(f'adventurer-{name}-{state}',content,transient=state!='idle')

# Every rod pose includes its own hand meshes, exact rod-tip line origin, and
# float endpoint. No hand/tool or line/float is animated independently.
GON_POSES = {
    'back': (-22,(104,-83),0),
    'release': (14,(128,-74),0),
    'settle': (5,(115,-64),0),
    'reel-a': (-8,(108,-66),-2),
    'reel-b': (-8,(108,-66),2),
    'reel-up': (-13,(109,-70),0),
}
GON_SCHEDULE=[(0,'idle'),(6,'back'),(6.3,'release'),(6.6,'settle'),(7.2,'idle'),
              (24,'reel-a'),(24.2,'reel-b'),(24.4,'reel-a'),(24.6,'reel-b'),
              (24.8,'reel-up'),(25.2,'idle'),(DURATION,'idle')]
_state_tracks('gon',GON_SCHEDULE)

def _gon_active(nodes,angle,endpoint,crank):
    # Fixed shoulders. The palms use the same rigid transform as the rod.
    left=_rotate((16,-50),angle);right=_rotate((30,-51),angle)
    elbow_l=(-19,-54);elbow_r=(18,-61)
    arms=''
    arms+=_segment((-14,-69),elbow_l,6,5,'#558b3a')
    arms+=_segment((-16,-68),(-20,-57),2.5,2.5,'#70a64c')
    arms+=_segment(elbow_l,left,5,3.5,'#5f9842')
    arms+=_segment((10,-70),elbow_r,5,4.7,'#3b7131')
    arms+=_segment(elbow_r,right,4.7,3.4,'#548a3b')
    grip=_parts([nodes[31],nodes[32],nodes[35],nodes[36]],True)
    transform=f'rotate({angle:g} 22 -52)'
    rod=_xml(nodes[1],True)
    # Replace the reel crank with a three-position angular hand/crank action.
    if crank:
        reel=_ellipse(31,-51+crank,2.4,2.2,'#c8a775')
        reel+=_path(f'M29 -52L33 {-51+crank}', '#8d7847',1.5)
        grip+=reel
    tip=_rotate((106,-121),angle);ex,ey=endpoint
    control=((tip[0]+ex)/2+8,(tip[1]+ey)/2+5)
    line=_path(f'M{tip[0]:.4f} {tip[1]:.4f}Q{control[0]:.4f} {control[1]:.4f} {ex:g} {ey:g}',
               '#b7c9ab',.8,opacity='.9',data_fishing_tip=f'{tip[0]:.4f},{tip[1]:.4f}',
               data_fishing_endpoint=f'{ex:g},{ey:g}')
    floating=_group(_xml(nodes[3],True),f'translate({ex-107:g} {ey+62:g})')
    return _group(rod,transform)+line+floating+arms+_group(grip,transform)

def gon(x,y,s=1):
    r=ET.fromstring(base.gon(x,y,s));nodes=list(r)
    out=_begin('gon',x,y,s,'Gon Freecss casting, waiting, and reeling a fishing rod')
    out+=_parts(nodes[:1])+_parts(nodes[4:28])
    idle=_parts(nodes[1:4])+_parts(nodes[28:37])
    out+=_state('gon','idle',idle)
    for state,args in GON_POSES.items():out+=_state('gon',state,_gon_active(nodes,*args))
    out+=_parts(nodes[37:])
    return out+'</g>'

# The yo-yo stays on the west/left of Killua, away from Gon's fishing rig.
# A state contains the complete sleeve, hand, tied string, and disc.
KILLUA_POSES={
    'draw':((-23,-50),(-25,-43)),
    'drop':((-31,-57),(-37,-20)),
    'swing':((-32,-57),(-57,-39)),
    'loop':((-33,-61),(-58,-75)),
    'return':((-32,-59),(-53,-43)),
    'catch':((-29,-57),(-30,-50)),
}
KILLUA_SCHEDULE=[(0,'idle'),(15.6,'draw'),(15.85,'drop'),(16.1,'swing'),
                 (16.35,'loop'),(16.65,'return'),(16.95,'drop'),(17.25,'catch'),
                 (17.55,'draw'),(17.8,'idle'),(DURATION,'idle')]
_state_tracks('killua',KILLUA_SCHEDULE)

def _yoyo_hand(hand,disc):
    hx,hy=hand;dx,dy=disc
    arm=_segment((-17,-66),(-25,-59),5,4.2,'#3d4668')
    arm+=_segment((-25,-59),hand,4.2,3.2,'#465271')
    arm+=_segment((-19,-66),(-27,-59),1.5,1.5,'#61708b')
    # The line enters the disc axle; its start is inside the thumb and fingers.
    arm+=_path(f'M{hx:g} {hy:g}L{dx:g} {dy:g}', '#b4c1ba',.95,
               data_yoyo_hand=f'{hx:g},{hy:g}',data_yoyo_axle=f'{dx:g},{dy:g}')
    arm+=_poly([(hx-4,hy-2),(hx,hy-4),(hx+3,hy-2),(hx+3,hy+2),(hx-1,hy+4),(hx-4,hy+1)],'#d0b88e')
    arm+=_poly([(hx-4,hy-2),(hx,hy-4),(hx+3,hy-2),(hx,hy),(hx-3,hy)],'#e1c9a3')
    # Faceted metal yo-yo, subdued blue to match Killua's long sleeves.
    arm+=_poly([(dx-5,dy-3),(dx-1,dy-6),(dx+4,dy-4),(dx+6,dy),(dx+3,dy+5),(dx-2,dy+6),(dx-6,dy+2)],'#596e82')
    arm+=_poly([(dx-5,dy-3),(dx-1,dy-6),(dx+4,dy-4),(dx+2,dy-1),(dx-3,dy+1),(dx-6,dy+2)],'#b3c3c3')
    arm+=_poly([(dx+2,dy-1),(dx+4,dy-4),(dx+6,dy),(dx+3,dy+5),(dx-2,dy+6),(dx-1,dy+2)],'#3c526c')
    arm+=_ellipse(dx,dy,2,2,'#d6d8c6')
    return arm

def killua(x,y,s=1):
    r=ET.fromstring(base.killua(x,y,s));nodes=list(r[1])
    out=_begin('killua',x,y,s,'Killua Zoldyck throwing and catching a metal yo-yo')+_xml(r[0])
    out+='<g transform="translate(0 -2)">'+_parts(nodes[:16])
    out+=_parts(nodes[18:20])+_xml(nodes[21])
    out+=_state('killua','idle',_parts(nodes[16:18])+_xml(nodes[20]))
    for state,(hand,disc) in KILLUA_POSES.items():out+=_state('killua',state,_yoyo_hand(hand,disc))
    out+=_parts(nodes[22:])
    return out+'</g></g>'

# Contact poses are solved against the ACTUAL free-right edge of the lid.
# A small grounded left step supplies reach; arm segments remain 28/30 px.
LINK_CONTACTS={
    'touch-low':(737.3,237.7),
    'touch-mid':(740.9,205.3),
    'touch-high':(748.1,186.4),
}
def _link_local_hand(world,lean,step):
    return _rotate((world[0]-797-step,world[1]-279),-lean,(0,-33))

# Pose tuple: torso lean, leftward ground step, hand in torso coordinates, rupee.
LINK_POSES={
    'prepare':(-10,-5,(-29,-59),False),
    'touch-low':(-25,-10,_link_local_hand(LINK_CONTACTS['touch-low'],-25,-10),False),
    'touch-mid':(-18,-10,_link_local_hand(LINK_CONTACTS['touch-mid'],-18,-10),False),
    'touch-high':(-10,-10,_link_local_hand(LINK_CONTACTS['touch-high'],-10,-10),False),
    'reach':(-25,-10,_link_local_hand((735,235),-25,-10),False),
    'lift':(-6,-10,(-30,-70),True),
    'inspect':(0,-10,(-24,-87),True),
    'pocket':(0,-10,(-7,-58),True),
}
LINK_SCHEDULE=[(0,'idle'),(18.4,'prepare'),(18.7,'touch-low'),(18.78,'touch-mid'),
               (19.02,'touch-high'),(19.15,'reach'),(19.5,'lift'),(19.8,'inspect'),
               (20.7,'pocket'),(21,'touch-high'),(21.2,'touch-mid'),(21.32,'touch-low'),
               (21.45,'prepare'),(21.6,'idle'),(DURATION,'idle')]
_state_tracks('link',LINK_SCHEDULE)

CHEST_INSTRUCTIONS={
    'original_is_open':True,
    'original_lid_bounds':(698,185,750,226),
    'free_edge_world':LINK_CONTACTS,
    'opening_contacts':((18.7,'touch-low'),(18.78,'touch-mid'),(19.02,'touch-high')),
    'reach_at':19.15,
    'closing_contacts':((21.0,'touch-high'),(21.2,'touch-mid'),(21.32,'touch-low')),
    'withdraw_at':21.45,
    'idle_restored':21.6,
    'ground_step_px':-10,
    'note':'Mutate the actual original lid at the listed low/mid/high contact times. The hand center is solved against its free-right corner in each state, not the fence or fixed hinge. Body, feet, and ground shadow move together for the small left step, then return to the original resting position.',
}

def _link_elbow(hand):
    shoulder=(14,-70);dx,dy=hand[0]-shoulder[0],hand[1]-shoulder[1]
    distance=hypot(dx,dy);upper,forearm=28.,30.
    assert abs(upper-forearm)<distance<upper+forearm,(hand,distance)
    along=(upper*upper-forearm*forearm+distance*distance)/(2*distance)
    height=sqrt(max(0,upper*upper-along*along))
    candidates=[(shoulder[0]+along*dx/distance-sign*height*dy/distance,
                 shoulder[1]+along*dy/distance+sign*height*dx/distance) for sign in (-1,1)]
    return max(candidates,key=lambda p:p[1])

def _link_arm(hand,rupee):
    hx,hy=hand;elbow=_link_elbow(hand)
    # Fixed bone lengths: upper arm 28 px, elbow-to-hand 30 px. The last
    # eight pixels of the latter are the brown gauntlet and gripping hand.
    dx,dy=hand[0]-elbow[0],hand[1]-elbow[1]
    wrist=(hx-dx*8/30,hy-dy*8/30)
    arm=_segment((14,-70),elbow,5.7,4.7,'#436d35')
    arm+=_segment(elbow,wrist,4.4,3.5,'#b7bfac')
    arm+=_segment(wrist,hand,4.1,3.4,'#785633')
    arm+=_segment((wrist[0]-1,wrist[1]-1),(hx-dx*2/30-1,hy-dy*2/30-1),1.3,1.3,'#a17a43')
    arm+=_poly([(hx-3,hy-3),(hx+2,hy-4),(hx+5,hy-1),(hx+3,hy+3),(hx-1,hy+4),(hx-4,hy+1)],'#cbae7b',
               data_link_hand=f'{hx:.8f},{hy:.8f}')
    if rupee:
        cy=hy-10
        arm+=_poly([(hx,cy-8),(hx+5,cy-4),(hx+5,cy+4),(hx,cy+9),(hx-5,cy+4),(hx-5,cy-4)],'#3b9a52',data_rupee_hand=f'{hx:g},{hy:g}')
        arm+=_poly([(hx,cy-8),(hx,cy+9),(hx-5,cy+4),(hx-5,cy-4)],'#80b963')
        arm+=_poly([(hx,cy-8),(hx+5,cy-4),(hx+2,cy-3),(hx,cy+5)],'#b3ce85')
        arm+=_poly([(hx+2,cy-3),(hx+5,cy-4),(hx+5,cy+4),(hx,cy+9),(hx,cy+5)],'#2d7045')
    return arm

def link(x,y,s=1):
    r=ET.fromstring(base.link(x,y,s));nodes=list(r)
    out=_begin('link',x,y,s,'Link stepping to open a chest, inspecting a rupee, and closing its lid')
    out+=_state('link','idle',_parts(nodes))
    for state,(lean,step,hand,rupee) in LINK_POSES.items():
        upper=_parts(nodes[19:31],True)+_link_arm(hand,rupee)+_parts(nodes[36:],True)
        turn=f'rotate({lean:g} 0 -33)'
        # The shadow follows the 10 px step, while all foot heights stay
        # exactly grounded. Lean applies only to the torso and sword.
        legs=_parts(nodes[8:19],True)
        if state=='prepare':
            # Lead with the left foot; the rear boot catches up next pose.
            legs=_parts(nodes[8:15],True)+_group(_parts(nodes[15:19],True),'translate(5 0)')
        body=_xml(nodes[0],True)+_group(_parts(nodes[1:8],True),turn)+legs+_group(upper,turn)
        out+=_state('link',state,_group(body,f'translate({step:g} 0)'))
    return out+'</g>'
