from flask import Flask, render_template, request, url_for, redirect, flash, g, session
from flask import Flask, jsonify
from flask.helpers import send_file
from io import BytesIO
import psycopg2

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
                session['user'] = i[0]
                return 'hello owner'
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
                return redirect(url_for('user_home'))
        else:
            flash("Invalid Email or Password", 'invalidUser')

        conn.close()
    return redirect(url_for('index'))

@app.route('/user_logout')
def user_logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/user_home')
def user_home():
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
    return redirect(url_for('index'))

@app.route('/user_profile<int:id>')
def user_profile(id):
    if g.user:
        conn = psycopg2.connect(database)
        c = conn.cursor()

        c.execute("SELECT * FROM users WHERE id = '"+str(id)+"'")
        rs = c.fetchone()
        certificate = rs[4]
        conn.close()

        return send_file(BytesIO(certificate), attachment_filename='flask.png', as_attachment=False)

@app.route('/recommend')
def recommend():
    return render_template('recommend.html')


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