from app import app, db, bcrypt
from flask import render_template, url_for, flash, redirect, request, abort
from app.forms import SearchForm, RegistrationForm, LoginForm, UpdateAccountForm, ProductForm, AddToCart, CartForm, \
    PurchaseForm, VoucherForm, OrdersForm, UpdateProductForm
from sqlalchemy import or_, and_
from app.models import User, Product, Seller, Cart, Order, PurchaseHistory, Rated, Vouchers
from flask_login import login_user, current_user, logout_user, login_required
import secrets
import os
import pandas as pd
import numpy as np
# import sklearn
from sklearn.decomposition import TruncatedSVD
from PIL import Image
from app.chatbot import faq, lsvc, tfidf


@app.route('/')
@app.route('/home')
# home route function
def home():
    if isinstance(current_user, Seller):
        is_seller = True
    else:
        is_seller = False
    page = request.args.get('page', 1, type=int)
    search_items = []
    recommended = []
    high_value = []
    products = Product.query.order_by(Product.discount.desc()).all()
    # products with highest sale
    high_value.append(products[0])
    high_value.append(products[1])
    high_value.append(products[2])
    high_value.append(products[3])
    # does the user has any recommendations variable
    r = False
    # does the user has any search variable
    s = False
    # checking if the user is authenticated and is customer to start searching for recommendations for him
    if current_user.is_authenticated and not is_seller:
        last_search = current_user.last_searched
        # querying the data bse for the last purchased product to recommend products related to it
        product_id = PurchaseHistory.query.filter_by(buyer_id=current_user.id).order_by(
            PurchaseHistory.date_of_delivery).all()
        # checking if the user had done any purchases
        if len(product_id) == 0:
            # recommending to user by last rated product
            product_id = Rated.query.filter_by(rater_id=current_user.id).order_by(Rated.rate.desc(),
                                                                                  Rated.timestamp.desc()).all()
            if len(product_id) > 0:
                p_id = product_id[0].product_id
                temp = Recommendations(p_id)
                if len(temp) != 0:
                    for id in temp:
                        recommended.append(Product.query.get(id))
                    recommended[0] = Product.query.get(p_id)

        # recommending to user by purchased products and rates
        else:
            p_id = product_id[0].product_id
            product_id = Rated.query.filter_by(rater_id=current_user.id).order_by(Rated.rate.desc(),
                                                                                  Rated.timestamp.desc()).all()
            temp = Recommendations(p_id)
            if product_id:
                r_p_id = product_id[0].product_id
                r_temp = Recommendations(r_p_id)
                for id in range(len(temp)):
                    if id % 2 == 0 and len(r_temp) > id:
                        for i in r_temp:
                            p = Product.query.get(i)
                            if p not in recommended:
                                recommended.append(p)
                                break
                    else:
                        for i in temp:
                            p = Product.query.get(i)
                            if p not in recommended:
                                recommended.append(p)
                                break
                if len(recommended) > 0:
                    recommended[0] = Product.query.get(p_id)
                    recommended[1] = Product.query.get(r_p_id)
            else:
                if len(temp):
                    for id in temp:
                        recommended.append(Product.query.get(id))
                    recommended[0] = Product.query.get(p_id)
            if len(recommended) == 0:
                product_id = Rated.query.filter_by(rater_id=current_user.id).order_by(Rated.rate.desc(),
                                                                                      Rated.product_id).all()
                if len(product_id) > 0:
                    p_id = product_id[0].product_id
                    temp = Recommendations(p_id)
                    for id in temp:
                        recommended.append(Product.query.get(id))
            if len(recommended) > 0:
                recommended[0] = Product.query.get(p_id)
        if len(recommended) > 0:
            r = True
        if last_search:
            product.searched = last_search
            products = Product.query.filter(or_(Product.product_name.like("%" + product.searched + "%"),
                                                Product.description.like("%" + product.searched + "%"))).all()
            seller = Seller.query.filter(or_(Seller.seller_name.like("%" + product.searched + "%"))).all()
            for shop in seller:
                products = products + shop.products
            search_items = list(set(products))
            search_items = search_items[:3]
            if len(search_items) > 0:
                s = True
    products = Product.query.order_by(Product.selling.desc()).paginate(page=page, per_page=8)

    return render_template('home.html', products=products, is_seller=is_seller, recomended=recommended, r=r,
                           search_items=search_items, s=s, high_value=high_value)


