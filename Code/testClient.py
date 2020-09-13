import session, time

userSession = session.enlightSession("myLocalSession", role = session.USER)
userSession.initConnection()
time.sleep(8)
print(list(userSession.allOnlineSessions.keys())[0])
userSession.join(list(userSession.allOnlineSessions.keys())[0])
time.sleep(8)
userSession.leave()
