from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, RadioField, FloatField, \
    IntegerField, IntegerRangeField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, NumberRange
from app.models import User


class RegistrationForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    phone = StringField('phone number',
                        validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password',
                             validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])

    user_type = RadioField('Choose account type', choices=[('user', 'Customer'), ('seller', 'Shop')])

    submit = SubmitField('Sign up')

    def validate_user_name(self, user_name):
        user = User.query.filter_by(username=user_name.data).first()
        if user:
            raise ValidationError('username is already taken please choose different one')

    def validate_email(self, Email):
        user = User.query.filter_by(email=Email.data).first()

        if user:
            raise ValidationError('email is already taken please choose different one')

    def validate_phone(self, phone):
        user = User.query.filter_by(phone=phone.data).first()

        if user:
            raise ValidationError('email is already taken please choose different one')



class LoginForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password',
                             validators=[DataRequired()])
    user_type = RadioField('Choose account type', choices=[('user', 'Customer'), ('seller', 'Shop')])
    remember = BooleanField('Remember me')
    submit = SubmitField('Login in')


class SearchForm(FlaskForm):
    searched = StringField('Searched', validators=[DataRequired()])
    submit = SubmitField('Update')


class UpdateAccountForm(FlaskForm):
    user_name = StringField('Username',
                            validators=[DataRequired(), Length(min=2, max=20)])
    phone = StringField('phone number',
                        validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    submit = SubmitField('Update')

    def validate_user_name(self, user_name):
        if current_user.username != user_name.data:
            user = User.query.filter_by(username=user_name.data).first()
            if user:
                raise ValidationError('username is already taken please choose different one')

    def validate_email(self, email):
        if current_user.email != email.data:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('email is already taken please choose different one')

    def validate_phone(self, phone):
        if current_user.email != phone.data:
            user = User.query.filter_by(phone=phone.data).first()
            if user:
                raise ValidationError('email is already taken please choose different one')


class ProductForm(FlaskForm):
    product_name = StringField('product name', validators=[DataRequired()])
    description = TextAreaField('description', validators=[DataRequired()])
    picture = FileField('Product Picture', validators=[DataRequired(), FileAllowed(['jpg', 'png'])])
    price = FloatField("product Price", validators=[DataRequired()])
    quantity = IntegerField("product Quantity", validators=[DataRequired()])
    discount = FloatField("Discount")
    category = StringField('category')
    submit = SubmitField('Add product')


class UpdateProductForm(FlaskForm):
    product_name = StringField('product name')
    description = TextAreaField('description')
    picture = FileField('Product Picture')
    price = FloatField("product Price")
    quantity = IntegerField("product Quantity")
    discount = FloatField("Discount")
    category = StringField('category')
    submit = SubmitField('update product')


class AddToCart(FlaskForm):
    rate = IntegerRangeField('rate', validators=[NumberRange(min=0, max=5)])
    give_rate = SubmitField('Give rate')
    review = TextAreaField('Your review')
    voucher = StringField('voucher')
    add_to_cart = SubmitField('add to cart')


class CartForm(FlaskForm):
    proceed = SubmitField('proceed')


class PurchaseForm(FlaskForm):
    address = StringField('address', validators=[DataRequired()])
    governorate = StringField('governorate', validators=[DataRequired()])
    city = StringField('city', validators=[DataRequired()])
    proceed = SubmitField('proceed')


class OrdersForm(FlaskForm):
    statue = RadioField('Statue',
                        choices=[('shipping', 'Shipping'), ('shipped', 'Shipped'), ('delivered', 'Delivered')])
    submit = SubmitField('submit')


class VoucherForm(FlaskForm):
    voucher = StringField('voucher', validators=[DataRequired()])
    sale = FloatField('sale', validators=[NumberRange(min=0, max=1)])
    submit = SubmitField('submit')
