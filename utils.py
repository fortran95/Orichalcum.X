def stripJID(jid):
    if '/' in jid:
        jid = jid.split('/',1)[0]
    return jid.strip()
