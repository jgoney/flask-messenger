import json
import os
import sqlite3
import tempfile
import unittest

import messenger
import settings


class MessengerBaseTestCase(unittest.TestCase):

    def setUp(self):
        messenger.app.config.from_object(settings.Config)
        self.db_fd, messenger.app.config['DATABASE'] = tempfile.mkstemp()
        messenger.app.config['TESTING'] = True
        self.app = messenger.app.test_client()

        with sqlite3.connect(messenger.app.config['DATABASE']) as conn:
            sql_path = os.path.join(messenger.app.config['APP_ROOT'], 'db_init.sql')  # TODO: simplify this for production
            cmd = open(sql_path, 'r').read()
            c = conn.cursor()
            c.execute(cmd)
            conn.commit()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(messenger.app.config['DATABASE'])

    # Helper functions for testing login/logout
    def login(self, username, password):
        return self.app.post('/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    def logout(self):
        return self.app.get('/logout', follow_redirects=True)


class MessengerEmptyTestCase(MessengerBaseTestCase):

    def test_get_empty_db(self):
        """A GET on an empty database should return 404 Not found"""
        rv = self.app.get('/messages/api')
        self.assertEqual(rv.status_code, 404)
        self.assertIn('"error": "Not found"', rv.data)

    def test_post_empty_db(self):
        """POST a message to an empty database"""
        data = json.dumps({'message': 'Test', 'sender': 'jgoney'})
        rv = self.app.post('/messages/api', data=data, content_type='application/json')

        # Check error code
        self.assertEqual(rv.status_code, 201)

        # Decode JSON response and store object id
        resp = json.loads(rv.data)

        self.assertEqual('jgoney', resp['messages'][0]['sender'])
        self.assertEqual('Test', resp['messages'][0]['message'])

    def test_post_bad_request(self):
        """Not setting the Content-Type will return a 400 status code"""
        data = json.dumps({'message': 'Test', 'sender': 'jgoney'})
        rv = self.app.post('/messages/api', data=data)

        # Check error code
        self.assertEqual(rv.status_code, 400)


class MessengerSingleTestCase(MessengerBaseTestCase):

    def setUp(self):
        super(MessengerSingleTestCase, self).setUp()
        with sqlite3.connect(messenger.app.config['DATABASE']) as conn:
            cmd = "INSERT INTO messages VALUES (NULL, datetime('now'), 'Test', 'jgoney')"
            c = conn.cursor()
            c.execute(cmd)
            conn.commit()

    def test_get_single(self):
        # Fetch a single message
        rv = self.app.get('/messages/api/1')

        # Check error code
        self.assertEqual(rv.status_code, 200)

        resp = json.loads(rv.data)

        self.assertEqual('jgoney', resp['messages'][0]['sender'])
        self.assertEqual('Test', resp['messages'][0]['message'])

    def test_delete_single(self):
        # Delete a single message
        rv = self.app.delete('/messages/api/1')
        self.assertEqual(rv.status_code, 200)
        self.assertIn('"result": true', rv.data)

    def test_delete_wrong_id(self):
        # Try to delete a single message with a non-int id
        rv = self.app.delete('/messages/api/foo')
        self.assertEqual(rv.status_code, 404)
        self.assertIn('"error": "Not found"', rv.data)


class MessengerMultipleTestCase(MessengerBaseTestCase):

    def setUp(self):
        super(MessengerMultipleTestCase, self).setUp()
        with sqlite3.connect(messenger.app.config['DATABASE']) as conn:
            c = conn.cursor()
            for i in xrange(5):
                cmd = "INSERT INTO messages VALUES (NULL, datetime('now'), ?, ?)"
                m = 'message #%s' % (i,)
                s = 'sender #%s' % (i,)
                c.execute(cmd, (m, s))
            conn.commit()

    def test_delete_multiple(self):
        # Delete multiple messages at once
        rv = self.app.delete('/messages/api/1')
        self.assertEqual(rv.status_code, 200)
        self.assertIn('"result": true', rv.data)


class MessengerMiscTestCase(MessengerBaseTestCase):

    def test_login_logout(self):
        # Test successful login
        rv = self.login('admin', '123')
        self.assertIn('Logout', rv.data)
        self.assertEqual(rv.status_code, 200)

        # Test successful logout
        rv = self.logout()
        self.assertIn('Login', rv.data)
        self.assertEqual(rv.status_code, 200)

        # Test wrong username
        rv = self.login('adminx', '123')
        self.assertIn('Invalid username and/or password', rv.data)
        self.assertEqual(rv.status_code, 200)

        # Test wrong password
        rv = self.login('admin', '123x')
        self.assertIn('Invalid username and/or password', rv.data)
        self.assertEqual(rv.status_code, 200)

    def test_about_page(self):
        rv = self.app.get('/about')
        self.assertIn('About page, nothing to see here.', rv.data)
        self.assertEqual(rv.status_code, 200)


if __name__ == '__main__':
    unittest.main()
