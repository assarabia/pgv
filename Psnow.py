from nodebox.graphics import *
from nodebox.graphics.shader import Shader, vec4
from nodebox.graphics.physics import Particle, MASS, Vector
from PsnowGraphics import *
from PcapMonitor import *
from math import atan, degrees

development = True
interface   = 'en1'
fullscreen  = False

'''
'src can be'          'dst can be'
'2001:1111:10::10' -> '2001:aaaa:10::10'
'2001:2222:10::20' -> '2001:bbbb:10::20'
'2001:3333:10::30' -> '2001:cccc:10::30'
'''
node_map = {'2001:1111:10::10' : '2001:aaaa:10::10',
            '2001:2222:10::20' : '2001:bbbb:10::20', 
            '2001:3333:10::30' : '2001:cccc:10::30'}

if fullscreen:
    canvas.fullscreen = True
else:
    canvas.size = 800, 600

bg_color = (0.8,0.8,0.8,0.8)        # background color

''' text setting '''
t_color  = (0.1, 0.1, 0.1, 0.9)  # text color
t_font   = "Droid Serif"
t_fontsize = 10

''' node setting '''
n_color0 = (0.25, 0.75, 0.25, 0.8)  # color for node (green)
n_color1 = (0.75, 0.25, 0.25, 0.7)  # color for node (red)
n_color2 = (0.25, 0.50, 0.50, 0.8)  # color for node (blue)
n_color3 = (0.10, 0.10, 0.10, 0.1)  # color for node (gray)
n_color4 = (0.90, 0.90, 0.90, 0.3)  # color for node (white)
n_radius = 80                       # node radius

''' graph setting '''
g = GraphExt()
g.prune(depth=0)                    # Remove orphaned nodes with no connections.
g.distance         = 80             # Overall spacing between nodes.
g.layout.force     = 0.01           # Strength of the attractive & repulsive force.
g.layout.repulsion = 15             # Repulsion radius.

''' system setting '''
systems = {}

systems['global'] = System(gravity=(0, 1.0), drag=0.01)
e = Emitter(x=-canvas.width/2+50, y=canvas.height/2-50, angle=-40, strength=5.0, spread=-10)
for i in range(100):
    e.append(ParticleExt(0, 0, mass=random(5,25), radius=MASS, life=random(50,200), color=n_color4))
systems['global'].append(e)
obstacle = Obstacle(0, 0, mass=70, radius=70, fixed=True)
systems['global'].append(obstacle)
systems['global'].force(6, source=obstacle) # Repulsive force from this particle to all others.

for i in node_map.values():
    g.add_node(id=i, center_w=canvas.width/2, center_h=canvas.height/2,
               radius=n_radius,
               stroke=bg_color, fill=n_color1, text=t_color)

for i in node_map.values():
    for j in node_map.values():
        if i != j:
            g.add_edge(i, j, stroke=bg_color, visible=False)
            systems[i+j] = SystemExt(gravity=(0.0,0.0), drag=1.0)

''' particle setting '''
p_gravity    = 200      # lower is stronger
p_interval   = 5.0      # if particle is emitted, next emit is after p_interval
p_deadradius = 20       # particle will be dead if it gets into dead distance to node.
p_img = blur(Image("IMG_Psnow/train.png", width=100, height=50), amount=3, kernel=2)

def reflect(canvas, mvp):
    if node_map.has_key(mvp['mpsa']['src']) == False:
        return

    ns = g.node(node_map[mvp['mpsa']['src']])
    nd = g.node(mvp['mpsa']['dst'])

    if ns and nd:
        e = g.edge(ns.id, nd.id)
        if e.active:
            return

        if 'ffffffff' in mvp.dst.encode("hex"):
            burst = True
        else:
            burst = False

        caption=mvp['inner']['src'] + ' - ' + mvp['inner']['dst']

        angle=0
        if nd.x-ns.x != 0:
            angle = degrees(atan((nd.y-ns.y)/(nd.x-ns.x)))

        e.activate(p_interval, caption=caption)
        systems[ns.id+nd.id].setGravity(((nd.x-ns.x)/p_gravity, -(nd.y-ns.y)/p_gravity))
        systems[ns.id+nd.id].append(ParticleImg(ns.x, ns.y,
                                                system_ns=systems[ns.id], system_ns_col=n_color4,
                                                deadpoint=(nd.x, nd.y), deadradius=p_deadradius,
                                                img=p_img, angle=angle))

def reflect_test(canvas, mvp):
    if type(mvp) == dpkt.ethernet.Ethernet:
        ns = g.node('2001:aaaa:10::10')
        nd = g.node('2001:bbbb:10::20')

        e = g.edge(ns.id, nd.id)
        if e.active:
            return

        if 'ffffffff' in mvp.dst.encode("hex"):
            burst = True
        else:
            burst = False

        caption=mvp.src.encode("hex") + ' - ' + mvp.dst.encode("hex")
        angle=0
        if nd.x-ns.x != 0:
            angle = degrees(atan((nd.y-ns.y)/(nd.x-ns.x)))

        e.activate(p_interval)
        systems[ns.id+nd.id].setGravity(((nd.x-ns.x)/p_gravity, -(nd.y-ns.y)/p_gravity))
        systems[ns.id+nd.id].append(ParticleImg(ns.x, ns.y,
                                                system_ns=systems[nd.id+ns.id], system_ns_col=n_color4,
                                                deadpoint=(nd.x, nd.y), deadradius=p_deadradius,
                                                img=p_img, angle=angle))

dragged=None

def draw(canvas):    
    canvas.clear()
    background(bg_color)
    colorplane(0, 0, canvas.width, canvas.height,
               n_color2, bg_color, bg_color)
    translate(canvas.width/2, canvas.height/2)

    ''' reflect captured packet to canvas '''
    mvp = logger.get_packet()
    if mvp:
        if development:
            reflect_test(canvas, mvp)
        else:
            reflect(canvas, mvp)

    ''' draw should be done before update to draw framing out image '''
    g.draw(weighted=0.5, directed=True)
    for s in systems.values():
        s.draw()

    g.update(iterations=10)
    if canvas.frame % 10 == 0:
        g.update_edge_life()
    for s in systems.values():
        s.update(limit=20)

    ''' make it draggable '''
    dx = canvas.mouse.x - canvas.width/2
    dy = canvas.mouse.y - canvas.height/2
    global dragged
    if canvas.mouse.pressed and not dragged:
        dragged = g.node_at(dx, dy)
    if not canvas.mouse.pressed:
        dragged = None
    if dragged:
        dragged.x = dx
        dragged.y = dy

if development:
    logger = PcapMonitor(interface)
else:
    logger = PcapMonitor(interface, mpsa_vxlan_filter)
logger.start()

canvas.run(draw)
