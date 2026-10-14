"""Native, stepped companion actions for the PRIVATE crossover preview.

All artwork is retained from refined_visitors.py / creatures/sprites.py.
Functions return SVG only. Ground shadows are deliberately outside motion.
Actions are stylistic adaptations, not claims of canonical OSRS timings.
No JavaScript, filesystem I/O, browser scripting, or publication.
"""
from .motion_runtime import motion, track

class _Sprite:
    def __init__(self, name, label, x, y, s):
        self.parts=[f'<g id="{"crossover" if name=="chao" else "preview"}-{name}" aria-label="{label}" transform="translate({x:g} {y:g}) scale({s:g})">']
    def add(self, value):
        self.parts.append(value)
    def poly(self, pts, color, **attrs):
        attributes=' '.join(f'{key.replace("_", "-")}="{value}"' for key,value in attrs.items())
        self.parts.append('<path d="M'+'L'.join(f'{x:g} {y:g}' for x,y in pts)+f'Z" fill="{color}" {attributes}/>')
    def path(self, d, color='none', **attrs):
        attributes=' '.join(f'{key.replace("_", "-")}="{value}"' for key,value in attrs.items())
        self.parts.append(f'<path d="{d}" fill="{color}" {attributes}/>')
    def ellipse(self,x,y,rx,ry,color,opacity=1):
        self.parts.append(f'<ellipse cx="{x}" cy="{y}" rx="{rx}" ry="{ry}" fill="{color}" opacity="{opacity}"/>')
    def joint(self, start, name, x=0, y=0, transient=False):
        content=''.join(self.parts[start:])
        self.parts[start:]=[motion(name,content,x,y,transient)]
    def finish(self):
        return ''.join(self.parts)+'</g>'

