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

import binascii
import xml.etree.ElementTree
import xml.dom.minidom
import xml.parsers.expat
import xmpp.msg
from xmpp.msg import xmsg
import xmpp.utils
import xmpp.ns as ns
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom.minidom import parseString
from xmpp.utils import randstr

def sthdr(afrom='', type='', msgid='', xmlnsdb=''):
    tst = Element(ns.TAG_STST)
    tst.set(ns.ATRBT_VER, "1.0")
    if msgid!='no': tst.set(ns.ATRBT_ID, randstr(8))
    tst.set(ns.ATRBT_FROM, afrom)
    tst.set(ns.XMLNS, type)
    tst.set(ns.XMLNS_STREAM, ns.HTTP_ETHERX)
    if xmlnsdb != '': tst.set('xmlns:db', "jabber:server:dialback")
    tdummy = SubElement(tst, "DUMMY")
    rough_string = tostring(tst, 'utf-8')
    reparsed = parseString(rough_string)
    fullxml = reparsed.toprettyxml(indent="")
    return fullxml[0:fullxml.find("<DUMMY")-1]

def featdback():
    tst = Element(ns.TAG_STFE)
    tmechs = SubElement(tst, "dialback")
    tmechs.set(ns.XMLNS, "urn:xmpp:features:dialback")
    tmech = SubElement(tmechs, 'optional')
    return tostring(tst).decode("utf-8")

def featmech():
    tst = Element(ns.TAG_STFE)
    tmechs = SubElement(tst, ns.TAG_MECHS)
    tmechs.set(ns.XMLNS, ns.XMPP_SASL)
    tmech_1 = SubElement(tmechs, ns.TAG_MECH)
    tmech_1.text = "PLAIN"
    tmech_2 = SubElement(tmechs, ns.TAG_MECH)
    tmech_2.text = "DIGEST-MD5"
    tmech_3 = SubElement(tmechs, ns.TAG_MECH)
    tmech_3.text = "ANONYMOUS"
    tauth = SubElement(tst, ns.TAG_AUTH)
    tauth.set(ns.XMLNS, ns.HTTP_IQAUTH)
    return tostring(tst).decode("utf-8")

def auth(username, password):
    ta = Element(ns.TAG_AUTH)
    ta.set(ns.XMLNS, ns.XMPP_SASL)
    ta.set('mechanism', 'PLAIN')
    s = "\0"+username+"\0"+password+"\0"
    s = s.encode("cp932")
    ta.text = binascii.b2a_base64(s).decode("utf-8")
    return tostring(ta).decode("utf-8")    

def md5ch1(h, r, n):
    chal = 'realm="{R}",nonce="{N}",qop="auth",charset=utf-8,algorithm=md5-sess'
    chal = chal.format(R=r, N=n)
    chal = chal.encode("cp932")
    b64str = binascii.b2a_base64(chal).decode("utf-8")
    b64str = b64str.replace('\n', '')
    m = xmsg(h,tag=ns.TAG_CHLNG,attrib={ns.XMLNS:ns.XMPP_SASL},text=b64str)
    return m.tostring()

def success(sthdr, rspauth=''):
    ratext = ''
    if rspauth != '':
        chal = ('rspauth={R}'.format(R=rspauth)).encode("cp932")
        b64str = binascii.b2a_base64(chal).decode("utf-8")
        ratext = b64str.replace('\n', '')
        pass
    m = xmsg(sthdr,tag=ns.TAG_SUCC,attrib={ns.XMLNS:ns.XMPP_SASL},text=ratext)
    return m.tostring()

def failure(sthdr):
    m = xmsg(sthdr,
             tag=ns.TAG_FAIL,
             attrib={ns.XMLNS:ns.XMPP_SASL},
             sub=[xmsg(sthdr,"temporary-auth-failure")])
    return m.tostring()+"</stream:stream>"

def featbs():
    tst = Element(ns.TAG_STFE)
    tbind = SubElement(tst, ns.TAG_BIND)
    tbind.set(ns.XMLNS, ns.XMPP_BIND)
    tsess = SubElement(tst, ns.TAG_SESS)
    tsess.set(ns.XMLNS, ns.XMPP_SESSION)
    return tostring(tst).decode("utf-8")

def bindres(jid, msgid):
    tiq = Element("iq")
    #tiq.set("to", jid) # why???
    tiq.set("type", "result")
    tiq.set("id", msgid)
    tbind = SubElement(tiq, "bind")
    tbind.set("xmlns", ns.XMPP_BIND)
    tjid = SubElement(tbind, "jid")
    tjid.text = jid
    return tostring(tiq).decode("utf-8")

def iq(iqattrs, internal):
    tiq = "<iq "
    for k,v in iqattrs.items():
        if len(v) == 0: continue
        tiq += (k + '="' + v + '" ')
        pass
    tiq += ">"
    tiq += internal
    tiq += "</iq>"
    return tiq


def addfrom(m, mfrom):
    t = xml.etree.ElementTree.fromstring(m)
    t.set("from", mfrom)
    a = tostring(t).decode("utf-8")
    return a

