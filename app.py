import requests
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import InputRequired
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.secret_key = 'supersecreto'

# Configurar Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

# Simulación de base de datos de usuarios
users = {'admin': {'password': 'password123'}}

class User(UserMixin):
    def __init__(self, id):
        self.id = id

# Cargar usuario
@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# Formulario de login
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])

# URL de la API de FastAPI
API_URL = "https://api-yovy.onrender.com/news/news/posts"  # URL de la API

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        if username in users and users[username]['password'] == password:
            user = User(username)
            login_user(user)
            return redirect(url_for('create_news'))  # Redirige a la página para crear noticias
        else:
            flash('Login failed. Check your username and/or password.')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/create_news', methods=['GET', 'POST'])
@login_required
def create_news():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        user_id = 0  # O el ID del usuario autenticado, si es necesario
        image = request.files['image']  # Para subir la imagen

        # Crear noticia en la API (POST a FastAPI)
        files = {'image': image}  # Enviar imagen
        data = {
            "user_id": user_id,
            "title": title,
            "description": description
        }

        try:
            response = requests.post(f"{API_URL}", json=data, files=files)
            if response.status_code == 201:
                flash("News created successfully!", 'success')
                return redirect(url_for('view_posts'))  # Redirige a la lista de posts
            else:
                flash(f"Failed to create post: {response.text}", 'danger')
        except requests.exceptions.RequestException as e:
            flash(f"Error connecting to API: {e}", 'danger')

    return render_template('create_news.html')

@app.route('/view_posts')
@login_required
def view_posts():
    try:
        response = requests.get(API_URL)  # Consulta todas las noticias
        if response.status_code == 200:
            posts = response.json()  # Obtener las noticias
        else:
            posts = []
            flash("Failed to fetch posts from the API.", 'danger')
    except requests.exceptions.RequestException as e:
        posts = []
        flash(f"Error fetching data: {e}", 'danger')
    return render_template('view_posts.html', posts=posts)

@app.route('/edit_news/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_news(post_id):
    try:
        # Consultar la noticia que se quiere editar
        response = requests.get(f"{API_URL}/{post_id}")
        post = response.json() if response.status_code == 200 else None

        if not post:
            flash("Post not found", 'danger')
            return redirect(url_for('view_posts'))

        if request.method == 'POST':
            title = request.form['title']
            description = request.form['description']
            data = {
                "user_id": post['user_id'],
                "title": title,
                "description": description
            }

            response = requests.put(f"{API_URL}/{post_id}", json=data)
            if response.status_code == 200:
                flash("News updated successfully!", 'success')
                return redirect(url_for('view_posts'))
            else:
                flash(f"Failed to update post: {response.text}", 'danger')
        
        return render_template('edit_news.html', post=post)

    except requests.exceptions.RequestException as e:
        flash(f"Error fetching data: {e}", 'danger')
        return redirect(url_for('view_posts'))

@app.route('/delete_news/<int:post_id>', methods=['POST'])
@login_required
def delete_news(post_id):
    try:
        response = requests.delete(f"{API_URL}/{post_id}")
        if response.status_code == 200:
            flash("News deleted successfully!", 'success')
        else:
            flash(f"Failed to delete post: {response.text}", 'danger')
    except requests.exceptions.RequestException as e:
        flash(f"Error deleting post: {e}", 'danger')

    return redirect(url_for('view_posts'))

if __name__ == '__main__':
    app.run(debug=True)
