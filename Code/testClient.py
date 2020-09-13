import session, time

userSession = session.enlightSession("myLocalSession", role = session.USER)
userSession.initConnection()
time.sleep(1)
userSession.join("iq9vf96Ba1hNA6RsQwv19OWI")
time.sleep(8)
userSession.leave()