def trainer(x,y,s=1):
    z=_Sprite("trainer","Pokemon Trainer Red tossing and catching a Poke Ball",x,y,s)
    add,poly,path,ellipse=z.add,z.poly,z.path,z.ellipse
    ellipse(1,2,25,11,'#233722',.27)
    # Backpack behind the torso, visible over the left shoulder, never an outlined sticker.
    poly([(-24,-63),(-13,-70),(-6,-61),(-7,-29),(-20,-25),(-28,-35)],'#8f783e')
    poly([(-24,-63),(-13,-70),(-9,-63),(-21,-57),(-27,-53)],'#d1b76a')
    poly([(-27,-53),(-21,-57),(-20,-29),(-27,-35)],'#b49a54')
    path('M-25-43l8-3v12l-8 3Z','#bca361');path('M-25-43l8-3','none',stroke='#695a30',stroke_width=1.5)
    # Separate trouser legs and flat faceted shoes.
    poly([(-12,-31),(1,-31),(-2,-13),(-9,0),(-19,-1),(-15,-17)],'#385a72')
    poly([(0,-31),(13,-31),(12,-14),(18,0),(8,5),(0,-12)],'#487e97')
    poly([(-18,-4),(-8,-1),(-9,4),(-26,6),(-26,1)],'#d2d3bc')
    poly([(-26,1),(-9,1),(-9,5),(-26,7)],'#394a50')
    poly([(8,0),(17,-2),(27,5),(25,9),(10,8)],'#d8d9c3')
    poly([(10,6),(26,5),(25,9),(10,10)],'#344a50')
    poly([(-13,-33),(0,-33),(-3,-15),(-9,-2),(-13,-3),(-9,-17)],'#4f7e94')
    # Tee and sleeveless red vest with top-lit shoulders.
    poly([(-14,-70),(-3,-73),(10,-70),(16,-56),(11,-31),(-11,-29),(-18,-46)],'#2d3c3a')
    poly([(-14,-70),(-4,-72),(-3,-32),(-12,-29),(-18,-46)],'#aa3d32')
    poly([(-14,-70),(-4,-72),(-5,-65),(-16,-61)],'#d06249')
    poly([(2,-72),(10,-70),(16,-56),(11,-31),(3,-32)],'#c34d3c')
    poly([(10,-70),(16,-56),(12,-34),(8,-33),(10,-58)],'#94392f')
    poly([(-11,-31),(11,-32),(11,-27),(-11,-26)],'#2b3430')
    poly([(-1,-32),(3,-32),(3,-27),(-1,-27)],'#b9ad85')
    # The FireRed-style vest has pale front facings, not a plain red slab.
    poly([(-4,-72),(-1,-69),(-1,-32),(-4,-32)],'#d7d9be')
    poly([(2,-72),(5,-70),(5,-32),(2,-32)],'#c4cbb7')
    # Pack strap, left arm, ball hand on the far side.
    path('M-11-69l-3 15 4 14','none',stroke='#c4b68b',stroke_width=3)
    poly([(-15,-65),(-21,-59),(-23,-45),(-18,-41),(-12,-52)],'#303d39')
    poly([(-23,-46),(-17,-44),(-14,-30),(-18,-26),(-23,-31)],'#c6a87b')
    poly([(-23,-44),(-20,-43),(-17,-30),(-20,-30)],'#dfc18d')
    arm_start=len(z.parts)
    poly([(13,-66),(20,-59),(22,-47),(16,-43),(10,-55)],'#37453d')
    poly([(19,-47),(24,-49),(29,-38),(26,-30),(20,-33),(20,-40)],'#c4a273')
    poly([(24,-39),(30,-39),(32,-34),(29,-29),(24,-30),(22,-34)],'#d3b583')
    ball_start=len(z.parts)
    # Tiny Poké Ball: angular red top, ivory lower half, central dark band/button.
    poly([(27,-39),(31,-42),(36,-39),(36,-35),(32,-32),(28,-34)],'#d2d0b8')
    poly([(27,-39),(31,-42),(36,-39),(36,-37),(28,-37)],'#c84f42')
    path('M28-37h8','none',stroke='#3f4440',stroke_width=1.2)
    ellipse(32,-37,1.2,1.2,'#e4e1c9')
    ball_svg=''.join(z.parts[ball_start:])
    z.joint(ball_start,'companion-trainer-held-ball',32,-37)
    z.joint(arm_start,'companion-trainer-arm',14,-62)
    # Flight is the identical ball at the exact release-arm orientation.
    # Its opacity is mutually exclusive with the ball attached to the palm.
    release_ball='<g transform="rotate(-55 14 -62)">'+ball_svg+'</g>'
    add(motion('companion-trainer-flight-ball',release_ball,0,0,transient=True))
    # Neck, polygonal face, dark hair and unmistakable Red cap.
    poly([(-5,-77),(7,-78),(8,-69),(2,-65),(-5,-70)],'#b49469')
    poly([(-11,-93),(-5,-100),(7,-99),(14,-91),(14,-79),(7,-72),(-4,-74),(-12,-82)],'#c9aa7b')
    poly([(-11,-93),(-5,-100),(7,-99),(7,-87),(-3,-82),(-12,-84)],'#dfc18d')
    poly([(7,-87),(14,-91),(15,-85),(16,-82),(13,-80),(7,-72),(2,-77)],'#ba9668')
    poly([(-12,-91),(-6,-95),(-6,-81),(-9,-77),(-13,-82)],'#3f382a')
    poly([(9,-85),(12,-85),(12,-83),(9,-83)],'#333b33')
    # White front panel, red crown and a projecting red brim in the viewing direction.
    poly([(-15,-96),(-8,-107),(5,-109),(15,-102),(17,-94),(4,-91),(-9,-91)],'#b64436')
    poly([(-15,-96),(-8,-107),(5,-109),(10,-104),(-3,-102)],'#d4614b')
    poly([(1,-103),(10,-104),(15,-100),(16,-94),(5,-92),(-1,-96)],'#e1ddc2')
    poly([(3,-94),(16,-96),(29,-90),(24,-86),(11,-88)],'#ad3b30')
    poly([(3,-94),(16,-96),(29,-90),(17,-90)],'#d15a43')
    path('M6-98q3-5 6 0','none',stroke='#a84b37',stroke_width=1.8)
    poly([(-5,-92),(-1,-94),(1,-90),(-2,-88)],'#4a3b2b')
    poly([(4,-91),(8,-92),(9,-88),(6,-87)],'#55422d')
    path('M8-78l3-1','none',stroke='#96734e',stroke_width=.8)
    return z.finish()

