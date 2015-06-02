from nodebox.graphics import *
from nodebox.graphics.shader import Shader, vec4
from nodebox.graphics.physics import Particle, MASS, Vector
from PcatGraphics import *
from PcapMonitor import *

development = False
interface   = 'en0'
fullscreen  = False

node_ids = ['2001:db8:10::30',
            '2001:aaaa:10::10',
            '2001:bbbb:10::20']

canvas_w = 800                      # canvas width
canvas_h = 600                      # canvas height
center_w = canvas_w/2
center_h = canvas_h/2
bg_color = (0.8,0.8,0.8,0.8)        # background color

''' text setting '''
t_color  = (0.1, 0.1, 0.1, 0.9)  # text color
t_font   = "Droid Serif"
t_fontsize = 10
t_center = Text("MPSA isle", fontname=t_font, fontweight=BOLD, fill=t_color)

''' node setting '''
n_color0 = (0.25, 0.75, 0.25, 0.8)  # color for node (green)
n_color1 = (0.75, 0.25, 0.25, 0.7)  # color for node (red)
n_color2 = (0.50, 0.75, 0.75, 0.8)  # color for node (blue)
s_color  = (0.1,  0.1,  0.1,  0.2)  # color for node (gray)
n_radius = 120                      # node radius
c_radius = 240                      # center node raidus

''' graph setting '''
g = GraphExt()
g.prune(depth=0)                    # Remove orphaned nodes with no connections.
g.distance         = 80             # Overall spacing between nodes.
g.layout.force     = 0.01           # Strength of the attractive & repulsive force.
g.layout.repulsion = 15             # Repulsion radius.

''' system setting '''
systems = {}

for i in node_ids:
    g.add_node(id=i, center_w=center_w, center_h=center_h,
               radius=n_radius,
               stroke=bg_color, fill=n_color1, text=t_color)
    systems[i] = SystemExt(gravity=(0.0,0.0), drag=1.0)

for i in node_ids:
    for j in node_ids:
        if i != j:
            g.add_edge(i, j, stroke=bg_color, visible=False)

''' particle setting '''
p_gravity    = 200      # lower is stronger
p_interval   = 2.0      # if particle is emitted, next emit is after p_interval
p_deadradius = 20       # particle will be dead if it gets into dead distance to node.
p_imgs = [
    Image("IMG_Pcat/f0s.png"),
    Image("IMG_Pcat/f1s.png"),
    Image("IMG_Pcat/f2s.png"),
    Image("IMG_Pcat/f3s.png"),
    Image("IMG_Pcat/f4s.png")
    ]
p_img_fout = Image("IMG_Pcat/cat1.png", width=128, height=128)

def reflect(canvas, mvp):
    ns = g.node(mvp['mpsa']['src'])
    nd = g.node(mvp['mpsa']['dst'])
    if ns and nd:
        e = g.edge(ns.id, nd.id)
        if e.active:
            return

        caption=[]
        caption.append(Text("MPSA  Outer src-dst : " + mvp['mpsa']['src'] + ' - ' + mvp['mpsa']['src'],
                            font=t_font, fontsize=t_fontsize, fill=t_color))
        caption.append(Text("VXLAN Outer src-dst : " + mvp['vxlan']['src'] + ' - ' + mvp['vxlan']['src'],
                            font=t_font, fontsize=t_fontsize, fill=t_color))
        caption.append(Text("VXLAN vni     : " + mvp['vxlan']['vni'],
                            font=t_font, fontsize=t_fontsize, fill=t_color))
        caption.append(Text("Inner src-dst : " + mvp['inner']['src'] + ' - ' + mvp['inner']['dst'],
                            font=t_font, fontsize=t_fontsize, fill=t_color))

        e.activate(p_interval, caption=caption)
        #ns.fill= nd.fill=n_color2
        systems[nd.id].setGravity(((nd.x-ns.x)/p_gravity, -(nd.y-ns.y)/p_gravity))
        systems[nd.id].append(ParticleExt(ns.x, ns.y,
                                          deadpoint=(nd.x, nd.y), deadradius=p_deadradius,
                                          imgs=p_imgs, img_fout=p_img_fout,
                                          index=canvas.frame%len(p_imgs)))

def reflect_test(canvas, mvp):
    if type(mvp) == dpkt.ethernet.Ethernet:
        ns = g.node(node_ids[0])
        nd = g.node(node_ids[2])    
        e = g.edge(ns.id, nd.id)
        if e.active:
            return

        caption=[]
        caption.append(Text("Inner src-dst : AA:AA:AA:AA:AA:AA - BB:BB:BB:BB:BB:BB",
                            font=t_font, fontsize=t_fontsize, fill=t_color))

        e.activate(p_interval, caption=caption)
        #ns.fill= nd.fill=n_color2
        systems[nd.id].setGravity(((nd.x-ns.x)/p_gravity, -(nd.y-ns.y)/p_gravity))
        systems[nd.id].append(ParticleExt(ns.x, ns.y,
                                          deadpoint=(nd.x, nd.y), deadradius=p_deadradius,
                                          imgs=p_imgs, img_fout=p_img_fout,
                                          index=canvas.frame%len(p_imgs)))

dragged=None

def draw(canvas):    
    canvas.clear()
    background(bg_color)

    ''' center ellipse '''
    translate(center_w, center_h)
    ew = eh = 0
    for i in node_ids:
        n = g.node(i)
        ew += n.x
        eh += n.y
    ew /= len(node_ids)
    eh /= len(node_ids)
    ellipse(ew, eh, c_radius, c_radius, stroke=bg_color, fill=n_color0)
    text(t_center, ew, eh)

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
        s.draw(fill=s_color)

    g.update(iterations=10)
    if canvas.frame % 10 == 0:
        g.update_edge_life()
    for s in systems.values():
        s.update(limit=20)

    ''' make it draggable '''
    dx = canvas.mouse.x - center_w
    dy = canvas.mouse.y - center_h
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

canvas.size = canvas_w, canvas_h
if fullscreen:
    canvas.fullscreen = True
canvas.run(draw)
