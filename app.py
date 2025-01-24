from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Flask application setup
app = Flask(__name__)
app.secret_key = "supersecretkey"  # Required for session management


# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# User Database setup
def init_db():
    print("Initializing database...")
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()
    print("Database initialized!")

# Database Model
class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Initialize the database (creates tables)
with app.app_context():
    db.create_all()

# Home Page: Display All Blog Posts
@app.route('/')
def home():
    posts = BlogPost.query.order_by(BlogPost.created_at.desc()).all()
    return render_template('home.html', posts=posts)


# View Single Post
@app.route('/post/<int:post_id>')
def post(post_id):
    post = BlogPost.query.get_or_404(post_id)
    return render_template('post.html', post=post)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash('Email and password are required!', 'danger')
            return redirect(url_for('register'))

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()[0]

        is_admin = 1 if user_count == 0 else 0

        try:
            cursor.execute('INSERT INTO users (email, password, is_admin) VALUES (?, ?, ?)', (email, password, is_admin))
            conn.commit()
            flash('Registration successful!', 'success')
            if is_admin:
                return redirect(url_for('login'))
            else:
                return redirect(url_for('home'))
        except sqlite3.IntegrityError:
            flash('Username already exists!', 'danger')
        except Exception as e:
            flash(f'An error occurred: {e}', 'danger')
        finally:
            conn.close()

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, is_admin FROM users WHERE email = ? AND password = ?', (email, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session['user_id'] = user[0]
            session['email'] = email
            session['admin'] = user[1] == 1
            print(f"Logged in user: {email}, Admin: {session['admin']}")
            flash('Logged in successfully!', 'success')
            if session['admin']:
                return redirect(url_for('dashboard'))
            else:
                return redirect(url_for('home'))
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('login.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if not session.get('admin'):
        flash('You must be logged in as an admin to access the dashboard.', 'danger')
        return redirect(url_for('home'))

    posts = BlogPost.query.order_by(BlogPost.created_at.desc()).all()
    return render_template('dashboard.html', posts=posts)

@app.route('/logout')
def logout():
    # Clear session data to log out the user
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('admin', None)
    
    # Flash message to notify the user of logout
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))
# Create Post route
@app.route('/create', methods=['GET', 'POST'])
def create():
    if not session.get('admin'):
        flash('You must be logged in as an admin to create posts.', 'danger')
        return redirect(url_for('login'))
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        new_post = BlogPost(title=title, content=content)
        db.session.add(new_post)
        db.session.commit()
        flash('Post created successfully!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('create_post.html')

# Edit Post
@app.route('/edit/<int:post_id>', methods=['GET', 'POST'])
def edit(post_id):
    if not session.get('admin'):
        flash('You must be logged in as an admin to edit posts.', 'danger')
        return redirect(url_for('login'))
    post = BlogPost.query.get(post_id)
    if request.method == 'POST':
        post.title = request.form.get('title')
        post.content = request.form.get('content')
        db.session.commit()
        flash('Post updated successfully!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('edit_post.html', post=post)

# Delete Post route
@app.route('/delete/<int:post_id>')
def delete(post_id):
    if not session.get('admin'):
        flash('You must be logged in as an admin to delete posts.', 'danger')
        return redirect(url_for('login'))
    post = BlogPost.query.get(post_id)
    db.session.delete(post)
    db.session.commit()
    flash('Post deleted successfully!', 'success')
    return redirect(url_for('dashboard'))

# Run the Application
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
