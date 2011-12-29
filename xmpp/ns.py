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

XMLNS = 'xmlns'
XMLNS_STREAM = 'xmlns:stream'

XMPP_STREAMS  = 'urn:ietf:params:xml:ns:xmpp-streams'
XMPP_TLS      = 'urn:ietf:params:xml:ns:xmpp-tls'
XMPP_SASL     = 'urn:ietf:params:xml:ns:xmpp-sasl'
XMPP_BIND     = 'urn:ietf:params:xml:ns:xmpp-bind'
XMPP_SESSION  = 'urn:ietf:params:xml:ns:xmpp-session'

JABBER_ROSTER = 'jabber:iq:roster'
JABBER_CLIENT = 'jabber:client'
JABBER_SERVER = 'jabber:server'
JABBER_CMPNT  = 'jabber:component:accept'
              
ATRBT_FROM    = 'from'
ATRBT_TO      = 'to'
ATRBT_ID      = 'id'
ATRBT_TYPE    = 'type'
ATRBT_VER     = 'version'
ATRBT_XMLLANG = 'xml:lang'

IQTYPE_RESULT = 'result'
IQTYPE_SET    = 'set'
IQTYPE_GET    = 'get'

TAG_STST  = 'stream:stream'
TAG_STFE  = 'stream:features'
TAG_STER  = 'stream:error'
TAG_MECHS = 'mechanisms'
TAG_MECH  = 'mechanism'
TAG_CHLNG = 'challenge'
TAG_SUCC  = 'success'
TAG_FAIL  = 'failure'
TAG_IQ    = 'iq'
TAG_MSG   = 'message'
TAG_PRES  = 'presence'
TAG_BIND  = 'bind'
TAG_SESS  = 'session'
TAG_AUTH  = 'auth'
TAG_QUERY = 'query'

HTTP_ETHERX = "http://etherx.jabber.org/streams"
HTTP_IQAUTH = "http://jabber.org/features/iq-auth"
HTTP_CHSTAT = "http://jabber.org/protocol/chatstates"
HTTP_DINFO  = "http://jabber.org/protocol/disco#info"
HTTP_DITEMS = "http://jabber.org/protocol/disco#items"

AUTH_MD5    = "DIGEST-MD5"
AUTH_PLAIN  = "PLAIN"
AUTH_ANON   = "ANONYMOUS"

E_BAD_FORMAT      = "bad-format"
E_BAD_NSPREFIX    = "bad-namespace-prefix"
E_CONFLICT        = "conflict"
E_CONNECTION_TOUT = "connection-timeout"
E_HOST_GONE       = "host-gone"
E_HOST_UNKNOWN    = "host-unknown"
E_IMPROPER_ADDR   = "improper-addressing"
E_INTSERV_ERROR   = "internal-server-error"
E_INV_FROM        = "invalid-from"
E_INV_NAMESPACE   = "invalid-namespace"
E_INV_XML         = "invalid-xml"
E_NOT_AUTHORIZED  = "not-authorized"
E_NOT_WELL_FORMED = "not-well-formed"
E_POL_VIOLATION   = "policy-violation"
E_REMCON_FAILED   = "remote-connection-failed"
E_RESET           = "reset"
E_RES_CONSTRAINT  = "resource-constraint"
E_RESTRICTED_XML  = "restricted-xml"
E_SEE_OTHER_HOST  = "see-other-host"
E_SYSTEM_SHUTDOWN = "system-shutdown"
E_UNDEFINED_COND  = "undefined-condition"
E_UNSUP_ENCODING  = "unsupported-encoding"
E_UNSUP_FEATURE   = "unsupported-feature"
E_UNSUP_STNZ_TYPE = "unsupported-stanza-type"
E_UNSUP_VERSION   = "unsupported-version"
