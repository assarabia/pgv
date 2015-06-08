from nodebox.graphics import *
from nodebox.graphics.shader import Shader, vec4
from nodebox.graphics.physics import Particle, MASS, Vector
from PcatGraphics import *
from PcapMonitor import *

development = False
interface   = 'en0'
fullscreen  = True

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
bg_image = Image("IMG_Pcat/frame.png", width=canvas.width, height=canvas.height)

''' text setting '''
t_color  = (0.1, 0.1, 0.1, 0.9)  # text color
t_font   = "Droid Serif"
t_fontsize = 15
t_center = Text("MPSA isle", fontname=t_font, fontweight=BOLD, fill=t_color, fontsize=t_fontsize)

''' node setting '''
n_color0 = (0.25, 0.75, 0.25, 0.8)  # color for node (green)
n_color1 = (0.75, 0.25, 0.25, 0.7)  # color for node (red)
n_color2 = (0.50, 0.75, 0.75, 0.8)  # color for node (blue)
s_color  = (0.1,  0.1,  0.1,  0.2)  # color for node (gray)
n_radius = 180                      # node radius
c_radius = 240                      # center node raidus

''' graph setting '''
g = GraphExt()
g.prune(depth=0)                    # Remove orphaned nodes with no connections.
g.distance         = 85             # Overall spacing between nodes.
g.layout.force     = 0.01           # Strength of the attractive & repulsive force.
g.layout.repulsion = 15             # Repulsion radius.

''' system setting '''
systems = {}

for i in node_map.values():
    g.add_node(id=i, center_w=canvas.width/2, center_h=canvas.height/2,
               radius=n_radius,
               stroke=bg_color, fill=n_color1, text=t_color, fontsize=t_fontsize)

for i in node_map.values():
    for j in node_map.values():
        if i != j:
            g.add_edge(i, j, stroke=bg_color, visible=False)
            systems[i+j] = SystemExt(gravity=(0.0,0.0), drag=1.0)

''' particle setting '''
p_gravity    = 200      # lower is stronger
p_interval   = 4.0      # if particle is emitted, next emit is after p_interval
p_deadradius = 20       # particle will be dead if it gets into dead distance to node.
p_black_imgs = [
    Image("IMG_Pcat/black/f0s.png"),
    Image("IMG_Pcat/black/f1s.png"),
    Image("IMG_Pcat/black/f2s.png"),
    Image("IMG_Pcat/black/f3s.png"),
    Image("IMG_Pcat/black/f4s.png")
    ]
p_black_img_fout = Image("IMG_Pcat/cat1.png", width=150, height=150)
p_yellow_imgs = [
    Image("IMG_Pcat/blue/f0s.png"),
    Image("IMG_Pcat/blue/f1s.png"),
    Image("IMG_Pcat/blue/f2s.png"),
    Image("IMG_Pcat/blue/f4s.png")
    ]
p_yellow_img_fout = Image("IMG_Pcat/blue/cat1.png", width=150, height=150)

def reflect(canvas, mvp):
    if node_map.has_key(mvp['mpsa']['src']) == False:
        return

    ns = g.node(node_map[mvp['mpsa']['src']])
    nd = g.node(mvp['mpsa']['dst'])

    if ns and nd:
        e = g.edge(ns.id, nd.id)
        if e.active:
            return

        if 'ffffffff' in mvp['inner']['dst']:
            burst = True
        else:
            burst = False

        caption=[]
        #caption.append(Text("MPSA  Outer src-dst : " + mvp['mpsa']['src'] + ' - ' + mvp['mpsa']['src'],
        #                    font=t_font, fontsize=t_fontsize, fill=t_color))
        #caption.append(Text("VXLAN Outer src-dst : " + mvp['vxlan']['src'] + ' - ' + mvp['vxlan']['src'],
        #                    font=t_font, fontsize=t_fontsize, fill=t_color))
        #caption.append(Text("VXLAN vni     : " + mvp['vxlan']['vni'],
        #                    font=t_font, fontsize=t_fontsize, fill=t_color))
        #caption.append(Text("Inner src-dst : " + mvp['inner']['src'] + ' - ' + mvp['inner']['dst'],
        #                    font=t_font, fontsize=t_fontsize, fill=t_color))

        e.activate(p_interval, caption=caption)
        systems[ns.id+nd.id].setGravity(((nd.x-ns.x)/p_gravity, -(nd.y-ns.y)/p_gravity))

        if 'fff' in mvp['vxlan']['vni']:
            systems[ns.id+nd.id].append(ParticleExt(ns.x, ns.y,
                                                    deadpoint=(nd.x, nd.y), deadradius=p_deadradius,
                                                    imgs=p_black_imgs, img_fout=p_black_img_fout,
                                                    burst=burst,
                                                    index=canvas.frame%len(p_black_imgs)))
        if '01' in mvp['vxlan']['vni']:
            systems[ns.id+nd.id].append(ParticleExt(ns.x, ns.y,
                                                    deadpoint=(nd.x, nd.y), deadradius=p_deadradius,
                                                    imgs=p_yellow_imgs, img_fout=p_yellow_img_fout,
                                                    burst=burst,
                                                    index=canvas.frame%len(p_yellow_imgs)))

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

        caption=[]
        caption.append(Text("Inner src-dst : " + mvp.src.encode("hex") + ' - ' + mvp.dst.encode("hex"),
                            font=t_font, fontsize=t_fontsize, fill=t_color))

        e.activate(p_interval, caption=caption)
        systems[ns.id+nd.id].setGravity(((nd.x-ns.x)/p_gravity, -(nd.y-ns.y)/p_gravity))
        if 'ffffffff' in mvp.dst.encode("hex"):
            systems[ns.id+nd.id].append(ParticleExt(ns.x, ns.y,
                                                    deadpoint=(nd.x, nd.y), deadradius=p_deadradius,
                                                    imgs=p_black_imgs, img_fout=p_black_img_fout,
                                                    burst=burst,
                                                    index=canvas.frame%len(p_black_imgs)))
        else:
            systems[ns.id+nd.id].append(ParticleExt(ns.x, ns.y,
                                                    deadpoint=(nd.x, nd.y), deadradius=p_deadradius,
                                                    imgs=p_yellow_imgs, img_fout=p_yellow_img_fout,
                                                    burst=burst,
                                                    index=canvas.frame%len(p_yellow_imgs)))

dragged=None

def draw(canvas):    
    canvas.clear()
    background(bg_color)
    image(bg_image, x=0, y=0)

    ''' center ellipse '''
    translate(canvas.width/2, canvas.height/2)
    ew = eh = 0
    for i in node_map.values():
        n = g.node(i)
        ew += n.x
        eh += n.y
    ew /= len(node_map.values())
    eh /= len(node_map.values())
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
