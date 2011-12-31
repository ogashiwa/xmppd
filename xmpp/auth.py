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
import xmpp.utils as utils
import xmpp.ns as ns
from xmpp.msg import xmsg as xm

def md5ch1(h, r, n):
    chal = 'realm="{R}",nonce="{N}",qop="auth",charset=utf-8,algorithm=md5-sess'
    chal = chal.format(R=r, N=n)
    chal = chal.encode("cp932")
    b64str = binascii.b2a_base64(chal).decode("utf-8")
    b64str = b64str.replace('\n', '')
    m = xm(h,tag=ns.TAG_CHLNG,attrib={ns.XMLNS:ns.XMPP_SASL},text=b64str)
    return m.tostring()

def success(sthdr, rspauth=''):
    ratext = ''
    if rspauth != '':
        chal = ('rspauth={R}'.format(R=rspauth)).encode("cp932")
        b64str = binascii.b2a_base64(chal).decode("utf-8")
        ratext = b64str.replace('\n', '')
        pass
    m = xm(sthdr,tag=ns.TAG_SUCC,attrib={ns.XMLNS:ns.XMPP_SASL},text=ratext)
    return m.tostring()

def failure(sthdr):
    m = xm(sthdr,
             tag=ns.TAG_FAIL,
             attrib={ns.XMLNS:ns.XMPP_SASL},
           sub=[xm(sthdr,"temporary-auth-failure")])
    return m.tostring()+"</stream:stream>"

class MechDigestMD5:
    def HHD(self,n): return hashlib.md5(n).hexdigest()
    def HH(self,n): return hashlib.md5(bytes(n,encoding='ascii')).hexdigest()
    def H(self,n): return hashlib.md5(bytes(n,encoding='ascii')).digest()
    def C(self,n): return ':'.join(n)
    def B(self,n): return bytes(n, encoding='ascii')
    def CreateA1(self,A0,no,cn):
        R=bytearray()
        R+=self.H(A0)
        R+=self.B(':')
        for c in no: R+=self.B(c)
        R+=self.B(':')
        for c in cn: R+=self.B(c)
        return R
    def GetDigestMD5Str(self, username, password, realm, nonce, cnonce, nc, uri, qop, ver):
        utils.dprint(username)
        utils.dprint(password)
        utils.dprint(realm)
        utils.dprint(nonce)
        utils.dprint(cnonce)
        utils.dprint(nc)
        utils.dprint(uri)
        utils.dprint(qop)
        A0=self.C([username,realm,password])
        A1=self.CreateA1(A0,nonce,cnonce)
        A2=self.C(['AUTHENTICATE',uri])
        A2_2=':'+uri
        if ver==1:
            response = self.HH(self.C([self.HHD(A1),nonce,nc,cnonce,qop,self.HH(A2)]))
        else:
            response = self.HH(self.C([self.HHD(A1),nonce,nc,cnonce,qop,self.HH(A2_2)]))
        return response
    def __init__(self, man):
        self.manager = man
        self.realm = self.manager.servname
        self.nonce = utils.randstr(14)
        self.STATE_INIT         = 0
        self.STATE_CHALLENGE    = 1
        self.STATE_CHALLENGEOK  = 2
        self.state = 0
        pass
    
    def response(self,data):
        userinfo={}
        b64str = str(data)
        binstr = base64.b64decode(b64str.encode("cp932"))
        utils.dprint(binstr)
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
                userinfo[result.group(1)] = v
                tmpstr = result.group(3)
                pass
            pass
        return userinfo
                
    def proc(self, m):
        if self.state == self.STATE_INIT:
            m = md5ch1(self.manager.sendsthdr,self.realm, self.nonce)
            self.manager.CBF_SendFunc(m)
            self.state = self.STATE_CHALLENGE
            pass
        elif self.state == self.STATE_CHALLENGE:
            x=xm(self.manager.recvsthdr)
            x.fromstring(m)
            userinfo = self.response(x.e.text)
            self.manager.username = userinfo["username"]
            u = userinfo["username"]
            username = u
            password = self.manager.CBF_GetPasswordFunc(u)
            realm = self.realm
            nonce = self.nonce
            cnonce = userinfo["cnonce"]
            nc = userinfo["nc"]
            uri = userinfo["digest-uri"]
            qop = userinfo["qop"]
            response = userinfo["response"]
            chkreshex = self.GetDigestMD5Str(username, password,
                                             realm, nonce, cnonce, nc, uri, qop, 1)
            utils.dprint("RECV: "+response)
            utils.dprint("SEND: "+chkreshex)
            if chkreshex == response: authresult = True
            else: authresult = False
            if authresult == True:
                ra = self.GetDigestMD5Str(username, password,
                                          realm, nonce, cnonce, nc, uri, qop, 2)
                m = success(self.manager.sendsthdr,ra)
                self.manager.CBF_SendFunc(m)
                self.state = self.STATE_CHALLENGEOK
                self.manager.authenticated = True
                self.manager.CBF_AuthenticatedFunc(True)
                pass
            else:
                m = failure(self.manager.sendsthdr)
                self.manager.CBF_SendFunc(m)
                self.manager.authenticated = False
                self.manager.CBF_AuthenticatedFunc(False)
                pass
            pass
        pass
    pass

