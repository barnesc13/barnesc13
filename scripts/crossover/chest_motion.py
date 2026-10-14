"""Animate the actual existing deposit-chest lid, not a duplicate overlay."""
from xml.etree import ElementTree as ET
import re
from .motion_runtime import motion,track
I='translate(0px,0px)'
# Contact starts at 18.70 and21.00; the hinge and chest body never move.
SCHEDULE=[(0,'closed'),(18.78,'mid'),(19.02,'open'),(21.2,'mid'),(21.32,'closed'),(28.8,'closed')]
TRACKS={f'world-chest-{st}':track([(t,I,int(s==st)) for t,s in SCHEDULE]) for st in ('closed','mid','open')}
def apply(scene):
 pattern=r'<g transform="translate\(751 244\) scale\(0\.9\)">.*?</g>'
 original=re.search(pattern,scene,re.S);assert original
 r=ET.fromstring(original[0]);a=list(r)
 def pack(nodes):return ''.join(ET.tostring(n,encoding='unicode') for n in nodes)
 body=pack(a[:2])+pack(a[6:12])
 lidopen=pack(a[2:6])+pack(a[12:])
 closed='<path d="M-14-24L39-24L27-7L-26-7Z" fill="#92724d" stroke="#868986" stroke-width="5"/>'
 closed+='<path d="M-18-18H35M-22-13H30" fill="none" stroke="#584631" stroke-width="1.2"/>'
 closed+='<path d="M-11-22H30L28-20H-13Z" fill="#b08a59" opacity=".65"/><path d="M-1-9H8V-5H-1Z" fill="#929890"/>'
 mid='<path d="M-22-43L31-43L39-24L-14-24Z" fill="#8b6b48" stroke="#868986" stroke-width="5"/>'
 mid+='<path d="M-18-37H33M-16-31H35" fill="none" stroke="#584631" stroke-width="1.4"/>'
 mid+='<path d="M-17-41H28L29-38H-16Z" fill="#b08a59" opacity=".6"/><path d="M1-45H10V-42H1Z" fill="#929890"/>'
 result='<g id="preview-animated-chest" transform="translate(751 244) scale(0.9)">'+body
 result+=motion('world-chest-closed',closed)+motion('world-chest-mid',mid,transient=True)+motion('world-chest-open',lidopen,transient=True)+'</g>'
 return scene[:original.start()]+result+scene[original.end():]
