# Copyright (c) 2011, Nobuo Ogashiwa <ogashiwa@wide.ad.jp>
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#     1. Redistributions of source code must retain the above copyright
#        notice, this list of conditions and the following disclaimer.
#
#     2. Redistributions in binary form must reproduce the above copyright
#        notice, this list of conditions and the following disclaimer in the
#        documentation and/or other materials provided with the distribution.
#
#     3. Neither the name of the <organization> nor the
#        names of its contributors may be used to endorse or promote products
#        derived from this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

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
