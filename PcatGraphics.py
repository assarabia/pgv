from nodebox.graphics import *
from nodebox.graphics.physics import Node, Edge, Graph, Emitter, System, Particle, Vector
import time

class NodeExt(Node):
    def __init__(self, id="", center_w=0, center_h=0, radius=5, img=None, **kwargs):
        Node.__init__(self, id, radius, **kwargs)
        self.center_w, self.center_h = center_w, center_h
        self.leaf = BezierPath()

        ''' for leaf '''
        self.leaf.moveto(0, 0)
        self.leaf.curveto(radius, radius,  0, radius*3, 0, radius*4)
        self.leaf.curveto(0, radius*3, -radius, radius, 0,  0)

        ''' for image '''
        self.img = img

    def draw(self, weighted=False):
        self.__draw_ellipse(weighted)

        # Draw the node text label.
        if self.text:
            self.text.draw(self.x, self.y) 

    def __draw_ellipse(self, weighted=False):
        # Draw the node weight as a shadow (based on node betweenness centrality).
        if weighted is not False and self.centrality > (weighted==True and -1 or weighted):
            w = self.centrality * 35
            ellipse(
                self.x, 
                self.y, 
                self.radius + w, 
                self.radius + w, fill=(0,0,0,0.2), stroke=None)
        # Draw the node.
        ellipse(
            self.x, 
            self.y, 
            self.radius, 
            self.radius, fill=self.fill, stroke=self.stroke, strokewidth=self.strokewidth)

    def __draw_leaf(self, weighted=False):
        translate(self.x, self.y)
        for i in range(10):
            rotate(36)
            drawpath(self.leaf, fill=self.fill)
        translate(-self.x, -self.y)

class EdgeExt(Edge):
    def __init__(self, node1, node2, weight=0.0, length=1.0,
                 type=None,
                 stroke=(0,0,0,1), strokewidth=1, visible=True):
        Edge.__init__(self, node1, node2, weight, length, type, stroke, strokewidth)
        self.active = False
        self.visible = visible
        self.lifetime = 0.0
        self.text = []

    def activate(self, lifetime=0.0, caption=None, **kwargs):
        self.active = True
        if lifetime:
            self.lifetime = time.time() + lifetime
        self.text = caption

    def deactivate(self):
        self.active = False
        self.lifetime = 0.0
        self.text = []

    def draw(self, weighted=False, directed=False):
        """ Draws the edge as a line with the given stroke and strokewidth (increased with Edge.weight).
            Override this method in a subclass for custom drawing.
        """
        if not self.active:
            return

        if self.text:
            x = (self.node2.x + self.node1.x) / 2
            y = (self.node2.y + self.node1.y) / 2
            for t in self.text:
                t.draw(x, y)
                y = y + t.fontsize * 2

        if not self.visible:
            return

        d = sin(self.lifetime) * 10.0
        for i in range(5):
            seed(i) # Lock the seed for smooth animation.
            dx = (self.node2.x - self.node1.x) / 5
            dy = (self.node2.y - self.node1.y) / 5

            p = BezierPath()
            x = self.node1.x
            y = self.node1.y
            p.moveto(x, y)
            for j in range(5):
                x = self.node1.x + dx*j + random(-d, d)
                y = self.node1.y + dy*j + random(-d, d)
                p.lineto(x, y)
                p.moveto(x, y)

            # random alpha
            stroke = (self.stroke[0], self.stroke[1],
                      self.stroke[2], random(0.0, 0.5))

            p.lineto(self.node2.x, self.node2.y)
            drawpath(p, fill=None, stroke=stroke)

            if directed:
                self.draw_arrow(stroke=self.stroke, strokewidth=self.strokewidth)

class GraphExt(Graph):
    def add_node(self, id, *args, **kwargs):
        """ Appends a new Node to the graph.
            An optional base parameter can be used to pass a subclass of Node.
        """
        n = kwargs.pop("base", NodeExt)
        n = isinstance(id, NodeExt) and id or self.get(id) or n(id, *args, **kwargs)
        if n.id not in self:
            self.nodes.append(n)
            self[n.id] = n; n.graph = self
            self.root = kwargs.get("root", False) and n or self.root
            # Clear adjacency cache.
            self._adjacency = None
        return n
    
    def add_edge(self, id1, id2, *args, **kwargs):
        """ Appends a new Edge to the graph.
            An optional base parameter can be used to pass a subclass of Edge:
            Graph.add_edge("cold", "winter", base=IsPropertyOf)
        """
        # Create nodes that are not yet part of the graph.
        n1 = self.add_node(id1)
        n2 = self.add_node(id2)
        # Creates an Edge instance.
        # If an edge (in the same direction) already exists, yields that edge instead.
        e1 = n1.links.edge(n2)
        if e1 and e1.node1 == n1 and e1.node2 == n2:
            return e1
        e2 = kwargs.pop("base", EdgeExt)
        e2 = e2(n1, n2, *args, **kwargs)
        self.edges.append(e2)
        # Synchronizes Node.links:
        # A.links.edge(B) yields edge A->B
        # B.links.edge(A) yields edge B->A
        n1.links.append(n2, edge=e2)
        n2.links.append(n1, edge=e1 or e2)
        # Clear adjacency cache.
        self._adjacency = None
        return e2        

    def update_edge_life(self):
        current = time.time()
        for e in self.edges:
            if e.active is True and e.lifetime < current:
                e.deactivate()

    def draw(self, weighted=False, directed=False):
        """ Draws all nodes and edges.                                                                                                                                     
        """
        for e in self.edges:
            e.draw(weighted, directed)
        for n in reversed(self.nodes): # New nodes (with Node._weight=None) first.                                                                                         
            n.draw(weighted)

