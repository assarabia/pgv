import pcapy
import dpkt
import multiprocessing
import Queue
import socket

'''
usage 
  logger = PcapMonitor('en1')
  logger.start()
  p = logger.get_packet()
'''

class PcapMonitor(multiprocessing.Process):
    def __init__ (self, interface, filter=None):
        multiprocessing.Process.__init__(self)
        self.interface = interface
        self.filter = filter
        self.queue = multiprocessing.Queue(1000)
        #self.daemon = True

    def run(self):
        p = pcapy.open_live(self.interface, 1600, True, 1)
        p.loop(-1, self.handle_packet)

    def handle_packet (self, header, data):
        if self.queue.full():
            while self.queue.empty() is not True:
                self.queue.get()
            print 'pcap queue is full. cleared'
        if self.filter:
            fp = self.filter(data)
            if fp:
                self.queue.put_nowait(fp)
        else:
            eth = dpkt.ethernet.Ethernet(data)
            if eth:
                self.queue.put_nowait(eth)

    def get_packet (self):
        try:
            p = self.queue.get_nowait()
        except Queue.Empty:
            return None
        else:
            return  p

'''
VXLAN over MPSA packet parser
{'mpsa'  : {'src' : 'A.B.C.D', 'dst' : 'A.B.C.D'},
 'vxlan' : {'src' : 'A.B.C.D', 'dst' : 'A.B.C.D', 'vni' : 'xxx'},
 'inner' : {'src' : 'M.M.M', 'dst' : 'M.M.M'}}
'''
def mpsa_vxlan_filter(buf): 
    eth = dpkt.ethernet.Ethernet(buf)
    if type(eth.data) == dpkt.ip6.IP6:
        ip6 = eth.data
        mpsa = {'src' : socket.inet_ntop(socket.AF_INET6, ip6.src),
                'dst' : socket.inet_ntop(socket.AF_INET6, ip6.dst)}

        if type(ip6.data) == dpkt.esp.ESP:
            esp = ip6.data
            vxlan = {'src' : socket.inet_ntop(socket.AF_INET, esp.data[12:16]),
                     'dst' : socket.inet_ntop(socket.AF_INET, esp.data[16:20]),
                     'vni' : esp.data[32:35].encode("hex")}
            inner = {'dst' : esp.data[36:42].encode("hex"),
                     'src' : esp.data[42:48].encode("hex")}

            return {'mpsa'  : mpsa,
                    'vxlan' : vxlan,
                    'inner' : inner}
    return None