def mudkip(x,y,s=1):
    z=_Sprite("mudkip","Mudkip giving a small hop and dorsal fin flick",x,y,s)
    add,poly,path,ellipse=z.add,z.poly,z.path,z.ellipse
    ellipse(4,3,31,10,'#233b28',.26)
    body_start=len(z.parts)
    # One broad, continuous fan tail rather than separate sharp lobes.
    poly([(17,-20),(24,-34),(36,-44),(44,-43),(49,-36),(47,-27),(38,-17),(26,-10),(18,-12)],'#a9c8cb')
    poly([(24,-34),(36,-44),(44,-43),(46,-38),(34,-27),(21,-18)],'#d0dfd6')
    poly([(34,-27),(46,-38),(49,-36),(47,-27),(38,-17),(26,-10),(21,-18)],'#86aeb6')
    path('M24-17Q33-30 43-37','none',stroke='#729ca8',stroke_width=1.3)
    # Low round-bodied mesh and four short planted feet.
    poly([(-10,-24),(0,-31),(15,-31),(27,-23),(30,-14),(24,-5),(8,0),(-9,-5),(-15,-14)],'#4b91aa')
    poly([(-10,-24),(0,-31),(15,-31),(27,-23),(15,-18),(-6,-18)],'#76bac8')
    poly([(15,-18),(27,-23),(30,-14),(24,-5),(8,0),(10,-10)],'#3d809c')
    poly([(-10,-10),(5,-15),(20,-10),(21,-4),(8,1),(-7,-2)],'#bdd8cf')
    poly([(17,-10),(25,-10),(29,-4),(28,2),(22,5),(16,2),(14,-4)],'#519ab0')
    poly([(17,-10),(25,-10),(26,-4),(19,-1),(14,-4)],'#70b3c2')
    poly([(-14,-11),(-7,-12),(-5,-5),(-8,1),(-17,1),(-20,-3)],'#3e809a')
    poly([(-6,-10),(2,-10),(6,-4),(5,3),(-1,7),(-9,5),(-12,1),(-10,-6)],'#5aa7bb')
    poly([(-10,-6),(-6,-10),(2,-10),(3,-3),(-3,1),(-12,1)],'#81c0cb')
    # Far orange cheek fan, partly occluded by the head.
    poly([(13,-33),(21,-36),(27,-33),(24,-28),(30,-24),(25,-21),(26,-15),(18,-17),(12,-24)],'#c58d42')
    # Twelve-sided head keeps a soft, round silhouette within the faceted style.
    poly([(-27,-28),(-23,-37),(-14,-43),(-2,-44),(10,-41),(18,-34),(21,-25),(19,-16),(10,-9),(-3,-6),(-17,-10),(-25,-17)],'#5ca5ba')
    poly([(-27,-28),(-23,-37),(-14,-43),(-2,-44),(10,-41),(6,-33),(-9,-28)],'#85c4ce')
    poly([(6,-33),(10,-41),(18,-34),(21,-25),(19,-16),(10,-9),(1,-14)],'#4b91ad')
    poly([(-25,-17),(-15,-19),(-4,-17),(8,-16),(19,-16),(10,-9),(-3,-6),(-17,-10)],'#c1ddd3')
    # One bulbous gill pad with three short outer frills.
    poly([(-25,-33),(-32,-34),(-39,-38),(-36,-29),(-42,-25),(-36,-21),(-36,-14),(-29,-16),(-23,-14),(-18,-22),(-20,-30)],'#d69c45')
    poly([(-25,-33),(-32,-34),(-39,-38),(-34,-27),(-23,-24),(-20,-30)],'#e8b864')
    poly([(-23,-24),(-34,-27),(-36,-21),(-36,-14),(-29,-16),(-23,-14),(-18,-22)],'#c28a37')
    fin_start=len(z.parts)
    # Tall paddle-like dorsal fin with a gently chamfered cap, not a sharp spike.
    poly([(-6,-40),(-6,-60),(-3,-68),(3,-71),(10,-67),(13,-59),(13,-39),(5,-35)],'#559db6')
    poly([(-6,-40),(-6,-60),(-3,-68),(3,-71),(4,-57),(5,-35)],'#80c3cf')
    poly([(4,-57),(3,-71),(10,-67),(13,-59),(13,-39),(5,-35)],'#4389a7')
    z.joint(fin_start,'companion-mudkip-fin',5,-38)
    # Small oval eyes and a quiet smile avoid the robotic square-face look.
    ellipse(-13,-27,2.4,3.8,'#223b43');ellipse(-13.7,-28.5,.8,1.15,'#e5ecd9')
    ellipse(8,-27,2.1,3.4,'#243d45');ellipse(7.5,-28.2,.7,1,'#dce9d5')
    path('M-8-17Q-3-13 2-17','none',stroke='#4d7478',stroke_width=1.1)
    z.joint(body_start,'companion-mudkip-hop',0,0)
    return z.finish()

