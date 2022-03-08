from flask import Flask, render_template, request, url_for, redirect, flash, g, session
from flask import Flask, jsonify
from flask.helpers import send_file
from io import BytesIO

app = Flask(__name__)
app.secret_key = 'ritesh'

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        return redirect(url_for('home'))
    return render_template('index.html')

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/recommend')
def recommend():
    return render_template('recommend.html')

if __name__ == "__main__":
    app.run(debug=True)