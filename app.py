from flask import Flask, render_template, request, redirect, url_for, flash, jsonify,session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import extract,or_
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import os
import json
from flask_cors import CORS
from datetime import datetime,timedelta
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = os.getenv("UPLOAD_FOLDER")
app.config["SQLALCHEMY_DATABASE_URI"] =os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
#db = SQLAlchemy(app)
#app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///site.db')
app.secret_key = os.getenv('SECRET_KEY')  # Use environment variable
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100),unique=True,nullable=False)
    password = db.Column(db.String(10000), nullable=False)  # Increased length for hashed passwords
    address = db.Column(db.String(1000), nullable=True)
    date =db.Column(db.DateTime, default=(datetime.now()).date())

class Guest(db.Model):
    guest_id = db.Column(db.String(100), primary_key=True)

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username=db.Column(db.String(100),unique=True,nullable=False)
    password = db.Column(db.String(10000), nullable=False)
    img = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(14), nullable=True)
    email= db.Column(db.String(100), nullable=True)

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    itemid = db.Column(db.String(1000), nullable=False)
    userid = db.Column(db.String(100), nullable=False)


class Items(db.Model):
    __tablename__ = "items"
    id = db.Column(db.Integer, primary_key=True)
    img = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    type=db.Column(db.Integer,nullable=False)
    details = db.Column(db.String(1000), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    def to_dict(self):
        return {
            "id": self.id,
            "img": self.img,
            "name": self.name,
            "type":self.type,
            "details": self.details,
            "price": self.price
        }



class Order(db.Model):
    id = db.Column(db.String(100), primary_key=True)
    orderimage = db.Column(db.String(1000), nullable=False)
    orderlist = db.Column(db.String(1000), nullable=False)
    total = db.Column(db.Integer, nullable=False)
    userid = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(1000), nullable=False)
    date =db.Column(db.DateTime, default=db.func.current_timestamp())
    conform=db.Column(db.Boolean , default=True)
    packed=db.Column(db.Boolean , default=False)
    dispached=db.Column(db.Boolean , default=False)
    outfordeliver=db.Column(db.Boolean , default=False)
    deliver=db.Column(db.Boolean , default=False)


@app.route("/")
def home():
    if(session.get("Admin")):
       return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route("/logout")
def logout():
    session.clear()
    return render_template('login.html')

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(name=username).first()
        if user and check_password_hash(user.password, password):
            flash('Login successful!', 'success')
            return jsonify({"username": username, "id": user.id}), 200
        else:
            flash('Login failed. Please check your credentials.', 'danger')
            return jsonify({"message": "Invalid credentials"})
    return jsonify({"message": "Method not allowed"}), 405
@app.route("/admin", methods=['GET', 'POST'])
def admin():
    username = request.form.get('admin')
    print("admin", username)
    password = request.form.get('password')
    admin1= Admin.query.filter_by(username=username).first()
    if admin1 and check_password_hash(admin1.password, password):
        flash('Admin account already!', 'warning')
        session['Admin'] = username
        return redirect(url_for("dashboard"))
    flash('invalid details', 'warning')
    return render_template("login.html")
@app.route("/guest", methods=['GET', 'POST'])
def guest():
    if request.method == 'POST':
        numberofguests = Guest.query.count()
        new=numberofguests + 1
        guest_id = f"guest{new}"
        guest = Guest( guest_id=guest_id)
        db.session.add(guest)
        db.session.commit()
        return jsonify({"guest_id": guest_id}), 201
@app.route("/delete_product/<int:id>", methods=['DELETE'])
def delete_product(id):
    item = Items.query.get(id)
    if item:
        db.session.delete(item)
        db.session.commit()
        flash('Item deleted successfully!', 'success')
        return jsonify({"message": "Item deleted successfully"}), 200
    return jsonify({"message": "Item not found"}), 404 
    


