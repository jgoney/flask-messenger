import json
import os
import sqlite3
import tempfile
import unittest

import messenger
import settings


class MessengerBaseTestCase(unittest.TestCase):

    def setUp(self):
        """Create a temporary database and create the needed table"""
        messenger.app.config.from_object(settings)
        self.db_fd, messenger.app.config['DATABASE'] = tempfile.mkstemp()
        messenger.app.config['TESTING'] = True
        self.app = messenger.app.test_client()

        with sqlite3.connect(messenger.app.config['DATABASE']) as conn:
            sql_path = os.path.join(messenger.app.config['APP_ROOT'], 'db_init.sql')
            with open(sql_path, 'r') as sql_file:
                cmd = sql_file.read()
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
        self.assertIn(b'"error": "Not found"', rv.data)

    def test_post_empty_db(self):
        """POST a message to an empty database"""
        data = json.dumps({'message': 'Test', 'sender': 'jgoney'})
        rv = self.app.post('/messages/api', data=data, content_type='application/json')

        # Check error code
        self.assertEqual(rv.status_code, 201)

        # Decode JSON response and store object id
        resp = rv.get_json()

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
        """Add a single message to the database for testing"""
        super(MessengerSingleTestCase, self).setUp()
        with sqlite3.connect(messenger.app.config['DATABASE']) as conn:
            cmd = "INSERT INTO messages VALUES (NULL, datetime('now'), 'Test', 'jgoney')"
            c = conn.cursor()
            c.execute(cmd)
            conn.commit()

    def test_get_single(self):
        """Tests fetching a single message"""
        rv = self.app.get('/messages/api/1')

        # Check error code
        self.assertEqual(rv.status_code, 200)

        resp = rv.get_json()

        self.assertEqual('jgoney', resp['messages'][0]['sender'])
        self.assertEqual('Test', resp['messages'][0]['message'])

    def test_delete_single(self):
        """Tests deleting a single message"""
        rv = self.app.delete('/messages/api/1')
        self.assertEqual(rv.status_code, 200)

        resp = rv.get_json()
        self.assertTrue(resp['result'])

    def test_delete_wrong_id(self):
        """Tests deleting a single message with a non-int id"""
        rv = self.app.delete('/messages/api/foo')
        self.assertEqual(rv.status_code, 404)
        self.assertIn(b'<title>404 Not Found</title>', rv.data)


class MessengerMultipleTestCase(MessengerBaseTestCase):

    def setUp(self):
        """Adds multiple messages to the database for testing"""
        super(MessengerMultipleTestCase, self).setUp()
        with sqlite3.connect(messenger.app.config['DATABASE']) as conn:
            c = conn.cursor()
            for i in range(5):
                cmd = "INSERT INTO messages VALUES (NULL, datetime('now'), ?, ?)"
                m = 'message #%s' % (i,)
                s = 'sender #%s' % (i,)
                c.execute(cmd, (m, s))
            conn.commit()

    def test_delete_multiple(self):
        """Tests deleting multiple messages at once"""
        rv = self.app.delete('/messages/api/1')
        self.assertEqual(rv.status_code, 200)
        self.assertIn(b'"result": true', rv.data)

    def test_delete_multiple_admin_page(self):
        """Tests deleting multiple messages at once through admin interface"""

        # Set the proper session variable so that login works
        with self.app as c:
            with c.session_transaction() as session:
                session['logged_in'] = True

            # Assert that the setup messages are there
            rv = c.get('/admin', follow_redirects=True)
            self.assertIn(b'message #0', rv.data)
            self.assertIn(b'message #1', rv.data)
            self.assertEqual(rv.status_code, 200)

            # Assert that after POST, the chosen messages are deleted
            rv = c.post('/admin', data=dict(
                delete1='on',
                delete2='on'
            ), follow_redirects=True)
            self.assertNotIn(b'message #0', rv.data)
            self.assertNotIn(b'message #1', rv.data)
            self.assertEqual(rv.status_code, 200)


class MessengerMiscTestCase(MessengerBaseTestCase):

    def test_login_logout(self):
        """Tests login/logout functionality"""

        # Test successful login
        rv = self.login('admin', '123')
        self.assertIn(b'Logout', rv.data)
        self.assertEqual(rv.status_code, 200)

        # Test successful logout
        rv = self.logout()
        self.assertIn(b'Login', rv.data)
        self.assertEqual(rv.status_code, 200)

        # Test wrong username
        rv = self.login('adminx', '123')
        self.assertIn(b'Invalid username and/or password', rv.data)
        self.assertEqual(rv.status_code, 200)

        # Test wrong password
        rv = self.login('admin', '123x')
        self.assertIn(b'Invalid username and/or password', rv.data)
        self.assertEqual(rv.status_code, 200)

    def test_about_page(self):
        """Tests that about page renders"""
        rv = self.app.get('/about')
        self.assertIn(b'About page, nothing to see here.', rv.data)
        self.assertEqual(rv.status_code, 200)

    def test_home_page(self):
        """Tests creating a message through home page interface"""

        # Assert that message is not present
        rv = self.app.get('/')
        self.assertNotIn(b'test user', rv.data)
        self.assertNotIn(b'test message', rv.data)

        # Add message
        rv = self.app.post('/', data=dict(
            username="test user",
            message="test message"
        ), follow_redirects=True)

        # Assert that message has been added
        self.assertIn(b'test user', rv.data)
        self.assertIn(b'test message', rv.data)
        self.assertEqual(rv.status_code, 200)

    def test_admin_page_redirect(self):
        """Tests that the admin page redirects work as intended"""
        rv = self.app.get('/admin', follow_redirects=True)

        self.assertIn(b'Please login:', rv.data)
        self.assertEqual(rv.status_code, 200)

        with self.app as c:
            with c.session_transaction() as session:
                session['logged_in'] = True
            rv = c.get('/admin', follow_redirects=True)
        self.assertIn(b'No messages found.', rv.data)
        self.assertEqual(rv.status_code, 200)

if __name__ == '__main__':
    unittest.main()
