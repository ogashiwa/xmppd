#!/usr/local/bin/python3.2

from xml.etree import ElementTree as ET

class xmppxml:
    
    def _mkstreamtag(self,s):
        if s.find("<stream:stream ")!=-1:
            if s.find("</stream:stream>")!=-1: s=s.replace("</stream:stream>","")
            if s.find("/>")!=-1: s=s.replace("/>",">")
            s = "<?xml version='1.0'?>"+s
            pass
        return s
    
    def __init__(self):
        (self.header, self.tailer) = ('<stream:stream xmlns="xmlns" xmlns:stream="stream">', '</stream:stream>')
        pass
    
    def et(self,m):
        e = ET.fromstring(self.header + m + self.tailer)
        return e.find('*')
    
    def str(self,e):
        s = ET.tostring(e).decode('utf-8')
        s = self._mkstreamtag(s)
        return s
    
    def new(self,tag='',attrib={},text='',sub=[]):
        nt = ET.Element(tag)
        nt.text = text
        for k,v in attrib.items(): nt.set(k,v)
        for ee in sub: nt.append(ee)
        return nt
    
    def newstr(self,tag='',attrib={},text='',sub=[]):
        return self.str(self.new(tag,attrib,text,sub))
    
    pass

b = "<a>hoge</a><b>foo</b>"
x = xmppxml()
e = x.et(b)
print(x.str(e))

