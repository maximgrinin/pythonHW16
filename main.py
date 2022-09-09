from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from data import users_data, orders_data, offers_data

# Задаем параметры Flask-приложения
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JSON_AS_ASCII'] = False
app.url_map.strict_slashes = False
db = SQLAlchemy(app)


# Модель для пользователей
class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(200), nullable=False)
    last_name = db.Column(db.String(200))
    age = db.Column(db.Integer)
    email = db.Column(db.String(100))
    role = db.Column(db.String(30))
    phone = db.Column(db.String(20))
    as_executor_in_offers = db.relationship('Offer', foreign_keys='Offer.executor_id')
    as_executor_in_orders = db.relationship('Order', foreign_keys='Order.executor_id')
    as_customer_in_orders = db.relationship('Order', foreign_keys='Order.customer_id')

    def as_dict(self):
        return {
            'id:': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'age': self.age,
            'email': self.email,
            'role': self.role,
            'phone': self.phone
        }


# Модель для заказов
class Order(db.Model):
    __tablename__ = "orders"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255))
    # start_date = db.Column(db.Date, nullable=False)
    # end_date = db.Column(db.Date, nullable=False)
    start_date = db.Column(db.String(10), nullable=False)
    end_date = db.Column(db.String(10), nullable=False)
    email = db.Column(db.String(100))
    address = db.Column(db.String(255))
    price = db.Column(db.Integer)
    customer_id = db.Column(db.Integer, db.ForeignKey(User.id, onupdate="cascade"))
    executor_id = db.Column(db.Integer, db.ForeignKey(User.id, onupdate="cascade"))
    as_order_in_offers = db.relationship('Offer', foreign_keys='Offer.order_id')

    def as_dict(self):
        return {
            'id:': self.id,
            'name': self.name,
            'description': self.description,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'address': self.address,
            'price': self.price,
        }


# Модель для предложений
class Offer(db.Model):
    __tablename__ = "offers"
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey(Order.id))
    executor_id = db.Column(db.Integer, db.ForeignKey(User.id))
    order = db.relationship('Order', back_populates="as_order_in_offers", foreign_keys=[order_id])
    # executor = db.relationship('User', back_populates="as_executor_in_offers", foreign_keys=[executor_id])

    def as_dict(self):
        return {
            'id:': self.id,
            'order_id': self.order_id,
            'executor_id': self.executor_id
        }


# Пересоздаем таблицы согласно модели и проливаем данные
db.drop_all()
db.create_all()

users = [User(**row) for row in users_data]
order = [Order(**row) for row in orders_data]
offer = [Offer(**row) for row in offers_data]

with db.session.begin():
    db.session.add_all(users)
    db.session.add_all(order)
    db.session.add_all(offer)


# Функция для получения всех сущностей
def get_all_items(model):
    try:
        result_list: list[dict] = [row.as_dict() for row in model.query.all()]
    except Exception as e:
        return jsonify(f'Ошибка: {e}')
    return jsonify(result_list), 200


# Функция для возврата данных сущности по id
def get_item_by_id(model, idx):
    try:
        # result_item: dict | None = model.query.get(idx).as_dict()
        result_item: model | None = model.query.get(idx)
        if result_item is None:
            result_item_as_list = []
        else:
            result_item_as_list = result_item.as_dict()
    except Exception as e:
        return jsonify(f'Ошибка: {e}')
    return jsonify(result_item_as_list), 200


# Функция добавления новой сущности
def add_item(model):
    try:
        item_data = request.json
        new_item = model(**item_data)
        db.session.add(new_item)
    except Exception as e:
        return jsonify(f'Ошибка: {e}')
    db.session.commit()
    return jsonify(f"Сущность добавлена {new_item.as_dict()}")


# Функция обновления сущности
def update_item(model, idx):
    try:
        new_item_data = request.json
        item_data = model.query.get(idx)
        [setattr(item_data, key, value) for key, value in new_item_data.items()]
        db.session.add(item_data)
    except Exception as e:
        return jsonify(f'Ошибка: {e}')
    db.session.commit()
    return jsonify(f"Данные сущности обновлены {model.query.get(idx).as_dict()}")


# Функция удаления сущности
def delete_item(model, idx):
    try:
        item = model.query.get(idx)
        db.session.delete(item)
    except Exception as e:
        return jsonify(f'Ошибка: {e}')
    db.session.commit()
    return jsonify('Сущность удалена'), 200


# Представления для получения/добавления/изменения/удаления данных
@app.route('/')
def hello():
    return jsonify('Давайте начнем, укажите правильный URL')


@app.route('/users', methods=['GET', 'POST'])
def get_post_users():
    if request.method == 'GET':
        return get_all_items(User)
    if request.method == 'POST':
        return add_item(User)
    else:
        return jsonify('Неверный метод запроса'), 500


@app.route('/users/<int:idx>', methods=['GET', 'PUT', 'DELETE'])
def get_put_delete_user(idx):
    if request.method == 'GET':
        return get_item_by_id(User, idx)
    if request.method == 'PUT':
        return update_item(User, idx)
    if request.method == 'DELETE':
        return delete_item(User, idx)
    else:
        return jsonify('Неверный метод запроса'), 500


@app.route('/orders', methods=['GET', 'POST'])
def get_post_orders():
    if request.method == 'GET':
        return get_all_items(Order)
    if request.method == 'POST':
        return add_item(Order)
    else:
        return jsonify('Неверный метод запроса'), 500


@app.route('/orders/<int:idx>', methods=['GET', 'PUT', 'DELETE'])
def get_put_delete_order(idx):
    if request.method == 'GET':
        return get_item_by_id(Order, idx)
    if request.method == 'PUT':
        return update_item(Order, idx)
    if request.method == 'DELETE':
        return delete_item(Order, idx)
    else:
        return jsonify('Неверный метод запроса'), 500


@app.route('/offers', methods=['GET', 'POST'])
def get_post_offers():
    if request.method == 'GET':
        return get_all_items(Offer)
    if request.method == 'POST':
        return add_item(Offer)
    else:
        return jsonify('Неверный метод запроса'), 500


@app.route('/offers/<int:idx>', methods=['GET', 'PUT', 'DELETE'])
def get_put_delete_offer(idx):
    if request.method == 'GET':
        return get_item_by_id(Offer, idx)
    if request.method == 'PUT':
        return update_item(Offer, idx)
    if request.method == 'DELETE':
        return delete_item(Offer, idx)
    else:
        return jsonify('Неверный метод запроса'), 500


if __name__ == "__main__":
    app.run()
