#!/usr/local/bin/python3.2

import xml
from xml.etree import ElementTree as ET

class xmlblock:
    
    def __init__(self,d):
        self.p = xml.parsers.expat.ParserCreate()
        self.p.StartElementHandler  = self.start
        self.p.EndElementHandler    = self.end
        self.p.CharacterDataHandler = self.data
        self.d = d
        self.dep = 0
        try: self.p.Parse(self.d,0)
        except: pass
        pass
    def data(self, data): pass
    def start(self,tag,attrs): self.dep += 1
    def end(self,tag): self.dep -= 1
    def close(self):
        self.p.Parse("", 1)
        del self.p
        pass
    def get(self):
        if self.dep == 0 and self.p.CurrentByteIndex >= 4:
            return (self.d[:self.p.CurrentByteIndex],
                    self.d[self.p.CurrentByteIndex:])
        return ('', self.d)
    pass

_register_namespace_finished = False
def _register_namespace():
    global _register_namespace_finished
    if _register_namespace_finished == False:
        ET.register_namespace('', 'jabber:server')
        ET.register_namespace('db', 'jabber:server:dialback')
        ET.register_namespace('stream', 'http://etherx.jabber.org/streams')
        pass
    _register_namespace_finished = True
    pass

class xmsg:
    
    def _mkstreamtag(self,s):
        if s.find("<stream:stream ")!=-1:
            if s.find("</stream:stream>")!=-1: s=s.replace("</stream:stream>","")
            if s.find("/>")!=-1: s=s.replace("/>",">")
            s = "<?xml version='1.0'?>"+s
            pass
        return s
    
    def __init__(self,header, tag='', attrib={}, text='', sub=[]):
        _register_namespace()
        (self.header, self.tailer) = (header, '</stream:stream>')
        self.e = None
        if tag!='': self.create(tag,attrib,text,sub)
        pass
    
    def fromstring(self,m):
        tmp = ET.fromstring(self.header + m + self.tailer)
        self.e = tmp.find('*')
        pass
    
    def tostring(self):
        s = ET.tostring(self.e).decode('utf-8')
        s = self._mkstreamtag(s)
        return s
    
    def create(self, tag='', attrib={}, text='', sub=[]):
        nt = ET.Element(tag)
        nt.text = text
        for k,v in attrib.items(): nt.set(k,v)
        for ee in sub: nt.append(ee)
        self.e = nt
        pass
    
    pass