# shop page route
@app.route('/shop', methods=['GET', 'POST'])
def shop():
    if isinstance(current_user, Seller):
        is_seller = True
    else:
        is_seller = False
    page = request.args.get('page', 1, type=int)
    products = Product.query.order_by(Product.selling.desc()).paginate(page=page, per_page=9)
    return render_template('shop.html', products=products, is_seller=is_seller)


# register page route
@app.route('/register', methods=['GET', 'POST'])
def register():
    # checking if the user already logged in
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    # if the user submitted the register form
    if form.validate_on_submit():
        # storing user information in the data base
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        if form.user_type.data == "user":
            user = User(username=form.username.data, phone=form.phone.data, email=form.email.data,
                        password=hashed_password)
        elif form.user_type.data == "seller":
            user = Seller(seller_name=form.username.data, phone=form.phone.data, email=form.email.data,
                          password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! you can now log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


# login page route
@app.route('/login', methods=['GET', 'POST'])
def login():
    # checking if the user already logged in
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    # if the user submitted the register form
    if form.validate_on_submit():
        # searching for the user in the database
        if form.user_type.data == "user":
            user = User.query.filter_by(email=form.email.data).first()
        elif form.user_type.data == "seller":
            user = Seller.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful Please Check Email, Password or user type', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route('/logout')
# logging out function
def logout():
    logout_user()
    return redirect(url_for('home'))


# saving product picture function
def save_pic(form_pic):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_pic.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)
    output_size = (300, 300)
    i = Image.open(form_pic)
    i.thumbnail(output_size)
    i.save(picture_path)
    return picture_fn


