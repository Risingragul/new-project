from flask import Flask, render_template, request, redirect, url_for, session,flash
from flask_pymongo import PyMongo 
import pymongo
import re 
import os
from flask_mail import Mail, Message
import secrets
from dotenv import load_dotenv
# Load environment variables from .env
load_dotenv()
import hashlib
app = Flask(__name__)
app.secret_key = 'your_secret_key'



collection = pymongo.MongoClient(os.getenv('uri')).accounts.accounts
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Use Gmail's SMTP server
app.config['MAIL_PORT'] = 587  # The port used by Gmail is 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = os.getenv('username')  # Your Gmail email address
app.config['MAIL_PASSWORD'] = os.getenv('password')  # Your Gmail password
mail = Mail(app)


def generate_reset_token():
    return secrets.token_urlsafe(24)

@app.route('/password_reset', methods=['GET', 'POST'])
def password_reset():
    if request.method == 'POST':
        email = request.form.get('email')  # Get the user's email from the form

        # Generate a temporary password
        temporary_password = secrets.token_urlsafe(12)  # Adjust the length as needed
        account = collection.find_one({'email': email})
        if account:
            msg = Message('Password Reset', sender='support@gmail.com', recipients=[email])
            msg.body = f'Your temporary password is: {temporary_password}'
            mail.send(msg)
            collection.update_one({'email': email}, {'$set': {'password': temporary_password}})
            flash('Temporary password sent to your email. Check your inbox and use it.')
        else:
            flash('Email not found. Please enter a valid email address.')

        return render_template('password_reset_confirmation.html')

    return render_template('reset.html')



@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password']
        account = collection.find_one({'email': email, 'password': password})
        if account:
            session['loggedin'] = True
            session['id'] = str(account['_id'])
            session['username'] = account['username']
            msg = 'Logged in successfully!'
            return render_template('index.html', msg=msg)
        else:
            msg = 'Incorrect username / password!'
    return render_template('login.html', msg=msg)

@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('login'))



@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        username = request.form['username']
        session['user']=username
        password = request.form['password']
        email = request.form['email']
        account = collection.find_one({'email': email})
        print(account)
        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            collection.insert_one({'username': username, 'password': password, 'email': email})
            msg = 'You have successfully registered!'
    elif request.method == 'POST':
        msg = 'Please fill out the form!'
    return render_template('index.html', msg=msg)
    

if __name__ == '__main__':
    app.run(debug=True)