class MechPlain:
    def __init__(self, man):
        self.manager = man
        pass
    def plainparse(self,data):
        b64str = str(data)
        binstr = base64.b64decode(b64str.encode("cp932"))
        tmpstr = binstr
        i = 1
        (username,password)=('','')
        for i in range(1,len(tmpstr)):
            if tmpstr[i] == 0: break
            username = username + chr(tmpstr[i])
            pass
        for i in range(i+1,len(tmpstr)):
            if tmpstr[i] == 0: break
            password = password + chr(tmpstr[i])
            pass
        return (username,password)

    def proc(self, m):
        x = xm(self.manager.recvsthdr)
        x.fromstring(m)
        (self.manager.username,pw)=self.plainparse(x.e.text)
        if pw == self.manager.CBF_GetPasswordFunc(self.manager.username):
            m = success(self.manager.sendsthdr)
            self.manager.CBF_SendFunc(m)
            self.manager.authenticated = True
            x=xm('')
            x.create(tag='stream:stream',
                     attrib={'from':self.manager.servname,
                             'version':"1.0",
                             'xmlns':"jabber:client",
                             'xmlns:stream':"http://etherx.jabber.org/streams",
                             'xmlns:xml':"http://www.w3.org/XML/1998/namespace"})
            self.manager.CBF_SendFunc(x.tostring())
            self.manager.CBF_AuthenticatedFunc(True)
            pass
        else:
            m = failure(self.manager.sendsthdr)
            self.manager.CBF_SendFunc(m)
            self.manager.authenticated = False
            self.manager.CBF_AuthenticatedFunc(False)
            pass
        pass
    pass

class MechAnonymous:
    def __init__(self, man):
        self.manager = man
        pass
    def proc(self, m):
        m = success(self.manager.sendsthdr)
        self.manager.CBF_SendFunc(m)
        self.manager.authenticated = True
        self.manager.CBF_AuthenticatedFunc(True)
        pass
    pass

class manager:
    def __init__(self, servname, SendFunc, GetPasswordFunc, AuthenticatedFunc):
        self.mechlist = {ns.AUTH_MD5:MechDigestMD5,
                         ns.AUTH_PLAIN:MechPlain,
                         ns.AUTH_ANON:MechAnonymous}
        self.CBF_SendFunc = SendFunc
        self.CBF_GetPasswordFunc = GetPasswordFunc
        self.CBF_AuthenticatedFunc = AuthenticatedFunc
        self.servname = servname
        self.username = ""
        self.authenticated = False
        self.mech = None
        self.sendsthdr = ''
        self.recvsthdr = ''
        pass
    def ProcMsgAuthentication(self, m):
        x = xm(self.recvsthdr)
        x.fromstring(m)
        mc = x.e.attrib['mechanism']
        if self.mech is None:
            self.mech = self.mechlist[mc].__call__(self)
            self.mech.proc(m)
            pass
        pass
    def proc(self, m):
        x = xm(self.recvsthdr)
        x.fromstring(m)
        msgtype = x.e.tag
        pos=msgtype.find('}')
        if pos>0: msgtype = msgtype[pos+1:]
        utils.dprint(msgtype)
        if self.mech is None: self.ProcMsgAuthentication(m)
        else: self.mech.proc(m)
        pass
    pass