def chao(x,y,s=1):
    """Neutral blue Sonic Chao: bounds (-18,-49,18,2), shadow y=6."""
    z=_Sprite('chao','Tiny blue Sonic Chao with yellow orb and small pink wings',x,y,s);p=z.poly
    z.ellipse(1,1,15,5,'#213b2d',.24)
    body_start=len(z.parts)
    left_wing_start=len(z.parts)
    # Pink translucent-looking wings are small, solid faceted meshes.
    p([(-8,-18),(-16,-24),(-18,-19),(-15,-14),(-9,-12)],'#a88990')
    p([(-16,-24),(-12,-20),(-9,-12),(-15,-17)],'#ccaca8')
    z.joint(left_wing_start,'companion-chao-left-wing',-9,-16)
    right_wing_start=len(z.parts)
    p([(8,-18),(15,-24),(18,-20),(17,-15),(10,-12)],'#ad8c93')
    p([(15,-24),(18,-20),(17,-15),(12,-16)],'#d2aba7')
    z.joint(right_wing_start,'companion-chao-right-wing',10,-16)
    # Small round belly with yellow-tipped feet and hands.
    p([(-8,-20),(2,-23),(10,-19),(12,-10),(8,-3),(-6,-3),(-11,-10)],'#6ea9b8')
    p([(-8,-20),(2,-23),(5,-18),(0,-9),(-9,-8),(-11,-10)],'#96c4c8')
    p([(5,-18),(10,-19),(12,-10),(8,-3),(1,-4),(0,-9)],'#568c9f')
    p([(-7,-8),(-2,-7),(-2,-1),(-7,2),(-14,0),(-14,-4)],'#c5b553')
    p([(-7,-8),(-2,-7),(-5,-3),(-14,-4)],'#e0d278')
    p([(4,-7),(10,-8),(16,-3),(15,1),(8,2),(3,-1)],'#b9a649')
    p([(4,-7),(10,-8),(16,-3),(10,-2),(5,0)],'#d7c466')
    p([(-10,-18),(-15,-17),(-17,-11),(-14,-8),(-10,-10),(-7,-15)],'#8cb9bb')
    p([(-17,-13),(-13,-13),(-10,-10),(-14,-8),(-17,-10)],'#d5c465')
    p([(10,-18),(14,-16),(17,-11),(14,-8),(11,-10),(8,-15)],'#5b94a7')
    p([(14,-13),(17,-11),(14,-8),(11,-10)],'#c7b350')
    # Faceted round head with the characteristic teardrop tip and warm crown.
    p([(-12,-32),(-5,-37),(0,-39),(5,-37),(12,-33),(15,-26),(12,-20),(5,-17),(-6,-18),(-13,-24)],'#77b2c2')
    p([(-12,-32),(-5,-37),(0,-39),(2,-37),(-2,-29),(-13,-24)],'#a4ced0')
    p([(2,-37),(5,-37),(12,-33),(15,-26),(12,-20),(5,-17),(4,-28)],'#5595ae')
    p([(-5,-37),(0,-39),(4,-38),(4,-34),(-2,-33)],'#ded17d')
    p([(-3,-37),(0,-39),(2,-38),(0,-35)],'#eee3a0')
    # Oblong eyes kept small enough to sit within the original scene style.
    p([(-8,-28),(-6,-29),(-4,-27),(-4,-23),(-6,-22),(-8,-24)],'#2c494b')
    p([(3,-28),(5,-29),(7,-27),(7,-23),(5,-22),(3,-24)],'#29474a')
    z.path('M-2-21l2 1 2-1',stroke='#527a81',stroke_width=.8)
    # Detached mood orb; yellow faceting reads cleanly at the final world scale.
    p([(-2,-49),(1,-49),(4,-47),(3,-44),(0,-43),(-3,-44),(-4,-47)],'#ceb84e')
    p([(-2,-49),(1,-49),(2,-47),(-1,-45),(-4,-46),(-4,-47)],'#ecdc85')
    p([(-1,-45),(2,-47),(4,-47),(3,-44),(0,-43),(-3,-44)],'#bba342')
    # The mood orb shares this group, so its head clearance never drifts.
    z.joint(body_start,'companion-chao-bob',0,0)
    return z.finish()