class ParticleExt(Particle):
    def __init__(self, x, y, deadpoint=None, deadradius=0,
                 imgs=None, index=0, img_fout =None, shadow=True,
                 velocity=(0.0,0.0), mass=10.0, radius=10.0, life=None, fixed=False):
        Particle.__init__(self, x, y, velocity, mass, radius, life, fixed)
        self.deadpoint = deadpoint
        self.deadradius = deadradius

        ''' images of particle '''
        self.imgs = imgs
        self.index = index
        self.draw_cnt = 0

        ''' image which is displayed when particle is framing out'''
        self.img_fout = img_fout

        ''' create shadow images '''
        if shadow is True:
            self.enable_shadow = True
            self.imgs_shadow = []
            for img in self.imgs:
                shadow = colorize(img, color=(0,0,0,1))
                self.imgs_shadow.append(blur(shadow, amount=3, kernel=5))

            shadow = colorize(img_fout, color=(0,0,0,1))
            self.img_fout_shadow = blur(shadow, amount=3, kernel=5)

    def draw(self, **kwargs):
        x_dist = abs(self.x-self.deadpoint[0])
        y_dist = abs(self.y-self.deadpoint[1])

        if x_dist < self.deadradius*2 or y_dist < self.deadradius*2:
            image(self.img_fout, x=self.x, y=self.y)
            if self.enable_shadow:
                image(self.img_fout_shadow, x=self.x, y=self.y-10, alpha=0.5)
        else:
            image(self.imgs[self.index], x=self.x, y=self.y)
            if self.enable_shadow:
                image(self.imgs_shadow[self.index], x=self.x, y=self.y-10, alpha=0.5)

            self.draw_cnt += 1
            if self.draw_cnt == canvas.fps:
                self.draw_cnt = 0
                self.index += 1
                if self.index == len(self.imgs):
                    self.index = 0

class EmitterExt(Emitter):
    def __init__(self, x, y, angle=0, strength=1.0, spread=10, id=''):
        Emitter.__init__(self, x, y, angle, strength, spread)
        self.id = id

    def emit_some(self, num=10):
        for i in range(num):
            self.update()

class SystemExt(System):
    def get_emitter (self, id):
        for e in self.emitters:
            if e.id == id:
                return e

    ''' don't update emitter '''
    def update(self, limit=30):
        for p in self.particles:
            # Apply gravity. Heavier objects have a stronger attraction.                                                                                                   
            p.force.x = 0
            p.force.y = 0
            p.force.x += 0.1 *  self.gravity.x * p.mass
            p.force.y += 0.1 * -self.gravity.y * p.mass
        for f in self.forces:
            # Apply attractive and repulsive forces between particles.                                                                                                     
            if not f.particle1.dead and \
               not f.particle2.dead:
                f.apply()
        for s in self.springs:
            # Apply spring forces between particles.                                                                                                                       
            if not s.particle1.dead and \
               not s.particle2.dead and \
               not s.snapped:
                s.apply()
        for p in self.particles:
            if not p.fixed:
                # Apply drag.                                                                                                                                              
                p.velocity.x *= 1.0 - min(1.0, self.drag)
                p.velocity.y *= 1.0 - min(1.0, self.drag)
                # Apply velocity.                                                                                                                                          
                p.force.x += p.velocity.x
                p.force.y += p.velocity.y
                # Limit the accumulated force and update the particle's position.                                                                                          
                self.limit(p, limit)
                p.x += p.force.x
                p.y += p.force.y
            if p.deadpoint:
                if abs(p.x-p.deadpoint[0]) < p.deadradius or abs(p.y-p.deadpoint[1]) < p.deadradius:
                    p.dead = True
            if p.life:
                # Apply lifespan.                                                                                                                                          
                p._age += 1
                p.dead = p._age > p.life

    def setGravity(self, gravity=(0,0)):
         self.gravity = isinstance(gravity, tuple) and Vector(*gravity) or gravity

