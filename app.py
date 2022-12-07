from flask import Flask, render_template, flash, redirect, session, url_for, logging, request
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators, IntegerField
from passlib.hash import sha256_crypt 


app = Flask(__name__)

# config mysql
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'ecommerce-flask'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# initialized mysql
mysql = MySQL(app)

# Items = Items()

@app.route('/')
def home():
  return render_template('home.html')

@app.route('/items')
def items():
  # create cursor
  cur = mysql.connection.cursor()

  # get articles
  result = cur.execute('SELECT * FROM items')

  items = cur.fetchall()

  if result > 0:
    return render_template('items.html', items=items)
  else:
    msg = 'No items in your shopping list'
    return render_template('items.html', msg=msg)
  
  # close connection
  cur.close()

@app.route('/item/<string:id>/')
def item(id):
   # create cursor
  cur = mysql.connection.cursor()

  # get articles
  result = cur.execute('SELECT * FROM items WHERE id = %s', [id])

  item = cur.fetchone()
  return render_template('item.html', item=item)

class RegisterForm(Form):
  email = StringField('Email', validators=[validators.Length(min=1, max=50)])
  username = StringField('Username', validators=[validators.Length(min=4, max=50)])
  password = PasswordField('Password', [
    validators.DataRequired(),
    validators.EqualTo('confirm_password', message='Passwords do not match')
  ])
  confirm_password = PasswordField('Confirm Password')

@app.route('/register', methods=['GET', 'POST'])
def register():
  form = RegisterForm(request.form)
  if request.method == 'POST' and form.validate():
    email = form.email.data
    username = form.username.data
    password = sha256_crypt.encrypt(str(form.password.data))

    # create cursor
    cur = mysql.connection.cursor()

    cur.execute("INSERT INTO users(email, username, password) VALUES(%s, %s, %s)", (email, username, password))

    # commit to db
    mysql.connection.commit()

    # close the connection
    cur.close()

    flash('Account Created!', category='success')

    return redirect(url_for('login'))
  return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
  if request.method == 'POST':
    # get form fields
    username = request.form['username']
    password_candidate = request.form['password']

    # create cursor
    cur = mysql.connection.cursor()

    # get user by username
    result = cur.execute("SELECT * FROM users WHERE username = %s", [username])

    if result > 0:
      # get stored hash
      data = cur.fetchone()
      password = data['password']

      # compare the passwords
      if sha256_crypt.verify(password_candidate, password):
        # passed
        session['logged_in'] = True
        session['username'] = username

        flash('You are now logged in', category='success')
        return redirect(url_for('dashboard'))
      else:
        error = 'Invalid Login'
        return render_template('login.html',error=error)
      # close connection
      cur.close()
    else:
      error = 'Username not found'
      return render_template('login.html', error=error)
    return render_template('login.html', error=error)
  return render_template('login.html')
  

@app.route('/logout')
def logout():
  session.clear()
  flash('You are now logged out', category='success')
  return redirect(url_for('login'))

  
# Dashboard
@app.route('/dashboard')
def dashboard():
  # create cursor
  cur = mysql.connection.cursor()

  # get articles
  result = cur.execute('SELECT * FROM items')

  items = cur.fetchall()

  if result > 0:
    return render_template('dashboard.html', items=items)
  else:
    msg = 'No items in your shopping list'
    return render_template('dashboard.html', msg=msg)
  
  # close connection
  cur.close()

# Item form class
class ItemForm(Form):
  type = StringField('Item Type:', validators=[validators.Length(min=1, max=50)])
  name = StringField('Item Name:', validators=[validators.Length(min=1, max=50)])
  brand = StringField('Brand:', validators=[validators.Length(min=1, max=50)])
  specs = StringField('Specs:', validators=[validators.Length(min=1, max=50)])
  seller = StringField('Seller:', validators=[validators.Length(min=1, max=50)])
  price = IntegerField('Price')

total = 0

@app.route('/add_item', methods=['GET', 'POST'])
def add_item():
  form = ItemForm(request.form)
  if request.method == 'POST' and form.validate():
    type = form.type.data
    name = form.name.data
    brand = form.brand.data
    specs = form.specs.data
    seller = form.seller.data
    price = form.price.data

    total += price
    # create cursor
    cur = mysql.connection.cursor()

    # execute
    cur.execute("INSERT INTO items(type, name, brand, specs, seller, price) VALUES (%s, %s, %s, %s, %s, %s)", (type, name, brand, specs, seller, price))

    # commit to db
    mysql.connection.commit()

    # close connection
    cur.close()
  
    flash('Item Added to Shopping List', category='success')

    return redirect(url_for('dashboard'))
  return render_template('add_item.html', form=form)


@app.route('/edit_item/<string:id>/', methods=['GET', 'POST'])
def edit_item(id):
  # create cursor
  cur = mysql.connection.cursor()
  # get item by id
  result = cur.execute("SELECT * FROM items WHERE id = %s", [id])
  item = cur.fetchone()
  # get form
  form = ItemForm(request.form)
  # populate item fields
  form.type.data = item['type']
  form.name.data = item['name']
  form.brand.data = item['brand']
  form.specs.data = item['specs']
  form.seller.data = item['seller']
  form.price.data = item['price']

  if request.method == 'POST' and form.validate():
    type = request.form['type']
    name = request.form['name']
    brand = request.form['brand']
    specs = request.form['specs']
    seller = request.form['seller']
    seller = request.form['price']

    # create cursor
    cur = mysql.connection.cursor()
    # execute
    cur.execute("UPDATE items SET type = %s, name = %s, brand = %s, specs = %s, seller = %s, price = %s WHERE id = %s", (type, name, brand, specs, seller, price, id))
    # commit to db
    mysql.connection.commit()
    # close connection
    cur.close()
    flash('Item Edited', category='success')

    return redirect(url_for('dashboard'))
  return render_template('edit_item.html', form=form)
  
# delete item
@app.route('/delete_item/<string:id>', methods=['POST'])
def delete_item(id):
  cur = mysql.connection.cursor()
  cur.execute('DELETE FROM items WHERE id = %s', [id])
  mysql.connection.commit()
  cur.close()
  flash('Item Deleted', category='success')
  return redirect(url_for('dashboard')) 
  

@app.route('/cart')
def cart():
  return render_template('cart.html')
  
  
@app.route('/checkout')
def checkout():
  return render_template('checkout.html')

  
if __name__ == '__main__':
  app.secret_key = '123123'
  app.run(debug=True)