@app.route("/add_user", methods=['POST'])
def add_user():
    data = request.get_json()
    username = data.get('username')
    password1 = data.get('password')
    guest_id = data.get('guest_id')
    print(guest_id)
    address = data.get('address')
    print(address)
    usernameexist=User.query.filter_by(name=username).first()
    if(usernameexist):
        return jsonify({"message": "Username already exists"}), 400
    hashed_password = generate_password_hash(password1)
    if address:
        address_json = json.dumps(address)
        new_user = User(name=username, password=hashed_password, address=address_json)
    else:
        new_user = User(name=username, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    print("adter first comit")
    old=User.query.filter_by(name=username).first()
    new_cart= Cart(userid=old.id, itemid=json.dumps([]))
    db.session.add(new_cart)
    db.session.commit()
    print("sssssssssssssssss")
    if(guest_id):
        user= User.query.filter_by(name=username).first()
        print("fffffffffffffffffffffffffffffffff")
        guestorders= Order.query.filter_by(userid=guest_id).all()
        print(guestorders)
        if guestorders:
            print("ggggggggggg")
            for order in guestorders:
                print("id change")
                order.userid = user.id
                db.session.add(order)
                db.session.commit()
        return jsonify({"message": "User  added successfully"}), 201
    return jsonify({"message": "User  added successfully"}), 201

@app.route("/add_admin", methods=['POST'])
def add_admin():
    print("admin")
    data = request.get_json()
    
    # Validate incoming data
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({"message": "Username and password are required", "type": "error"}), 400
    
    # Check if the username already exists
    existing_admin = Admin.query.filter_by(username=username).first()
    if existing_admin:
        return jsonify({"message": "Admin username already exists", "type": "error"}), 400
    
    # Create a new admin
    new_admin = Admin(username=username, password=generate_password_hash(password))
    db.session.add(new_admin)
    db.session.commit()
    return jsonify({"message": "Admin added successfully", "type": "success"}), 201

@app.route('/addadmin')
def addadmin():
    admins=session["Admin"]
    admin=Admin.query.filter_by(username=admins).first()
    return render_template('addadmin.html',admin=admin)
@app.route("/add_order", methods=['POST'])
def add_order():
    data = request.get_json()
    try:
        orderimage = data.get('orderimage')
        orderlist = data.get('orderlist')
        total = data.get('total')
        userid = data.get('userid')
        address = data.get('address')
        numberofguests = Order.query.filter_by(userid=userid).count()
        order_id = f"order{userid}{numberofguests + 1}"
        new_order = Order(id=order_id, orderimage=orderimage, orderlist=orderlist, total=total, userid=userid, address=address)
        db.session.add(new_order)
        db.session.commit()
        
        return jsonify({"message": "Order added successfully", "id": order_id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error adding order", "error": str(e)}), 500

@app.route("/get_order/<string:id>", methods=['GET'])
def get_order(id):
    orders = Order.query.filter_by(userid=id,deliver=False).all()
    orders_list = []
    for order in orders:
        date=order.date
        print(date)
        print(order.conform)
        orders_list.append({
            "id": order.id,
            "orderimage": order.orderimage,
            "orderlist": order.orderlist,
            "total": order.total,
            "userid": order.userid,
            "address": order.address,
            "date":order.date,
            "conform":order.conform,
            "packed":order.packed,
            "dispached":order.dispached,
            "outfordeliver":order.outfordeliver,
            "deliver":order.deliver
            })
    print("order", orders_list)
        
    return jsonify({"orders":orders_list }), 200

@app.route("/get_order_history/<string:id>", methods=['GET'])
def get_order_history(id):
    orders = Order.query.filter_by(userid=id,deliver=True).all()
    orders_list = []
    for order in orders:
        orders_list.append({
            "id": order.id,
            "orderimage": order.orderimage,
            "orderlist": order.orderlist,
            "total": order.total,
            "userid": order.userid,
            "address": order.address,
            "date":order.date,
            "conform":order.conform,
            "packed":order.packed,
            "dispached":order.dispached,
            "outfordeliver":order.outfordeliver,
            "deliver":order.deliver
            })
    print("order", orders_list)
        
    return jsonify({"orders":orders_list }), 200

@app.route("/get_cartItem/<string:userid>")
def get_cartItem(userid):
    cart = Cart.query.filter_by(userid=userid).first()
    return jsonify({"message": "Item get from cart", "cartitem": cart.itemid})


@app.route("/add_cartItem/<int:itemid>/<string:userid>", methods=['POST', 'GET'])
def add_cart_item(itemid, userid):
    if request.method == 'POST':
        try:
            cart_item = Cart.query.filter_by(userid=userid).first()
        
            if cart_item:
                item_list = json.loads(cart_item.itemid) if cart_item.itemid else []
                if itemid not in item_list:
                    item_list.append(itemid)
                cart_item.itemid = json.dumps(item_list)
                db.session.commit()
                return jsonify({"message": "Item added to cart", "cartitem": cart_item.itemid}), 200
            else:
                new_cart_item = Cart(userid=userid, itemid=json.dumps([itemid]))
                db.session.add(new_cart_item)
                db.session.commit()
                return jsonify({"message": "New cart created and item added", "cartitem": new_cart_item.itemid}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({"message": "An error occurred", "error": str(e)}), 500
    if request.method == 'GET':
        print("GET request received for cart item")
        cart_item = Cart.query.filter_by(userid=userid).first()
        if cart_item:
            item_list = json.loads(cart_item.itemid) 
            print("Current cart items:", item_list)
            if itemid  in item_list:
                item_list.remove(itemid)
                print("Item removed from cart:", itemid,item_list)
                cart_item.itemid = json.dumps(item_list)
                db.session.commit()
                return jsonify({"message": "Item removed from cart", "cartitem": cart_item.itemid}), 200
                
            

@app.route("/add_item", methods=['POST'])
def add_item():
    if request.method == 'POST':
        img = request.files['image']

        img_filename = secure_filename(img.filename)
        print(img_filename)
        imgg=app.config['UPLOAD_FOLDER']+"/"+img_filename
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
        img.save(os.path.join(app.config['UPLOAD_FOLDER'], img_filename))
        name = request.form.get('name')
        details = request.form.get('description')
        price = request.form.get('price')
        type1=request.form.get('type')
        new_item = Items(img=imgg, name=name,type=type1,details=details, price=price)
        db.session.add(new_item)
        db.session.commit()
        flash('Item added successfully!', 'success')
        return redirect(url_for('product'))


@app.route("/get_items", methods=['GET'])
def get_items():
    items = Items.query.all()
    return jsonify([item.to_dict() for item in items]), 200



@app.route('/add_product')
def add_product():
    admins=session["Admin"]
    admin=Admin.query.filter_by(username=admins).first()
    return render_template("base.html",admin=admin)


from flask import Flask, render_template, url_for
import os

@app.route('/open_profile/<string:admin>')
def open_profile(admin):
    print(f"Admin username: {admin}")
    # Query the admin from the database
    admins = Admin.query.filter_by(username=admin).first()    
    if admins:
        print(f"Admin found: {admins}")
        print(f"Username: {admins.username}, ID: {admins.id}")
        
        img_path = admins.img  # Get the image path from the admin record
        
        # Check if img_path is None or empty
        if img_path:
            full_path = os.path.join(os.getcwd(), img_path)  
            print("Full image path:", full_path)
            
            # Check if the image file exists
            if os.path.exists(full_path):
                print("Image exists")
            else:
                print("Image does not exist")
                img_path = None  # Set img_path to None if the file does not exist
        else:
            print("Image path is None or empty")
        
        # If img_path is still None, you can set a default image or handle it
        if img_path:
            result = '/'.join(img_path.split('/')[1:])  # Adjust path if necessary
            img_url = url_for('static', filename=result) 
            print("Image URL:", img_url)
        else:
            img_url = url_for('static', filename='default_image.png')  
        return render_template("open_profile.html", admin=admin, id=admins.id, email=admins.email, phone=admins.phone, img=img_url)
    else:
        return "Admin not found", 404



@app.route('/edit_admin', methods=['POST'])
def edit_admin():
    print("runing")
    id=request.form.get('id')
    print(id)
    admin=Admin.query.get(id)
    print(admin)
    name=request.form.get('name')
    print(name)
    email=request.form.get('email')
    if email:
        print(email)
        admin.email=email
    phone=request.form.get('phone')
    if phone:
        print(phone)
        admin.phone=phone
    img = request.files['image']
    if img:
        print(img)
        img_filename = secure_filename(img.filename)
        print(img_filename)
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
        img.save(os.path.join(app.config['UPLOAD_FOLDER'], img_filename))
        newpath=admin.img
        if admin.img and os.path.exists(admin.img):
            os.remove(admin.img)
        imgg=app.config['UPLOAD_FOLDER']+"/"+img_filename
        admin.img=imgg
    db.session.commit()
    return jsonify({"admin":"fffffffff"})

@app.route("/product")
def product():
    items1= Items.query.all()
    items=[item.to_dict() for item in items1]
    print(items)
    admins=session["Admin"]
    admin=Admin.query.filter_by(username=admins).first()
    return render_template("product.html", items=items,admin=admin)

@app.route("/ManageAdmin")
def ManageAdmin():
    Admin_list=Admin.query.all()
    admins=[]
    for admin in Admin_list:
        admins.append(
            {"id":admin.id,
            "name":admin.username,
            "img":admin.img,
            "email":admin.email,
            "phone":admin.phone
            })
    print(admins)
    adminx=session["Admin"]
    admin=Admin.query.filter_by(username=adminx).first()
    return render_template("ManageAdmin.html", Admin_list=admins,admin=admin)





@app.route("/uploadstatus/<string:id>/<int:s>")
def uploadstatus(id,s):
    order = Order.query.filter_by(id=id).first()    
    if(s==1):
        order.comform=True
        db.session.commit()
        return jsonify({"message": "order confirm"}), 200
    elif(s==2):
        order.comform=True
        order.packed=True
        db.session.commit()
        return jsonify({"message": "order confirm and packed"}), 200
    elif(s==3):
        order.comform=True
        order.packed=True
        order.dispached=True
        db.session.commit()
        return jsonify({"message": "order confirm and packed and dispached"}), 200
    elif(s==4):
        order.comform=True
        order.packed=True
        order.dispached=True
        order.outfordeliver=True
        db.session.commit()
        return jsonify({"message": "order confirm and packed and dispached and outfordeliver"})
    elif(s==5):
        order.comform=True
        order.packed=True
        order.dispached=True
        order.outfordeliver=True
        order.deliver=True
        db.session.commit()
        return jsonify({"message":"order deliverd"})
    else:
        return jsonify({"message": "invalid status"}), 400

@app.route("/view_order_history")
def view_order_history():
    orders = Order.query.filter_by(deliver=True).all()
    print(orders)
    orders_list = []
    for order in orders:
        imge=[]
        liist=[]
        for img in json.loads(order.orderimage):
            imge.append(img)
        print(imge)
        for img in json.loads(order.orderlist):
            liist.append(img)
        a=json.loads(order.address)
        print("orderlist", a)
        orders_list.append({
            "id": order.id,
            "orderimage": imge,
            "orderlist": liist,
            "total": order.total,
            "userid": order.userid,
            "address": json.loads(order.address),
            "date":order.date,
            "conform":order.conform,
            "packed":order.packed,
            "dispached":order.dispached,
            "outfordeliver":order.outfordeliver,
            "deliver":order.deliver

            })
    admins=session["Admin"]
    admin=Admin.query.filter_by(username=admins).first()
    print(admins)
    return render_template("view_order_history.html", orders_list=orders_list,admin=admin)

@app.route("/view_orders")
def view_orders():
    orders = Order.query.filter_by(deliver=False).all()
    print(orders)
    orders_list = []
    admins=session["Admin"]
    admin=Admin.query.filter_by(username=admins).first()
    for order in orders:
        imge=[]
        liist=[]
        for img in json.loads(order.orderimage):
            imge.append(img)
        for img in json.loads(order.orderlist):
            liist.append(img)
        a=json.loads(order.address)
        print("orderlist", a)
        orders_list.append({
            "id": order.id,
            "orderimage": imge,
            "orderlist": liist,
            "total": order.total,
            "userid": order.userid,
            "address": json.loads(order.address),
            "date":order.date,
            "conform":order.conform,
            "packed":order.packed,
            "dispached":order.dispached,
            "outfordeliver":order.outfordeliver,
            "deliver":order.deliver

            })
    return render_template("vieworder.html", orders_list=orders_list,admin=admin)



@app.route("/deleteadmin/<int:id>",methods=['DELETE'])
def deleteadmin(id):
    print("id")
    admin = Admin.query.get(id)
    db.session.delete(admin)
    db.session.commit()
    return jsonify({"message":"Admin Removed "})

@app.route("/dashboard")
def dashboard():
    date=datetime.now()
    print(date)
    day1 = (date - timedelta(days=1)).date()
    day2 = (date - timedelta(days=2)).date()
    day3 = (date - timedelta(days=3)).date()
    print(day1,day2,day3)
    current_month=date.month
    orders = Order.query.filter(extract('month', Order.date)==current_month).all()
    orders1 = Order.query.filter(
    or_(
        Order.date == date,
        Order.date == day1,
        Order.date == day2,
        Order.date == day3
    )).all()
    print(orders1)
    orders_list = []
    for order in orders:
        orders_list.append({
            "id": order.id,
            "orderimage": order.orderimage,
            "orderlist": order.orderlist,
            "total": order.total,
            "userid": order.userid,
            "date":order.date,
            "conform":order.conform,
            "packed":order.packed,
            "dispached":order.dispached,
            "outfordeliver":order.outfordeliver,
            "deliver":order.deliver
            })
    print("orders", orders)
    admin=session["Admin"]
    getadmin=Admin.query.filter_by(username=admin).first()
    orders_count = len(orders)
    print("orders_count", orders_count)
    total_revenue = sum(order.total for order in orders)
    if total_revenue is None:
        total_revenue = 0
    user=User.query.count()
    guest=Guest.query.count()
    active_users = user+guest
    total_items=Items.query.count()
    admins=Admin.query.count()
    #return jsonify({"total_revenue": total_revenue,"orders_count":orders_count,"active_users":active_users})
    return render_template("dashboard.html",total_revenue=total_revenue, orders_count=orders_count, active_users=active_users,orders_list=orders_list,total_items=total_items,admins=admins,admin=getadmin)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

