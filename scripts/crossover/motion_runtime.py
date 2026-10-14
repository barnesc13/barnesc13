"""Shared native SVG held-pose contract for the private animated preview."""
DURATION=28.8

def motion(name, content, x=0, y=0, transient=False):
    classes='preview-motion '+('preview-transient ' if transient else '')+name
    return (f'<g data-preview-pivot="{name}" transform="translate({x:g} {y:g})">'
            f'<g class="{classes}" data-preview-track="{name}"><g transform="translate({-x:g} {-y:g})">'
            +content+'</g></g></g>')

def track(poses):
    # A pose is (seconds, CSS transform, opacity). All stages hold, never tween.
    return {'duration':DURATION,'poses':poses}

def motion_css(tracks):
    lines=['<style>', '.preview-motion { transform-box: view-box; transform-origin: 0px 0px; }',
           '.preview-transient { opacity: 0; }','@media (prefers-reduced-motion: no-preference) {']
    for name,t in tracks.items():
        lines.append(f'.{name} {{ animation: {name} {t["duration"]:g}s steps(1,end) infinite; }}')
    lines.append('}')
    for name,t in tracks.items():
        lines.append(f'@keyframes {name} {{')
        for sec,tr,op in t['poses']:
            lines.append(f'{sec/t["duration"]*100:.8g}% {{ transform: {tr}; opacity: {op:g}; }}')
        lines.append('}')
    lines+=['@media (prefers-reduced-motion: reduce) {','.preview-motion { animation: none !important; }',
            '.preview-transient { opacity: 0 !important; }','}','</style>']
    return '\n'.join(lines)
