
from flask import Flask, render_template
from models import db, Product

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/shop')
def shop():
    products = Product.query.all()
    return render_template('shop.html', products=products)


if __name__ == '__main__':
    app.run(debug=True)
