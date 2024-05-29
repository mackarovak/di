from flask import Flask, render_template, url_for, request, redirect, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask import send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin, AnonymousUserMixin
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cvartiry.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    role = db.Column(db.String(20), nullable=False)

    def __init__(self, username, password, role):
        self.username = username
        self.password = password
        self.role = role

    def get_id(self):
        return str(self.id)

    @staticmethod
    def get(username):
        user = User.query.filter_by(username=username).first()
        return user
    
    def __str__(self):
        return self.username

    def is_active(self):
        return True

class Articles(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    text = db.Column(db.Text, nullable=False)
    price = db.Column(db.Integer, nullable=False)

@app.route("/")
def index():
    return render_template('index.html', current_user=current_user)

@app.route("/about")
def about():
    return render_template('about.html')

@app.route("/profile")
@login_required
def profile():
    return render_template('profile.html', user=current_user, get_image_path=get_image_path)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route("/add_user", methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user:
            flash('Пользователь с таким именем уже существует', 'error')
            return redirect(url_for('add_user'))
        role = request.form.get('role')
        new_user = User(username=username, password=password, role=role)
        db.session.add(new_user)
        db.session.commit()
        return redirect('/')
    return render_template('add_user.html')

@app.route("/autoriz", methods=['POST', 'GET'])
def autoriz():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.get(username)
        if user and user.password == password:
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Неверное имя пользователя или пароль', 'error')
            return redirect(url_for('autoriz'))
    return render_template('autoriz.html')

def get_image_path(filename):
    image_path = os.path.join('static/images', filename)
    return image_path

@app.route("/tovars")
def tovarys():
    tovarys = Articles.query.order_by(Articles.price.desc()).all()
    return render_template('tovars.html', tovarys=tovarys, get_image_path=get_image_path)

@app.route("/patner")
def partner():
    return render_template('partner.html')

@app.route("/tovars/<string:id>")
def tovar_details(id):
    tovar = Articles.query.get(id)
    return render_template('tovar_details.html', tovar=tovar, get_image_path=get_image_path)

@app.route("/cart/<string:id>/add")
def add_to_cart(id):
    cart_items = session.get("cart", [])
    cart_items.append(id)
    session["cart"] = cart_items
    return redirect(url_for("cart"))

@app.route("/cart")
def cart():
    cart_items = session.get("cart", [])
    tovar_items = Articles.query.filter(Articles.id.in_(cart_items)).all()
    return render_template("cart.html", tovar_items=tovar_items, get_image_path=get_image_path)

@app.route("/cart/<string:id>/remove")
def remove_from_cart(id):
    cart_items = session.get("cart", [])
    if id in cart_items:
        cart_items.remove(id)
        session["cart"] = cart_items
    return redirect(url_for("cart"))

@app.route("/tovars/<string:id>/delete")
@login_required
def tovar_delete(id):
    if current_user.is_authenticated and current_user.role != "Администратор":
        return "Access denied"
    tovar = Articles.query.get_or_404(id)
    try:
        db.session.delete(tovar)
        db.session.commit()
        return redirect('/tovars')
    except:
        return "При удалении товара произошла ошибка"

@app.route("/create_article", methods=['POST', 'GET'])
@login_required
def create_article():
    if current_user.is_authenticated and current_user.role != "Администратор":
        return "Access denied"
    if request.method == "POST":
        name = request.form['name']
        text = request.form['text']
        price = request.form['price']
        article = Articles(name=name, text=text, price=price)
        if not name or not price:
            flash("Название и цена не могут быть пустыми", 'error')
            return redirect(url_for('create_article'))
        try:
            db.session.add(article)
            db.session.commit()
            return redirect('/tovars')
        except:
            return "При добавлении товара произошла ошибка"

    else:
        return render_template('create_article.html')

@app.route("/tovars/<string:id>/update", methods=['POST', 'GET'])
@login_required
def post_update(id):
    if current_user.is_authenticated and current_user.role != "Администратор":
        return "Access denied"
    tovar = Articles.query.get(id)
    if request.method == 'POST':
        tovar.name = request.form['name']
        tovar.text = request.form['text']
        tovar.price = request.form['price']

        try:
            db.session.commit()
            return redirect('/tovars')
        except:
            return "При редактировании товара произошла ошибка"

    else:
        return render_template('post_update.html', tovar=tovar)

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
