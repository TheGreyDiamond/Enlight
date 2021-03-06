import sys
sys.path.append('mainCode/../')
import mainCode.session
import unittest
import time


class SessionTesting(unittest.TestCase):

    def setUp(self):
        self.testSession = mainCode.session.enlightSession("TestSession", role = mainCode.session.HOST)
        self.testSession.initConnection()

    def test_check_if_members_are_empty(self):
        time.sleep(1)
        members = self.testSession.getSessionMembers()
        self.assertEqual(members, [])
    
    def test_if_allow_join_is_okay(self):
        time.sleep(2)
        self.assertEqual(self.testSession.allowJoin, True)

    def test_if_var_and_func_return_same(self):
        time.sleep(3)
        self.assertEqual(self.testSession.sessionId, self.testSession.getSessionId())
    
    def test_if_connection_works(self):
        self.recSession = mainCode.session.enlightSession("LocalSession", role = mainCode.session.USER)
        self.recSession.initConnection()
        time.sleep(1)
        sessnId = list(self.recSession.allOnlineSessions.keys())[0]
        print(sessnId)
        self.recSession.leave()
        self.assertEqual(self.testSession.getSessionId(), sessnId)
    
    def tearDown(self):
        self.testSession.stopSession()

if __name__ == '__main__':
   unittest.main()