def iqres(msgid):
    tiq = Element("iq")
    #tiq.set("to", jid) # why???
    tiq.set("type", "result")
    tiq.set("id", msgid)
    return tostring(tiq).decode("utf-8")

def msg(msgid, mtype, mfrom, mto, body):
    tmsg = Element("message")
    tmsg.set("xmlns", "jabber:client")
    tmsg.set("type", mtype)
    tmsg.set("to", mto)
    tmsg.set("from", mfrom)
    tmsg.set("id", msgid)
    tbody = SubElement(tmsg, "body")
    tbody.text = body
    tactive = SubElement(tmsg, "active")
    tactive.set(ns.XMLNS, ns.HTTP_CHSTAT)
    return tostring(tmsg).decode("utf-8")    
    
def rosterres(msgid, mfrom, mto, rosterlist):
    tiq = Element("iq")
    tiq.set("type", "result")
    tiq.set("id", msgid)
    tiq.set("from", mfrom)
    tiq.set("to", mto)
    tquery = SubElement(tiq, "query")
    tquery.set("xmlns", ns.JABBER_ROSTER)
    for jid, v in rosterlist.items():
        ali = v[0]
        drc = v[1]
        titem = SubElement(tquery, "item")
        titem.set("jid", jid)
        titem.set("name", ali)
        titem.set("subscription", drc)
        pass
    return tostring(tiq).decode("utf-8")

def dinfo(msgid,mfrom,mto,icat,itype,iname,flist):
    tiq = Element("iq")
    tiq.set("type", "result")
    tiq.set("id", msgid)
    tiq.set("from", mfrom)
    tiq.set("to", mto)
    tquery = SubElement(tiq, "query")
    tquery.set("xmlns", ns.HTTP_DINFO)
    tid = SubElement(tquery, "identity")
    if len(icat)>0: tid.set("category", icat)
    if len(itype)>0: tid.set("type", itype)
    if len(iname)>0: tid.set("name", iname)
    for item in flist:
        tit = SubElement(tquery, "feature")
        tit.set("var", item)
        pass
    return tostring(tiq).decode("utf-8")    

def ditems(msgid,mfrom,mto,dlist):
    tiq = Element("iq")
    tiq.set("type", "result")
    tiq.set("id", msgid)
    tiq.set("from", mfrom)
    tiq.set("to", mto)
    tquery = SubElement(tiq, "query")
    tquery.set("xmlns", ns.HTTP_DITEMS)
    for item in dlist:
        tit = SubElement(tquery, "item")
        tit.set("jid", item)
        pass
    return tostring(tiq).decode("utf-8")    

def presence(mfrom, mto, mtype, status, show):
    tp = Element("presence")
    tp.set("xmlns", ns.JABBER_CLIENT)
    tp.set("from", mfrom)
    tp.set("to", mto)
    if len(mtype) > 0: tp.set("type", mtype)
    if len(status) > 0:
        ts = SubElement(tp, "status")
        ts.text = status
        pass
    if len(show) > 0:
        th = SubElement(tp, "show")
        th.text = show
        pass
    return tostring(tp).decode("utf-8")

def presence_ret(mfrom, mto, mtype, status, show):
    tp = Element("presence")
    tp.set("from", mfrom)
    tp.set("to", mto)
    if len(mtype) > 0: tp.set("type", mtype)
    if len(status) > 0:
        ts = SubElement(tp, "status")
        ts.text = status
        pass
    if len(show) > 0:
        th = SubElement(tp, "show")
        th.text = show
        pass
    return tostring(tp).decode("utf-8")

def ping(mfrom, mto):
    tq = Element("iq")
    tq.set("from", mfrom)
    tq.set("to", mto)
    tq.set("id", randstr(8))
    tq.set("type", "get")
    tp = SubElement(tq, "ping")
    tp.set("xmlns", "urn:xmpp:ping")
    return tostring(tq).decode("utf-8")

def pong(mfrom, mto, mid):
    tq = Element("iq")
    tq.set("from", mfrom)
    tq.set("to", mto)
    tq.set("id", mid)
    tq.set("type", "result")
    return tostring(tq).decode('utf-8')    

def iqverres(mid, mfrom, mto, n, v):
    tq = Element("iq")
    tq.set("from", mfrom)
    tq.set("to", mto)
    tq.set("id", mid)
    tq.set("type", "result")
    tp = SubElement(tq, "query")
    tp.set("xmlns", "jabber:iq:version")
    tn = SubElement(tp, "name")
    tn.set("name", n)
    tv = SubElement(tp, "version")
    tv.set("version", v)
    return tostring(tq).decode("utf-8")

def sterr(reason):
    te = Element(ns.TAG_STER)
    tna = SubElement(te, reason)
    tna.set(ns.XMLNS, ns.XMPP_STREAMS)
    return tostring(te).decode("utf-8")

def hshake(stid, secret):
    th = Element("handshake")
    if stid != "" and secret != "":
        s = "\0"+stid+"\0"+secret+"\0"
        s = s.encode("cp932")
        th.text = binascii.b2a_base64(s).decode("utf-8")
        pass
    return tostring(th).decode("utf-8")

def stclose():
    return "</stream:stream>"
