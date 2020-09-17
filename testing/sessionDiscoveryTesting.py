import unittest
import code.session

class NamesTestCase(unittest.TestCase):

   def test_first_last_name(self):
       testSession = Code.session.enlightSession("TestSession", role = Code.session.HOST)
       testSession.initConnection()
       self.assertEqual(testSession.getSessionMembers(), [])