# account page function
@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    # checking if the user updated his information
    if form.validate_on_submit():
        if isinstance(current_user, User):
            current_user.username = form.user_name.data
        elif isinstance(current_user, Seller):
            current_user.seller_name = form.user_name.data
        current_user.email = form.email.data
        current_user.phone = form.phone.data
        db.session.commit()
        flash('Your account has been updated', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        if isinstance(current_user, User):
            type = "user"
            form.user_name.data = current_user.username
        elif isinstance(current_user, Seller):
            type = 'seller'
            form.user_name.data = current_user.seller_name
        form.email.data = current_user.email
        form.phone.data = current_user.phone
        if isinstance(current_user, Seller):
            is_seller = True
        else:
            is_seller = False
    return render_template('account.html', title='account', form=form, type=type, is_seller=is_seller)


# adding new product
@app.route('/product/new', methods=['GET', 'POST'])
@login_required
def new_product():
    form = ProductForm()
    if form.validate_on_submit():
        # saving the product data in the database
        picture_file = save_pic(form.picture.data)
        product = Product(product_name=form.product_name.data, description=form.description.data, seller=current_user,
                          image_file=picture_file, category=form.category.data, price=form.price.data,
                          quantity=form.quantity.data)
        if form.discount.data:
            if form.discount.data > 1:
                discount = form.discount.data / 100
            else:
                discount = form.discount.data
            product.discount = discount
        db.session.add(product)
        db.session.commit()
        flash('Your product has been added!', 'success')
        return redirect(url_for('home'))
    return render_template('Add_product.html', title='new product',
                           form=form, legend='New product', is_seller=True)


# product page route
@app.route('/product/<int:product_id>', methods=['GET', 'POST'])
def product(product_id):
    form = AddToCart()
    product = Product.query.get_or_404(product_id)
    rater = False
    may_like = Product.query.filter_by(category=product.category).order_by(Product.rating.desc()).all()
    # products to show the user from the sme category
    may_like = may_like[:4]
    # checking if the user rated this product or not
    if current_user.is_authenticated:
        if Rated.query.get((current_user.id, product.id)):
            rater = False
        else:
            rater = True
    # checking if the user gave a review now or not
    if form.give_rate.data:
        rate = form.rate.data
        product.rating = ((product.rating * product.raters) + rate) / (product.raters + 1)
        product.raters = product.raters + 1
        Rater = Rated(rater_id=current_user.id, product_id=product.id, rate=rate, review=form.review.data)
        db.session.add(Rater)
        db.session.commit()
        return redirect(url_for("product", product_id=product.id))
    sale = 0
    # checking if the user put the product in his cart or not
    if form.add_to_cart.data:
        temp = form.voucher.data
        voucher = Vouchers.query.get([temp, product.seller.id])
        if voucher:
            sale = voucher.sale
        if product.discount:
            sale += product.discount
        price = product.price - (product.price * sale)
        print(price)
        if current_user:
            if not isinstance(current_user, User):
                flash('Please login as a customer first', 'danger')
                return redirect(url_for("login"))
            else:
                db.session.add(Cart(buyer_id=current_user.id, product_id=product_id, price=price))
                product.quantity = product.quantity - 1
                db.session.commit()
                flash('Product added to your cart successfully', 'success')
        else:
            flash('Please login first', 'danger')
            return redirect(url_for('login'))
    rates = Rated.query.filter_by(product_id=product.id).all()
    reviews = []
    stars = []
    raters = []
    for rate in rates:
        raters.append(User.query.get(rate.rater_id).username)
        reviews.append(rate.review)
        stars.append(rate.rate)
    total = len(reviews)
    if isinstance(current_user, Seller):
        is_seller = True
    else:
        is_seller = False
    return render_template('product.html', title=product.product_name, product=product, form=form, is_seller=is_seller,
                           rater=rater, reviews=reviews, stars=stars, total=total, raters=raters, may_like=may_like)


# search base
@app.context_processor
def base():
    form = SearchForm()
    return dict(form=form)


# search rote function
@app.route('/search', methods=['GET', 'POST'])
def search():
    form = SearchForm()
    products = Product.query
    if isinstance(current_user, Seller):
        is_seller = True
    else:
        is_seller = False
    if form.validate_on_submit():
        product.searched = form.searched.data
        if not is_seller and current_user.is_authenticated:
            user = User.query.get(current_user.id)
            user.last_searched = product.searched
            db.session.commit()
        products = Product.query.filter(or_(Product.product_name.like("%" + product.searched + "%"),
                                            Product.description.like("%" + product.searched + "%"))).all()
        seller = Seller.query.filter(or_(Seller.seller_name.like("%" + product.searched + "%"))).all()
        for shop in seller:
            products = products + shop.products
        products = list(set(products))
    return render_template('search.html', form=form, products=products,
                           is_seller=is_seller)


# category page rout function
@app.route('/category', methods=['GET', 'POST'])
def category():
    search_word = request.args.get('category')
    products = Product.query.filter(Product.category.like("%" + search_word + "%")).all()
    if isinstance(current_user, Seller):
        is_seller = True
    else:
        is_seller = False
    return render_template('search.html', products=products, is_seller=is_seller)


# adding to cart function
@app.route('/<string:product_id>', methods=['GET', 'POST'])
def add_to_cart(product_id):
    product = Product.query.get(product_id)
    cart = Cart(buyer_id=current_user.id, product_id=product_id, price=product.price)
    db.session.add(cart)
    db.session.commit()
    return redirect(url_for("home"))


# updating product function
@app.route('/product/<int:product_id>/update', methods=['GET', 'POST'])
@login_required
def update_product(product_id):
    product = Product.query.get_or_404(product_id)
    if product.seller != current_user:
        abort(403)
    form = UpdateProductForm()
    if request.method == 'POST' and form.validate_on_submit():
        if form.picture.data:
            picture_file = save_pic(form.picture.data)
            product.image_file = picture_file
        product.product_name = form.product_name.data
        product.category = form.category.data
        product.description = form.description.data
        product.quantity = form.quantity.data
        product.price = form.price.data
        if form.discount.data > 1:
            discount = form.discount.data / 100
        else:
            discount = form.discount.data
        product.discount = discount
        db.session.commit()
        flash('Your product has been updated', 'success')
        return redirect(url_for('product', product_id=product.id))
    form.product_name.data = product.product_name
    form.description.data = product.description
    form.category.data = product.category
    form.price.data = product.price
    form.quantity.data = product.quantity
    form.discount.data = product.discount
    return render_template('Add_product.html', title='Update Product',
                           form=form, legend='Update Product', is_seller=True)


# delete product function
@app.route('/product/<int:product_id>/delete', methods=['POST'])
@login_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    if product.seller != current_user:
        abort(403)
    db.session.delete(product)
    db.session.commit()
    flash('Your product has been deleted', 'success')
    return redirect(url_for('home'))


# shop products page function
@app.route('/seller/<string:seller_name>')
def seller_products(seller_name):
    page = request.args.get('page', 1, type=int)
    seller = Seller.query.filter_by(seller_name=seller_name).first_or_404()
    products = Product.query.filter_by(seller=seller) \
        .order_by(Product.date_posted.desc()) \
        .paginate(page=page, per_page=9)
    if isinstance(current_user, Seller):
        is_seller = True
    else:
        is_seller = False
    return render_template('seller_products.html', products=products, seller=seller, is_seller=is_seller)


# user cart page function
@app.route('/cart/<string:username>', methods=['GET', 'POST'])
def cart(username):
    form = CartForm()
    cart = Cart.query.filter_by(buyer_id=current_user.id).all()
    products = []
    total_price = 0
    for product in cart:
        products.append(Product.query.filter_by(id=product.product_id).first())
        total_price += product.price
    if form.proceed.data:
        return redirect(url_for('purchase', products_id=','.join([str(p.id) for p in products])))
    return render_template('cart.html', products=products, cart=cart, total=len(products), form=form,
                           total_price=total_price, is_seller=False)


# removing form cart function
@app.route('/cart/<string:buyer_id>/remove/,<int:product_id>', methods=['POST'])
@login_required
def remove_from_cart(buyer_id, product_id):
    cart = Cart.query.get((buyer_id, product_id))
    if cart.buyer_id != current_user.id:
        abort(403)
    product = Product.query.get_or_404(product_id)
    db.session.delete(cart)
    product.quantity += 1
    db.session.commit()
    flash('the product has been removed', 'success')
    return redirect(url_for('cart', username=current_user.username))


# purchasing function
@app.route('/purchase/<products_id>', methods=['GET', 'POST'])
def purchase(products_id):
    form = PurchaseForm()
    total_price = 0
    products = [Product.query.get(id) for id in products_id.split(',')]
    carts = Cart.query.filter_by(buyer_id=current_user.id).all()
    for product in carts:
        total_price += product.price
    if form.proceed.data:
        for i in range(len(products)):
            order = Order(buyer_id=current_user.id,
                          buyer_address=form.address.data + '/' + form.governorate.data + '/' + form.city.data,
                          seller_id=products[i].seller_id,
                          product_id=products[i].id, price=carts[i].price, statue="shipping")
            db.session.add(order)
            db.session.commit()
            empty_cart(current_user.id)
        flash('your order has been placed check buying history to know its status', 'success')
        return redirect(url_for('home'))
    return render_template('purchase.html', total_price=total_price, form=form, is_seller=False, carts=carts,
                           products=products, total=len(carts))


# emptying the cart function
def empty_cart(buyer_id):
    cart = Cart.query.filter_by(buyer_id=buyer_id).all()
    for product in cart:
        db.session.delete(product)
    db.session.commit()


# showing the purchasing histroy for user function
@app.route('/history/<string:username>', methods=['GET', 'POST'])
def history(username):
    orders = PurchaseHistory.query.filter_by(buyer_id=current_user.id).all()
    products = []
    prices = []
    for product in orders:
        products.append(Product.query.filter_by(id=product.product_id).first())
        temp = Order.query.filter(
            and_(Order.buyer_id == current_user.id, Order.product_id == product.product_id)).first()
        prices.append(temp.price)

    return render_template('history.html', total=len(products), products=products, orders=orders, is_seller=False,
                           prices=prices)


# showing pending order for user
@app.route('/user_orders/<string:username>', methods=['GET', 'POST'])
def user_orders(username):
    orders = Order.query.filter_by(buyer_id=current_user.id).all()
    products = []
    temp = len(orders)
    i = 0
    while i < temp:
        if orders[i].statue == 'delivered' or orders[i].statue == 'canceled':
            orders.remove(orders[i])
            temp -= 1
        else:
            products.append(Product.query.filter_by(id=orders[i].product_id).first())
            i += 1

    return render_template('user_orders.html', total=len(products), products=products, orders=orders,
                           is_seller=False)


# cancel order for user
@app.route('/cart/<int:order_id>/remove', methods=['POST'])
@login_required
def cancel_order(order_id):
    order = Order.query.get((order_id))
    if order.buyer_id != current_user.id:
        abort(403)
    product = Product.query.get_or_404(order.product_id)
    product.quantity += 1
    order.statue = "canceled"
    db.session.commit()
    flash('your order has been canceled', 'success')
    return redirect(url_for('user_orders', username=current_user.username))


# showing orders for shop
@app.route('/orders', methods=['GET', 'POST'])
def orders():
    orders = Order.query.filter_by(seller_id=current_user.id).all()
    products = []
    for product in orders:
        products.append(Product.query.filter_by(id=product.product_id).first())
    return render_template('orders.html', total=len(orders), orders=orders, products=products, is_seller=True)


# showing order to shop
@app.route('/order/<int:order_id>', methods=['GET', 'POST'])
def order(order_id):
    order = Order.query.get_or_404(order_id)
    form = OrdersForm()
    # changing order statue
    if form.submit.data:
        order.statue = form.statue.data
        if order.statue == 'delivered':
            temp = PurchaseHistory(buyer_id=order.buyer_id, buyer_address=order.buyer_address,
                                   seller_id=order.seller_id,
                                   product_id=order.product_id)
            product = Product.query.get(order.product_id)
            if not product.selling:
                product.selling = 0
            product.selling = product.selling + 1
            db.session.add(temp)
        db.session.commit()
    else:
        form.statue.data = order.statue
    print(order.statue)
    buyer = User.query.get(order.buyer_id)
    product = Product.query.get(order.product_id)
    return render_template('order.html', title=product.product_name, product=product, order=order, buyer=buyer,
                           form=form, is_seller=True)


# adding new voucher by shop
@app.route('/voucher/new/<string:voucher>/<float:sale>', methods=['GET', 'POST'])
@login_required
def new_voucher(voucher, sale):
    voucher = Vouchers(seller_id=current_user.id, sale=sale, voucher=voucher)
    db.session.add(voucher)
    db.session.commit()
    flash('Your voucher has been added!', 'success')
    return redirect(url_for('my_vouchers', seller_id=current_user.id))


# showing voucher to shop
@app.route('/vouchers/new<string:seller_id>', methods=['GET', 'POST'])
def my_vouchers(seller_id):
    form = VoucherForm()
    vouchers = Vouchers.query.filter_by(seller_id=seller_id).all()
    if form.validate_on_submit():
        voucher = Vouchers(seller_id=current_user.id, sale=form.sale.data, voucher=form.voucher.data)
        db.session.add(voucher)
        db.session.commit()
        flash('Your voucher has been added!', 'success')
        return redirect(url_for('my_vouchers', seller_id=current_user.id))
    return render_template('vouchers.html', total=len(vouchers), vouchers=vouchers,
                           is_seller=True, form=form)


# deleting voucher by shop
@app.route('/voucher/<string:voucher>/remove/<string:seller_id>', methods=['POST'])
@login_required
def delete_voucher(voucher, seller_id):
    voucher = Order.query.get([voucher, seller_id])
    if voucher.buyer_id != current_user.id:
        abort(403)
        db.session.delete(voucher)
    db.session.commit()
    flash('your voucher has been deleted', 'success')
    return redirect(url_for('my_vouchers', seller_id=current_user.id))


# entering the chatbot page
@app.route('/contact')
def contact():
    return render_template('contact.html')


# getting response from the chatbot
@app.route('/get-response', methods=['POST'])
def get_response():
    questions = []
    user_message = request.form["message"]
    questions.append(user_message)
    user_message = tfidf.transform(questions)
    result = lsvc.predict(user_message)
    for question in result:
        faq_data = faq.loc[faq.isin([question]).any(axis=1)]
        bot_response = faq_data['Answers'].values

    return str(bot_response)


# generating recommendations function
def Recommendations(product_ID):
    # querying the database for the products and customers and rates
    customers_ids = User.query.with_entities(User.id).all()
    customers_ids = [id for id, in customers_ids]
    products_ids = Product.query.with_entities(Product.id).all()
    products_ids = [id for id, in products_ids]
    temp = []
    for i in range(len(customers_ids)):
        for j in range(len(products_ids)):
            temp1 = []
            temp1.append(customers_ids[i])
            temp1.append(str(products_ids[j]))
            rate = Rated.query.get([customers_ids[i], products_ids[j]])
            if rate:
                temp1.append(rate.rate)
            else:
                temp1.append(0)
            temp.append(temp1)
    # generating the data frame with rates and product id and customer id
    columns = ['rater_id', 'product_id', 'rate']
    rates = pd.DataFrame(temp, columns=columns)
    # making rate matrix with the rows are customer ids and the columns are product ids and the values are the rates
    ratings_utility_matrix = rates.pivot_table(values='rate', index='rater_id', columns='product_id', fill_value=0)
    X = ratings_utility_matrix.T
    X1 = X
    SVD = TruncatedSVD(n_components=6)
    decomposed_matrix = SVD.fit_transform(X1)
    # calculating correlation matrix
    correlation_matrix = np.corrcoef(decomposed_matrix)
    correlation_product_ID = correlation_matrix[products_ids.index(product_ID)]
    # getting products with correlation higher than 0.8 with the provided product to the function
    Recommend = list(X.index[correlation_product_ID > 0.8])
    return Recommend[:8]
