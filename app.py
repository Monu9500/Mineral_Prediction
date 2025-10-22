from flask import Flask, render_template, request, redirect, url_for, session, g, send_from_directory, jsonify
import sqlite3
import os
from flask import logging
import csv
import xml.etree.ElementTree as ET
from flask import session, redirect, url_for, request, abort
from utils import access_control_required  #  assuming you created the decorator in utils.py
from urllib.parse import urlparse



app = Flask(__name__)
app.secret_key = 'your_secret_key'

#----------------------xml----------------------------
DATABASE = os.path.join(os.getcwd(), 'database', 'user.db')
CSV_FILE = os.path.join('static', 'map_page', 'rock_info1.csv')
rock_data = []  # global cache

def is_page_allowed(user_level, requested_path):
    tree = ET.parse('user_access.xml')
    root = tree.getroot()
    
    for level in root.findall('Level'):
        if level.get('id') == str(user_level):
            pages = [page.text for page in level.findall('Page')]
            return requested_path in pages
    return False


from functools import wraps


def access_control_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_level = session.get('level')
        requested_path = request.path
        base_path = '/' + requested_path.strip('/').split('/')[0]  # Just the base like "/rock"

        print(f"🔒 Access check: level={user_level}, full_path={requested_path}, base_path={base_path}")

        if not user_level:
            return redirect(url_for('login'))

        if not is_page_allowed(user_level, base_path):
            print("❌ Access denied by XML for this route")
            return "❌ Access Denied", 403

        return f(*args, **kwargs)
    return decorated_function








