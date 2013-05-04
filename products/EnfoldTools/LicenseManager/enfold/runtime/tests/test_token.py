import unittest

class TestToken(unittest.TestCase):

    def testValidateToken(self):
        import time
        from enfold.runtime.license import createToken, validateToken

        token = createToken()
        expected = time.strftime('%Y%m%d%H', time.gmtime())
        self.failUnless(validateToken(token, expected))

def test_suite():
    t = unittest.TestSuite()
    t.addTest(unittest.makeSuite(TestToken))
    return t
