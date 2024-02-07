import logging
import string
import traceback
import random
import sqlite3
from datetime import datetime
from flask import * # Flask, g, redirect, render_template, request, url_for
from functools import wraps

app = Flask(__name__)
API_KEY = 'uz220NmV1MRNLR3SKQRu4d5VgJNtojDo'

# These should make it so your Flask app always returns the latest version of
# your HTML, CSS, and JS files. We would remove them from a production deploy,
# but don't change them here.
app.debug = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-cache"
    return response



def get_db():
    db = getattr(g, '_database', None)

    if db is None:
        db = g._database = sqlite3.connect('db/watchparty.sqlite3')
        db.row_factory = sqlite3.Row
        setattr(g, '_database', db)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def query_db(query, args=(), one=False):
    db = get_db()
    cursor = db.execute(query, args)
    print("query_db")
    print(cursor)
    rows = cursor.fetchall()
    print(rows)
    db.commit()
    cursor.close()
    if rows:
        if one: 
            return rows[0]
        return rows
    return None

def new_user():
    name = "Unnamed User #" + ''.join(random.choices(string.digits, k=6))
    password = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    api_key = ''.join(random.choices(string.ascii_lowercase + string.digits, k=40))
    u = query_db('insert into users (name, password, api_key) ' + 
        'values (?, ?, ?) returning id, name, password, api_key',
        (name, password, api_key),
        one=True)
    return u

def get_user_from_cookie(request):
    user_id = request.cookies.get('user_id')
    password = request.cookies.get('user_password')
    if user_id and password:
        return query_db('select * from users where id = ? and password = ?', [user_id, password], one=True)
    return None

def render_with_error_handling(template, **kwargs):
    try:
        return render_template(template, **kwargs)
    except:
        t = traceback.format_exc()
        return render_template('error.html', args={"trace": t}), 500

# ------------------------------ NORMAL PAGE ROUTES ----------------------------------

@app.route('/')
def index():
    print("index") # For debugging
    user = get_user_from_cookie(request)

    if user:
        rooms = query_db('select * from rooms')
        return render_with_error_handling('index.html', user=user, rooms=rooms)
    
    return render_with_error_handling('index.html', user=None, rooms=None)

