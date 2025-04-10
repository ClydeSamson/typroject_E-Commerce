from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField,DecimalField,SelectField,TextAreaField,EmailField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, NumberRange, Regexp
from flask_wtf.file import FileField, FileRequired, FileAllowed
from .models import logclass,get_db_connection

#################################################################################################################################
class LoginForm(FlaskForm):
    email = StringField('Email', 
        validators=[DataRequired(), Email()],
        render_kw={"placeholder": "Email", "class": "form-control", "required": True}
    )
    password = PasswordField('Password',
        validators=[DataRequired(), Length(min=8)],
        render_kw={"placeholder": "Password", "class": "form-control", "required": True}
    )
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login', render_kw={"class": "btn btn-login w-100 mb-3"})

class SignupForm(FlaskForm):
    email = StringField('Email',
        validators=[DataRequired(), Email(), Length(min=6, max=120)],
        render_kw={"placeholder": "Email", "class": "form-control", "required": True}
    )
    password = PasswordField('Password',
        validators=[DataRequired(), Length(min=8, message='Password must be at least 8 characters long')],
        render_kw={"placeholder": "Password", "class": "form-control", "required": True}
    )
    confirm_password = PasswordField('Confirm Password',
        validators=[DataRequired(), EqualTo('password', message='Passwords must match')],
        render_kw={"placeholder": "Confirm Password", "class": "form-control", "required": True}
    )
    terms = BooleanField('Terms', validators=[DataRequired()])
    submit = SubmitField('Sign Up', render_kw={"class": "btn btn-login w-100 mb-3"})

    def validate_email(self, field):
        db = logclass()
        try:
            with get_db_connection() as conn:  # Use your existing connection function
                cur = conn.cursor()
                cur.execute("SELECT * FROM login WHERE email = %s", (field.data,))
                if cur.fetchone() is not None:
                    raise ValidationError('Email already registered')
        except Exception as e:
            raise ValidationError(f'Database error: {str(e)}')
##################################################################################################################################
class addproduct(FlaskForm):
    proid = StringField('Email', 
        validators=[DataRequired(), Email()],
        render_kw={"placeholder": "Email", "class": "form-control", "required": True}
    )
    password = PasswordField('Password',
        validators=[DataRequired(), Length(min=8)],
        render_kw={"placeholder": "Password", "class": "form-control", "required": True}
    )
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login', render_kw={"class": "btn btn-login w-100 mb-3"})
##################################################################################################################################
class ProductForm(FlaskForm):
    pid = StringField('Product ID', validators=[
        DataRequired(), 
        Length(min=3, message="Product ID must be at least 3 characters"),
        Regexp(r'^[0-9]+$', message="Product ID must be numeric")
    ])
    
    pname = StringField('Product Name', validators=[
        DataRequired(),
        Length(min=3, message="Product name must be at least 3 characters")
    ])
    
    description = TextAreaField('Description', validators=[
        DataRequired(),
        Length(min=10, message="Description must be at least 10 characters")
    ])
    
    category = SelectField('Category', validators=[DataRequired()], 
                          choices=[('', 'Select Category'), 
                                   ('male', 'Male'), 
                                   ('female', 'Female'), 
                                   ('kids', 'Kids')])
    
    size = SelectField('Size', validators=[DataRequired()],
                      choices=[('', 'Select Size')])
    
    price = DecimalField('Price', validators=[
        DataRequired(),
        NumberRange(min=0, message="Price must be a positive number")
    ])
    
    image = FileField('Product Image', validators=[
        FileRequired(message="Please upload a product image"),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], message="Only image files are allowed")
    ])