# ------------------ Load CSV ------------------
def load_and_fix_csv():
    global rock_data
    rock_data = []

    if not os.path.exists(CSV_FILE):
        print(f"❌ CSV file not found: {CSV_FILE}")
        return

    print(f"📂 Loading CSV file from: {CSV_FILE}")
    with open(CSV_FILE, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        headers = [h.strip().lower() for h in reader.fieldnames]
        print("🧾 Original headers:", reader.fieldnames)
        print("✅ Normalized headers:", headers)

        for row_num, row in enumerate(reader, start=1):
            try:
                fixed = {k.strip().lower(): v.strip() for k, v in row.items()}
                lat = float(fixed.get('latitude', '0'))
                lon = float(fixed.get('longitude', '0'))
                rock = fixed.get('rocks') or ''
                place = fixed.get('place') or ''
                rid = fixed.get('id') or str(row_num)

                if not rock or lat == 0 or lon == 0:
                    print(f"⚠️ Skipping row {row_num}: missing data")
                    continue

                record = {
                    "Id": rid,
                    "Place": place,
                    "Rocks": rock,
                    "Latitude": lat,
                    "Longitude": lon
                }
                rock_data.append(record)
            except Exception as e:
                print(f"❌ Error parsing row {row_num}: {e}")

    print(f"✅ Loaded {len(rock_data)} rocks.")

# ------------------ DB connection ------------------
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# ------------------ Routes ------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if not session.get('access_granted'):
        return redirect(url_for('access_password'))
    
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        cur = get_db().execute('SELECT * FROM users WHERE email = ? AND password = ?', (email, password))
        user = cur.fetchone()
        if user:
            session['user'] = dict(user)
            session['level'] = user['level']  # ← Make sure this is set!
            print("✅ Logged in user level:", session.get('level'))  # ← Add this line
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Invalid email or password')
    return render_template('login.html')



#----------------------dashboard-----------------------
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    user = session['user']
    return render_template('dashboard.html', user=user, level=user['level'])



#------------------------map------------------------------
@app.route('/map')
@access_control_required
def map_page():
    if 'user' not in session:
        return redirect(url_for('login'))
    # serve map HTML
    return render_template('map.html')
@app.route('/api/rocks')
def api_rocks():
    return jsonify(rock_data)


#---------------insert rock---------------------------------
@app.route('/insert_rock', methods=['GET', 'POST'])
@access_control_required
def insert_rock():
    if 'user' not in session:
        return redirect(url_for('login'))
    user = session['user']
    if user['level'] not in [1, 2]:
        return "Access denied", 403
    if request.method == 'POST':
        rock_id = request.form['rock_id']
        rock_name = request.form['rock_name']
        parent_id = request.form['parent_id']
        db = get_db()
        db.execute('INSERT INTO rocks (rock_id, rock_name, parent_id) VALUES (?, ?, ?)',
                   (rock_id, rock_name, parent_id))
        db.commit()
        return redirect(url_for('dashboard'))
    return render_template('insert_rock.html')


#-------------insert location--------------------------------
@app.route('/insert_location', methods=['GET', 'POST'])
def insert_location():
    if 'user' not in session:
        return redirect(url_for('login'))
    user = session['user']
    if user['level'] not in [1, 2]:
        return "Access denied", 403
    if request.method == 'POST':
        id = request.form.get('id')
        place = request.form['place']
        latitude = request.form['latitude']
        longitude = request.form['longitude']
        db = get_db()
        db.execute('INSERT INTO locations (id, place, latitude, longitude) VALUES (?, ?, ?, ?)',
                   (id, place, latitude, longitude))
        db.commit()
        return redirect(url_for('dashboard'))
    return render_template('insert_location.html')

#------------------------------create user-----------------------
@app.route('/create_user', methods=['GET', 'POST'])
@access_control_required
def create_user():
    if 'user' not in session:
        return redirect(url_for('login'))
    user = session['user']
    if user['level'] != 1:
        return "Access denied", 403
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        password = request.form['password']
        level = int(request.form['level'])
        db = get_db()
        db.execute('INSERT INTO users (first_name, last_name, email, password, level) VALUES (?, ?, ?, ?, ?)',
                   (first_name, last_name, email, password, level))
        db.commit()
        return redirect(url_for('dashboard'))
    return render_template('create_user.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/rock/<rock_id>')
#@access_control_required
def rock_detail(rock_id):
    # Find rock in rock_data by id
    rock = next((r for r in rock_data if r['Id'] == rock_id), None)
    if not rock:
        return "Rock not found", 404
    return render_template('rock_detail.html', rock=rock)

@app.route('/update_rock/<int:rock_id>', methods=['GET', 'POST'])
@access_control_required
def update_rock(rock_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    user = session['user']

    # Find rock data
    rock = next((r for r in rock_data if int(r['Id']) == rock_id), None)
    if not rock:
        return "Rock not found", 404

    if request.method == 'POST':
        # Update the rock name etc. from form
        rock['Rocks'] = request.form['rocks']
        # Optional: update other fields like subtype, parent_id if you have them
        return redirect(url_for('rock_detail', rock_id=rock_id))

    return render_template('update_rock.html', rock=rock)


@app.route('/update_location/<int:rock_id>', methods=['GET', 'POST'])
@access_control_required
def update_location(rock_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    user = session['user']

    rock = next((r for r in rock_data if int(r['Id']) == rock_id), None)
    if not rock:
        return "Rock not found", 404

    if request.method == 'POST':
        rock['Place'] = request.form['place']
        rock['Latitude'] = request.form['latitude']
        rock['Longitude'] = request.form['longitude']
        return redirect(url_for('rock_detail', rock_id=rock_id))

    return render_template('update_location.html', rock=rock)


#-------------forgot password---------------------------------
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        new_password = request.form['new_password']

        db = get_db()
        cur = db.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cur.fetchone()
        if user:
            db.execute('UPDATE users SET password = ? WHERE email = ?', (new_password, email))
            db.commit()
            return render_template('forgot_password.html', message='Password updated successfully.')
        else:
            return render_template('forgot_password.html', error='Email not found.')
    return render_template('forgot_password.html')


# Initial access password route
@app.route('/', methods=['GET', 'POST'])
def access_password():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == '123':
            session['access_granted'] = True
            return redirect(url_for('login'))
        else:
            return render_template('access_password.html', error='Wrong password')
    return render_template('access_password.html')



# ------------------ Start ------------------
if __name__ == '__main__':
    load_and_fix_csv()
    print("🚀 Flask app running on http://127.0.0.1:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)