@app.route('/rooms/new', methods=['GET', 'POST'])
def create_room():
    print("create room") # For debugging
    user = get_user_from_cookie(request)
    if user is None: return {}, 403

    if (request.method == 'POST'):
        name = "Unnamed Room " + ''.join(random.choices(string.digits, k=6))
        room = query_db('insert into rooms (name) values (?) returning id', [name], one=True)
        return redirect(f'{room["id"]}')
    else:
        return app.send_static_file('create_room.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    print("signup")
    user = get_user_from_cookie(request)

    if user:
        return redirect('/profile')
        # return render_with_error_handling('profile.html', user=user) # redirect('/')
    
    if request.method == 'POST':
        u = new_user()
        print("u")
        print(u)
        for key in u.keys():
            print(f'{key}: {u[key]}')

        resp = redirect('/profile')
        resp.set_cookie('user_id', str(u['id']))
        resp.set_cookie('user_password', u['password'])
        return resp
    
    return redirect('/login')

@app.route('/profile')
def profile():
    print("profile")
    user = get_user_from_cookie(request)
    if user:
        return render_with_error_handling('profile.html', user=user)
    
    redirect('/login')


@app.route('/login', methods=['GET', 'POST'])
def login():
    print("login")
    user = get_user_from_cookie(request)

    if user:
        return redirect('/')
    
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['name']
        u = query_db('select * from users where name = ? and password = ?', [name, password], one=True)
        if user:
            resp = make_response(redirect("/"))
            resp.set_cookie('user_id', u.id)
            resp.set_cookie('user_password', u.password)
            return resp

    return render_with_error_handling('login.html', failed=True)   

@app.route('/logout')
def logout():
    resp = make_response(redirect('/'))
    resp.set_cookie('user_id', '')
    resp.set_cookie('user_password', '')
    return resp

@app.route('/rooms/<int:room_id>')
def room(room_id):
    user = get_user_from_cookie(request)
    if user is None: return redirect('/')

    room = query_db('select * from rooms where id = ?', [room_id], one=True)
    return render_with_error_handling('room.html',
            room=room, user=user)

# -------------------------------- API ROUTES ----------------------------------
def verify_api(request):
    key = request.headers.get('x-api-key')
    if key == API_KEY:
        return True
    else:
        print('authentication failed')
        return jsonify({"error": "unauthorized API key"}), 406


# POST to change the user's name
@app.route('/api/user/name', methods=['POST'])
def update_username():
    if verify_api(request) is not True:
        return verify_api(request)
    
    print('launched change username')
    user = get_user_from_cookie(request)
    if user is None:
        return redirect('/')
    
    user_id = request.cookies.get('user_id')
    new_name = request.json.get('username')
    print(new_name)
    if not new_name:
        return jsonify({'error': 'No username provided'}), 400
    query = """
UPDATE users SET name = ? WHERE id = ?
            """
    result = query_db(query, [new_name, user_id], one=True)
    print('username updated')
    return jsonify({'success': True})
    

# POST to change the user's password
@app.route('/api/user/password', methods=['POST'])
def update_password():
    if verify_api(request) is not True:
        return verify_api(request)

    print('launched change password')
    user = get_user_from_cookie(request)
    if user is None:
        return redirect('/')
    
    user_id = request.cookies.get('user_id')
    #print(request.json)
    name = request.json.get('username')
    new_password = request.json.get('password')
    #print(new_password)
    if not new_password:
        return jsonify({'error': 'No password provided'}), 400
    query = """
UPDATE users SET password = ? WHERE id = ?
            """
    result = query_db(query, [new_password, user_id], one=True)
    resp = make_response(redirect('/profile'))
    resp.set_cookie('user_password', new_password)
    #print('password changed to', request.cookies.get('user_password'))
    return resp


# POST to change the name of a room
@app.route('/api/room/<int:room_id>', methods=['POST'])
def update_roomname(room_id):
    if verify_api(request) is not True:
        return verify_api(request)
    
    print('change room name')
    user = get_user_from_cookie(request)
    if user is None:
        return redirect('/')
    
    new_name = request.json.get('name')
    print(new_name)
    if not new_name:
        return jsonify({'error': 'No room name provided'}), 400
    
    query = """
UPDATE rooms SET name = ? WHERE id = ?
            """
    result = query_db(query, [new_name, room_id], one=True)
    print('room name updated')
    return jsonify({'success': True})


# GET to get all the messages in a room
@app.route('/api/get_messages/rooms/<int:room_id>', methods=['GET'])
def api_get_messages(room_id):
    if verify_api(request) is not True:
        return verify_api(request)
    
    messages = query_db('''
SELECT messages.id, users.name AS author, messages.body, messages.room_id
FROM messages
INNER JOIN users ON messages.user_id = users.id
WHERE messages.room_id = ?
                        ''', [room_id])
    if messages is None:
        return jsonify('No message in this room yet!')
    else:
        return jsonify([{'id': msg['id'], 'author': msg['author'], 'body': msg['body'], 'room_id': msg['room_id']} for msg in messages])


# POST to post a new message to a room
@app.route('/api/post_message/rooms/<int:room_id>', methods=['POST'])
def post_message(room_id):
    if verify_api(request) is not True:
        return verify_api(request)
    
    print('launched post', room_id)
    user = get_user_from_cookie(request)
    if user is None:
        return redirect('/')

    #print('here')
    user_id = request.cookies.get('user_id')
    #print('here')
    #print(request.json)
    message = request.json.get('comment')
    print(message)
    #print('above is message')
    
    if not message:
        return jsonify({'error': 'No message provided'}), 400
    query = """
INSERT INTO messages (user_id, room_id, body) VALUES (?, ?, ?) RETURNING user_id
            """
    result = query_db(query, [user_id, room_id, message], one=True)
    print('inserted')
    return jsonify({'success': True})


if __name__ == '__main__':
    app.run()