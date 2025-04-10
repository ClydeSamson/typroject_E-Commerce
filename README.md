# 🛍️ TYProject E-Commerce

A smart e-commerce web application built with predictive analytics and machine learning to enhance product recommendations and improve user experience.

---

## 🚀 Features

- 👕 Dynamic product recommendations using Rule Based
- 🔍 Smart search filtering with Gradient Boosting
- 🛒 Add to cart, wishlist, and secure checkout
- 🔐 Login/Sign-Up functionality with secure authentication

---

## 🛠️ Tech Stack

- **Frontend:** HTML, CSS, Bootstrap
- **Backend:** Flask (Python)
- **Machine Learning:** Rule Based, Gradient Boosting
- **Database:** PostgreSQL (make sure it's installed and running)

---

## 🔗 Libraries Used

- Flask
- Flask-WTF
- WTForms
- Werkzeug
- psycopg2 (for PostgreSQL connection)
- pandas
- scikit-learn
- pickle
- re, difflib, os
- TfidfVectorizer, LabelEncoder, GradientBoostingClassifier, RandomForestClassifier
- cosine_similarity (from sklearn.metrics.pairwise)

> ⚠️ Make sure to install them via:

pip install -r requirements.txt

---

## 📦 Installation

### 🐘 Install PostgreSQL

If not already installed, download PostgreSQL from:  
👉 [https://www.postgresql.org/download/](https://www.postgresql.org/download/)

Create a new database and user, and update the connection string in your Flask config.

---

### 🔧 Set Up the Project

git clone https://github.com/ClydeSamson/typroject_E-Commerce.git
cd typroject_E-Commerce
pip install -r requirements.txt
python app.py