# Stepped action windows in seconds. Long quiet rests are intentional.
# First/last poses match exactly so the 28.8 s loop has no seam.
TRACKS={
    'companion-trainer-arm': track([
        (0,'rotate(0deg)',1),(.6,'rotate(8deg)',1),
        (.75,'rotate(-18deg)',1),(.9,'rotate(-55deg)',1),
        (2.1,'rotate(-35deg)',1),(2.25,'rotate(-12deg)',1),
        (2.4,'rotate(0deg)',1),(28.8,'rotate(0deg)',1)]),
    'companion-trainer-held-ball': track([
        (0,'none',1),(1.05,'none',0),(1.95,'none',1),
        (28.8,'none',1)]),
    'companion-trainer-flight-ball': track([
        (0,'translate(0px, 0px)',0),
        (1.05,'translate(0px, -12px)',1),
        (1.2,'translate(0px, -27px)',1),
        (1.35,'translate(0px, -39px)',1),
        (1.5,'translate(0px, -44px)',1),
        (1.65,'translate(0px, -36px)',1),
        (1.8,'translate(0px, -20px)',1),
        (1.95,'translate(0px, 0px)',0),
        (28.8,'translate(0px, 0px)',0)]),
    'companion-mudkip-hop': track([
        (0,'translate(0px, 0px)',1),
        (2.95,'translate(0px, -8px)',1),
        (3.1,'translate(0px, -14px)',1),
        (3.4,'translate(0px, -8px)',1),
        (3.55,'translate(0px, 0px)',1),
        (28.8,'translate(0px, 0px)',1)]),
    'companion-mudkip-fin': track([
        (0,'rotate(0deg)',1),(2.8,'rotate(-10deg)',1),
        (2.95,'rotate(12deg)',1),(3.25,'rotate(-8deg)',1),
        (3.55,'rotate(8deg)',1),(3.85,'rotate(-4deg)',1),
        (4,'rotate(0deg)',1),(28.8,'rotate(0deg)',1)]),
    'companion-chao-bob': track([
        (0,'translate(0px, 0px)',1),(8.4,'translate(0px, -2px)',1),
        (8.6,'translate(0px, -4px)',1),(8.8,'translate(0px, -5px)',1),
        (9.2,'translate(0px, -4px)',1),(9.6,'translate(0px, -2px)',1),
        (10,'translate(0px, 0px)',1),(28.8,'translate(0px, 0px)',1)]),
    'companion-chao-left-wing': track([
        (0,'rotate(0deg)',1),(8.4,'rotate(22deg)',1),
        (8.6,'rotate(-12deg)',1),(8.8,'rotate(22deg)',1),
        (9,'rotate(-12deg)',1),(9.2,'rotate(22deg)',1),
        (9.4,'rotate(-12deg)',1),(9.6,'rotate(0deg)',1),
        (28.8,'rotate(0deg)',1)]),
    'companion-chao-right-wing': track([
        (0,'rotate(0deg)',1),(8.4,'rotate(-22deg)',1),
        (8.6,'rotate(12deg)',1),(8.8,'rotate(-22deg)',1),
        (9,'rotate(12deg)',1),(9.2,'rotate(-22deg)',1),
        (9.4,'rotate(12deg)',1),(9.6,'rotate(0deg)',1),
        (28.8,'rotate(0deg)',1)]),
}
