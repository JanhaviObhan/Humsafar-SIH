from flask import Flask, render_template, request, url_for, redirect, flash, g, session
from flask import Flask, jsonify
from flask.helpers import send_file
from io import BytesIO
import psycopg2
import heapq

app = Flask(__name__)
app.secret_key = 'ritesh'

database = 'postgres://gjscfkpgyogvvp:76996cc99db43b0479e8c5ecf0181da2d41561c9f50efbd6622d97ace7259df8@ec2-3-216-221-31.compute-1.amazonaws.com:5432/df095rdjmq8tsv'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['username']
        email = request.form['email']
        password = request.form['password']
        profile = request.files['profile']
        role = request.form['role']

        conn = psycopg2.connect(database)
        c = conn.cursor()

        c.execute("SELECT email FROM users")
        rs = c.fetchall()
        for rs in rs:
            if email in rs:
                flash("Email already associated with an account", 'validemail')
                break
        else:
            c.execute("""
            INSERT INTO users (name, email, password, role, profile) VALUES (%s, %s, %s, %s, %s)""", (name, email, password, role, profile.read()))
            conn.commit()
            flash(
                "Registration successfull ! You can now log in to your account ", 'register')
        conn.close

        return redirect(url_for('index'))

    return redirect(url_for('index'))

@app.route('/owner_login', methods=['GET', 'POST'])
def owner_login():
    if request.method == 'POST':
        session.pop('owner', None)

        email = request.form['email']
        password = request.form['password']

        conn = psycopg2.connect(database)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE role = 'owner' AND email = '" +
                  email+"' AND password = '"+password+"'")
        r = c.fetchall()

        for i in r:
            if (email == i[2] and password == i[3]):
                session['owner'] = i[0]
                return redirect(url_for('home'))
        else:
            flash("Invalid Email or Password", 'invalidOwner')

        conn.close()
    return redirect(url_for('index'))

@app.route('/owner_logout')
def owner_logout():
    session.pop('owner', None)
    return redirect(url_for('index'))

@app.route('/user_login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        session.pop('user', None)

        email = request.form['email']
        password = request.form['password']

        conn = psycopg2.connect(database)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE role = 'user' AND email = '" +
                  email+"' AND password = '"+password+"'")
        r = c.fetchall()

        for i in r:
            if (email == i[2] and password == i[3]):
                session['user'] = i[0]
                return redirect(url_for('home'))
        else:
            flash("Invalid Email or Password", 'invalidUser')

        conn.close()
    return redirect(url_for('index'))

@app.route('/user_logout')
def user_logout():
    session.pop('user', None)
    return redirect(url_for('index'))


# ------------- HOME PAGE
@app.route('/home')
def home():
    if g.user:
        conn = psycopg2.connect(database)
        c = conn.cursor()

        c.execute("SELECT * FROM users WHERE id = '"+str(session['user'])+"'")
        rs = c.fetchone()

        conn.close()

        context = {
            'rs': rs
        }
        return render_template('user_home.html', **context)
    elif g.owner:
        conn = psycopg2.connect(database)
        c = conn.cursor()

        c.execute("SELECT * FROM users WHERE id = '"+str(session['owner'])+"'")
        rs = c.fetchone()

        conn.close()

        context = {
            'rs': rs
        }
        return render_template('owner_home.html', **context)
    return redirect(url_for('index'))

# ------------- RECOMMENDATION
@app.route('/recommendation', methods=['GET', 'POST'])
def recommendation():
    if request.method == 'POST':
        conn = psycopg2.connect(database)
        c = conn.cursor()

        facilities = ''
        city = request.form['city']
        state = request.form['state']
        place = request.form['place']
        value = request.form.getlist('check')

        c.execute("""SELECT * FROM places WHERE venue = %s AND state = %s AND city = %s""", (place, state, city))
        placesss = c.fetchall()
        scores = list()
        for rs in placesss:
            text = rs[9]
            li = list(text.split(" "))
            res = len(set(value) & set(li)) / float(len(set(value) | set(li))) * 100
            scores.append(res)
        
        recom = heapq.nlargest(3, range(len(scores)), key=scores.__getitem__)
        percent = heapq.nlargest(3, scores)

        recomend = list()
        for i in recom:
            recomend.append(placesss[i][0])
        
        c.execute("SELECT * FROM places WHERE id = '"+str(recomend[0])+"'")
        place1 = c.fetchone()
        c.execute("SELECT * FROM places WHERE id = '"+str(recomend[1])+"'")
        place2 = c.fetchone()
        c.execute("SELECT * FROM places WHERE id = '"+str(recomend[2])+"'")
        place3 = c.fetchone()

        c.execute("SELECT * FROM reviews WHERE place = '"+str(recomend[0])+"'")
        review1 = c.fetchall()
        c.execute("SELECT * FROM reviews WHERE place = '"+str(recomend[1])+"'")
        review2 = c.fetchall()
        c.execute("SELECT * FROM reviews WHERE place = '"+str(recomend[2])+"'")
        review3 = c.fetchall()
    
        context = {
            'percent': percent,
            'place1': place1,
            'review1': review1,
            'place2': place2,
            'review2': review2,
            'place3': place3,
            'review3': review3,
        }
        if g.user:
            return render_template('user_recommendation.html', **context)
        elif g.owner:
            return render_template('owner_recommendation.html', **context)
    return redirect(url_for('index'))


@app.route('/owner_place')
def owner_place():
    if g.owner:
        return render_template('owner_place.html')
    return redirect(url_for('index'))

@app.route('/owner_new_place')
def owner_new_place():
    if g.owner:
        return render_template('owner_new_place.html')
    return redirect(url_for('index'))


# ------------- PROFILE PICTURES
@app.route('/profile<int:id>')
def profile(id):
    conn = psycopg2.connect(database)
    c = conn.cursor()

    c.execute("SELECT * FROM users WHERE id = '"+str(id)+"'")
    rs = c.fetchone()
    picture = rs[4]
    conn.close()

    return send_file(BytesIO(picture), attachment_filename='flask.png', as_attachment=False)

@app.route('/place_profile<int:id>')
def place_profile(id):
    conn = psycopg2.connect(database)
    c = conn.cursor()

    c.execute("SELECT * FROM places WHERE id = '"+str(id)+"'")
    rs = c.fetchone()
    picture = rs[2]

    return send_file(BytesIO(picture), attachment_filename='flask.png', as_attachment=False)



@app.before_request
def before_request():
    g.user = None
    g.owner = None
    if 'user' in session:
        g.user = session['user']
    if 'owner' in session:
        g.owner = session['owner']

if __name__ == "__main__":
    app.run(debug=True)