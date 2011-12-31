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

import hashlib, binascii, base64, re
import xml
import xml.etree.ElementTree
import xml.dom.minidom
import xml.parsers.expat
import xmpp

def getmsgtype(m):
    result = re.search(r'(?ms)[^<]*<([^ />]+)[^>]*>(.*)',str(m))
    if result is None: return ''
    n=str(result.group(1))
    if n=='stream:stream': return n
    if n.find(':') != -1: return n[n.find(':')+1:]
    return n

def getmsgto(m):
    result = re.search(r'(?ms)[^<]*<([^ />]+)[^>]*to=[\'"]*([^ \'"]+)[\'"]*[^>]*>(.*)',str(m))
    if result is None: return ''
    return str(result.group(2))

def getmsgfrom(m):
    res = re.search(r'(?ms)[^<]*<([^ />]+)[^>]*from=[\'"]*([^ \'"]+)[\'"]*[^>]*>(.*)',str(m))
    if res is None: return ''
    return str(res.group(2))

def getinttag(outtag, m):
    result = re.search(r'(?ms)[^<]*<{OT}[^>]*>(.*)</{OT}[^>]*>'.format(OT=outtag),str(m))
    if result is None: return ''
    return str(result.group(1))

def splitjid(jid):
    r = re.search(r'(?ms)([^@]+)@([^/]+)/(.+)',jid)
    if r is not None: return (r.group(1),r.group(2),r.group(3))
    r = re.search(r'(?ms)([^@]+)@([^/]+)',jid)
    if r is not None: return (r.group(1),r.group(2),'')
    return ('',jid,'')

class parser:
    def __init__(self):
        self.p = xml.parsers.expat.ParserCreate()
        self.p.StartElementHandler  = self.start
        self.p.EndElementHandler    = self.end
        self.p.CharacterDataHandler = self.data
        pass
    def close(self):
        self.p.Parse("", 1)
        del self.p
        pass
    def start(self, tag, attrs): pass
    def end(self, tag): pass
    def data(self, data): pass
    pass

class xmlblock():
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

class stfeat(parser):
    def __init__(self,d):
        parser.__init__(self)
        self._ctag = ''
        self.mechs = []
        self.p.Parse(d,0)
        pass
    def start(self,t,a): self._ctag = t
    def end(self,t): self._ctag = ''
    def data(self,d):
        if self._ctag == 'mechanism': self.mechs.append(d)
    pass

class sthdr(parser):
    def __init__(self, d):
        parser.__init__(self)
        (self.name, self.attrs) = ('',{})
        self.p.Parse(d, 0)
        pass
    def start(self, tag, attrs): (self.name, self.attrs) = (str(tag), attrs)
    pass

class response(parser):
    def __init__(self,d):
        parser.__init__(self)
        self.userinfo = {}
        self.p.Parse(d, 0)
        pass
    def data(self, data):
        b64str = str(data)
        binstr = base64.b64decode(b64str.encode("cp932"))
        xmpp.utils.dprint(binstr)
        tmpstr = ''
        for i in range(0,len(binstr)):
            tmpstr = tmpstr + chr(binstr[i])
            pass
        while len(tmpstr) is not 0:
            if tmpstr[0] == ',': tmpstr = tmpstr[1:]
            result = re.search(r'(?ms)([^=,]+)=([^,]+)(.*)',tmpstr)
            if result is None: tmpstr = ""
            else:
                v = result.group(2)
                if v[0] == '"': v = v[1:]
                if v[len(v)-1] == '"': v = v[:len(v)-1]
                self.userinfo[result.group(1)] = v
                tmpstr = result.group(3)
                pass
            pass
        pass
    pass

class auth(parser):
    def __init__(self,d):
        parser.__init__(self)
        self.mech = ""
        self.p.Parse(d, 0)
        pass
    def start(self, tag, attrs):
        if str(tag) == 'auth' and ('mechanism' in attrs):
            self.mech = str(attrs['mechanism'])
            pass
        pass
    pass

