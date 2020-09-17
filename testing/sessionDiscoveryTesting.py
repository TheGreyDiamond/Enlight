from src import session
import unittest


class NamesTestCase(unittest.TestCase):

   def test_first_last_name(self):
       testSession = session.enlightSession("TestSession", role = session.HOST)
       testSession.initConnection()
       self.assertEqual(testSession.getSessionMembers(), [])