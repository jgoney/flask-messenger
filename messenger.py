import os
import sqlite3

from flask import Flask, abort, jsonify, make_response, redirect, render_template, request

import settings

app = Flask(__name__)
app.config.from_object(settings.Config)

# Helper functions
def _get_message(id=None):
    """Return a list of message objects (as dicts)"""
    with sqlite3.connect(app.config['DATABASE']) as conn:
        c = conn.cursor()

        if id:
            id = int(id)  # Ensure that we have a valid id value to query
            q = "SELECT * FROM messages WHERE id=? ORDER BY dt DESC"
            rows = c.execute(q, (id,))

        else:
            q = "SELECT * FROM messages ORDER BY dt DESC"
            rows = c.execute(q)

        return [{'id': r[0], 'dt': r[1], 'message': r[2], 'sender': r[3]} for r in rows]

# Custom error handlers
@app.errorhandler(400)
def not_found(error):
    return make_response(jsonify({'error': 'Bad request'}), 400)

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

# Standard routing
@app.route('/', methods = ['GET', 'POST'])
def home():
    if request.method == 'POST':
        with sqlite3.connect(app.config['DATABASE']) as conn:
            c = conn.cursor()
            q = "INSERT INTO messages VALUES (NULL, datetime('now'),?,?)"
            c.execute(q, (request.form['message'], request.form['username']))
            conn.commit()
            redirect('/')

    return render_template('index.html', messages=_get_message())

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/admin', methods = ['GET', 'POST'])
def admin():
    return render_template('admin.html', messages=reversed(_get_message()))

# RESTful routing
@app.route('/messages/api', methods=['GET'])
@app.route('/messages/api/<int:id>', methods=['GET'])
def get_message_by_id(id=None):
    messages = _get_message(id)
    if not messages:
        abort(404)

    return jsonify({'messages': messages})

@app.route('/messages/api', methods=['POST'])
def create_message():
    if not request.json or not 'message' in request.json or not 'sender' in request.json:
        abort(400)

    with sqlite3.connect(app.config['DATABASE']) as conn:
        c = conn.cursor()
        q = "INSERT INTO messages VALUES (NULL, datetime('now'),?,?)"
        c.execute(q, (request.json['message'], request.json['sender']))
        conn.commit()

    return get_message_by_id(c.lastrowid), 201

@app.route('/messages/api/<int:id>', methods=['DELETE'])
def delete_message_by_id(id):
    with sqlite3.connect(app.config['DATABASE']) as conn:
        c = conn.cursor()
        q = "DELETE FROM messages WHERE id=?"
        c.execute(q, (id,))
        conn.commit()
    return jsonify({'result': True})


if __name__ == '__main__':

    if not os.path.exists(app.config['DATABASE']):
        try:
            conn = sqlite3.connect(app.config['DATABASE'])
            # Give absolute path for testing environment
            sql_path = os.path.join(app.config['APP_ROOT'], 'db_init.sql')  # TODO: simplify this for production
            cmd = open(sql_path, 'r').read()
            c = conn.cursor()
            c.execute(cmd)
            conn.commit()
            conn.close()
        except IOError:
            print "Couldn't initialize the database, exiting..."
            raise
        except sqlite3.OperationalError:
            print "Couldn't execute the SQL, exiting..."
            raise

    app.run(host='0.0.0.0')