class authplain(parser):
    def __init__(self,d):
        parser.__init__(self)
        self.username = ''
        self.password = ''
        self.p.Parse(d, 0)
        pass
    def data(self, data):
        b64str = str(data)
        binstr = base64.b64decode(b64str.encode("cp932"))
        tmpstr = binstr
        i = 1
        for i in range(1,len(tmpstr)):
            if tmpstr[i] == 0: break
            self.username = self.username + chr(tmpstr[i])
            pass
        for i in range(i+1,len(tmpstr)):
            if tmpstr[i] == 0: break
            self.password = self.password + chr(tmpstr[i])
            pass
        pass
    pass

class hshake(parser):
    def __init__(self,d):
        parser.__init__(self)
        self.streamid = ''
        self.key = ''
        self.p.Parse(d, 0)
        pass
    def data(self, data):
        b64str = str(data)
        binstr = base64.b64decode(b64str.encode("cp932"))
        tmpstr = binstr
        i = 1
        for i in range(1,len(tmpstr)):
            if tmpstr[i] == 0: break
            self.streamid = self.streamid + chr(tmpstr[i])
            pass
        for i in range(i+1,len(tmpstr)):
            if tmpstr[i] == 0: break
            self.key = self.key + chr(tmpstr[i])
            pass
        pass
    pass

def getnstag(d):
    t = xml.etree.ElementTree.fromstring(d)
    return t.tag

class iqtest():
    def __init__(self,d):
        t = xml.etree.ElementTree.fromstring(d)
        print(t.tag)
        el = t.findall('*')
        print(el)
        for e in el:
            print(e.tag)
            pass
        pass
    pass

class iq(parser):
    def __init__(self,d):
        parser.__init__(self)
        self.iqattrs = {}
        self.iqtype = ''
        self.msgid = ''
        self.msgto = ''
        self.msgfrom = ''
        self.resource = ''
        self.xmlns = ''
        self._ctag = ''
        self.p.Parse(d, 0)
        pass
    def start(self, tag, attrs):
        self._ctag = str(tag)
        if self._ctag == 'iq': self.iqattrs = attrs;
        if self._ctag == 'iq' and 'id' in attrs: self.msgid  = attrs['id']
        if self._ctag == 'iq' and 'from' in attrs: self.msgfrom  = attrs['from']
        if self._ctag == 'iq' and 'to' in attrs: self.msgto  = attrs['to']
        if self._ctag == 'iq' and 'type' in attrs: self.iqtype = attrs['type']
        if self._ctag == 'bind' and 'xmlns' in attrs: self.xmlns  = attrs['xmlns']
        if self._ctag == 'session' and 'xmlns' in attrs: self.xmlns  = attrs['xmlns']
        if self._ctag == 'query' and 'xmlns' in attrs: self.xmlns  = attrs['xmlns']
        pass
    def data(self, data):
        if self._ctag == 'resource': self.resource = str(data)
        pass
    def end(self, tag):
        self._ctag = ''
        pass
    pass

class msg(parser):
    def __init__(self,d):
        parser.__init__(self)
        self.msgtype = ''
        self.msgto = ''
        self.msgid = ''
        self.body = ''
        self.p.Parse(d, 0)
        pass
    def start(self, tag, attrs):
        self.ctag = str(tag)
        if self.ctag == 'message' and 'type' in attrs: self.msgtype = attrs['type']
        if self.ctag == 'message' and 'to' in attrs: self.msgto = attrs['to']
        if self.ctag == 'message' and 'id' in attrs: self.msgid = attrs['id']
        pass
    def data(self, data):
        if self.ctag == 'body': self.body += str(data)
        pass
    def end(self, tag):
        self.ctag = ''
        pass
    pass

class presence(parser):
    def __init__(self,d):
        parser.__init__(self)
        self.status = ''
        self.show = ''
        self.type = ''
        self.priority = 0
        self.p.Parse(d,0)
        self._ctag = ''
        pass
    def start(self,tag,attrs):
        self._ctag = str(tag)
        if self._ctag == 'presence' and 'type' in attrs: self.type = attrs['type']
        pass
    def data(self,data):
        if self._ctag == 'priority': self.priority = int(str(data))
        if self._ctag == 'status': self.status = str(data)
        if self._ctag == 'show': self.show = str(data)
        pass
    def end(self,tag):
        self._ctag = ''
        pass
    pass
