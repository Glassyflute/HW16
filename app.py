from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
import json
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///C:\\pythonProject\\HW16\\test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# Есть пользователь, он может быть как заказчиком, так и исполнителем.
# Пользователь с ролью Заказчик может создать Заказ.
# Пользователь с ролью Исполнитель может откликнуться на Заказ
# и предложить выполнить его (Offer).

class UserRole(db.Model):
    __tablename__ = 'user_roles'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_role = db.Column(db.String(50))


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer)
    email = db.Column(db.String(50), unique=True)
    role_id = db.Column(db.Integer, db.ForeignKey("user_roles.id"))
    phone = db.Column(db.String(50), unique=True)

    role = relationship("UserRole")

    def serialize_user(self):
        """
        Метод Serialize для класса User
        """
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "age": self.age,
            "email": self.email,
            "role": self.role.user_role,
            "phone": self.phone,
        }


class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String, nullable=False)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    address = db.Column(db.String(300))
    price = db.Column(db.Integer, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    executor_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    customer = relationship("User", foreign_keys="Order.customer_id")
    executor = relationship("User", foreign_keys="Order.executor_id")

    def serialize_order(self):
        """
        Метод Serialize для класса Order
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "address": self.address,
            "price": self.price,
            "customer_id": self.customer_id,
            "executor_id": self.executor_id,
        }


class Offer(db.Model):
    __tablename__ = 'offers'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"))
    executor_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    executor = relationship("User")
    order = relationship("Order")

    def serialize_offer(self):
        """
        Метод Serialize для класса Offer
        """
        return {
            "id": self.id,
            "order_id": self.order_id,
            "executor_id": self.executor_id,
        }


db.drop_all()
db.create_all()


def load_data_from_json(file_json):
    """
    загружает данные из json файла
    :param file_json:
    :return:
    """
    with open(file_json, "r", encoding="utf-8") as file:
        data = json.load(file)
    return data


def data_migrate_commit(file_json, model_name):
    """
    Переносим данные, получаемые из json, в БД (миграция).
    Запись добавлена, если не существовала. Формат даты изменен.
    :param file_json: название файла с данными
    :param model_name: название модели
    :return:
    """
    data = load_data_from_json(file_json)

    for data_item in data:
        # меняем формат даты в orders.json со строки на формат для БД
        key_start = "start_date"
        if key_start in data_item.keys():
            start_date_value = data_item[key_start]
            if isinstance(start_date_value, str) and start_date_value.count("/") == 2:
                data_item[key_start] = datetime.strptime(start_date_value, "%m/%d/%Y")

        key_end = "end_date"
        if key_end in data_item.keys():
            end_date_value = data_item[key_end]
            if isinstance(end_date_value, str) and end_date_value.count("/") == 2:
                data_item[key_end] = datetime.strptime(end_date_value, "%m/%d/%Y")

        # проверяем на существование записи. Если есть запись, повторно не создается.
        if db.session.query(model_name).filter(model_name.id == data_item["id"]).first() is None:
            new_data_item = model_name(**data_item)
            db.session.add(new_data_item)

    db.session.commit()


# заполняем таблицы данными из файлов на основе моделей
data_migrate_commit("user_roles.json", UserRole)
data_migrate_commit("users.json", User)

data_migrate_commit("orders.json", Order)
data_migrate_commit("offers.json", Offer)


# Users

# все пользователи
@app.route("/users", methods=["GET"])
def get_all_users():
    all_users = User.query.all()

    users_to_show = []
    for user in all_users:
        user_dict = user.serialize_user()
        users_to_show.append(user_dict)

    return jsonify(users_to_show)


# вьюшка на отображение 1 пользователя по его id
@app.route("/users/<int:uid>", methods=["GET"])
def get_user_by_uid(uid):
    user = User.query.get(uid)
    if user is None:
        return "Такого пользователя не существует."

    return jsonify(user.serialize_user())


# добавление пользователя
@app.route("/users", methods=["POST"])
def add_new_user():
    data = request.json

    db.session.add(User(**data))
    db.session.commit()

    return "Пользователь добавлен."

# Пример на добавление пользователя
# {
#     "age": 28,
#     "email": "daniel_m@mymail.com",
#     "first_name": "Malcolm",
#     "last_name": "Dennie",
#     "phone": "6428998000",
#     "role_id": 1
# }


# обновление информации по пользователю
@app.route("/users/<int:uid>", methods=["PUT"])
def update_user_by_uid(uid):
    data = request.json

    user = db.session.query(User).filter(User.id == uid).first()
    if user is None:
        return "Такого пользователя не существует."

    db.session.query(User).filter(User.id == uid).update(data)
    db.session.commit()

    return "Данные пользователя обновлены."


# удаление пользователя
@app.route("/users/<int:uid>", methods=["DELETE"])
def delete_user_by_uid(uid):
    user = db.session.query(User).filter(User.id == uid).first()
    if user is None:
        return "Такого пользователя не существует."

    db.session.query(User).filter(User.id == uid).delete()
    db.session.commit()

    return "Данные пользователя удалены."


#################################################################
# Orders

# все заказы
@app.route("/orders", methods=["GET"])
def get_all_orders():
    all_orders = Order.query.all()

    orders_to_show = []
    for order in all_orders:
        order_dict = order.serialize_order()
        orders_to_show.append(order_dict)

    return jsonify(orders_to_show)


# отображение данных по 1 заказу по его id
@app.route("/orders/<int:order_id>", methods=["GET"])
def get_order_by_id(order_id):
    order = Order.query.get(order_id)
    if order is None:
        return "Такого заказа не существует."

    return jsonify(order.serialize_order())


# создание нового заказа. данные по дате сконвертированы в формат для БД.
@app.route("/orders", methods=["POST"])
def add_new_order():
    data = request.json

    key_start = "start_date"
    if key_start in data.keys():
        start_date_value = data[key_start]
        if isinstance(start_date_value, str) and start_date_value.count("/") == 2:
            data[key_start] = datetime.strptime(start_date_value, "%m/%d/%Y")

    key_end = "end_date"
    if key_end in data.keys():
        end_date_value = data[key_end]
        if isinstance(end_date_value, str) and end_date_value.count("/") == 2:
            data[key_end] = datetime.strptime(end_date_value, "%m/%d/%Y")

    db.session.add(Order(**data))
    db.session.commit()

    return "Заказ создан."

# Пример
# {
#     "name": "Подготовиться к сдаче экзамена",
#     "description": "Работа сама себя не сделает. Ползем в нужном направлении.",
#     "start_date": "04/08/2021",
#     "end_date": "03/28/2022",
#     "address": "4759 William Haven Apt. 194\nWest Cornwall, TX 43080",
#     "price": 5000,
#     "customer_id": 3,
#     "executor_id": 6
#   }


# обновление данных в заказе. данные по дате сконвертированы в формат для БД.
@app.route("/orders/<int:order_id>", methods=["PUT"])
def update_order_by_id(order_id):
    data = request.json

    order = db.session.query(Order).filter(Order.id == order_id).first()
    if order is None:
        return "Такого заказа не существует."

    key_start = "start_date"
    if key_start in data.keys():
        start_date_value = data[key_start]
        if isinstance(start_date_value, str) and start_date_value.count("/") == 2:
            data[key_start] = datetime.strptime(start_date_value, "%m/%d/%Y")

    key_end = "end_date"
    if key_end in data.keys():
        end_date_value = data[key_end]
        if isinstance(end_date_value, str) and end_date_value.count("/") == 2:
            data[key_end] = datetime.strptime(end_date_value, "%m/%d/%Y")

    db.session.query(Order).filter(Order.id == order_id).update(data)
    db.session.commit()

    return "Данные по заказу обновлены."


# удаление заказа
@app.route("/orders/<int:order_id>", methods=["DELETE"])
def delete_order_by_id(order_id):
    order = db.session.query(Order).filter(Order.id == order_id).first()
    if order is None:
        return "Такого заказа не существует."

    db.session.query(Order).filter(Order.id == order_id).delete()
    db.session.commit()

    return "Данные в заказе были удалены."


###############################

# Offers

# все предложения от исполнителей по заказам
@app.route("/offers", methods=["GET"])
def get_all_offers():
    all_offers = Offer.query.all()

    offers_to_show = []
    for offer in all_offers:
        offer_dict = offer.serialize_offer()
        offers_to_show.append(offer_dict)

    return jsonify(offers_to_show)


# данные по 1 предложению
@app.route("/offers/<int:offer_id>", methods=["GET"])
def get_offer_by_id(offer_id):
    offer = Offer.query.get(offer_id)
    if offer is None:
        return "Выбранное предложение на исполнение заказа отсутствует."

    return jsonify(offer.serialize_offer())


# создание нового предложения на заказ
@app.route("/offers", methods=["POST"])
def add_new_offer():
    data = request.json

    db.session.add(Offer(**data))
    db.session.commit()

    return "Данные по предложению на исполнение заказа добавлены."

# Пример
# {
#     "order_id": 50,
#     "executor_id": 10
#   }


# обновление данных в предложении выполнить заказ
@app.route("/offers/<int:offer_id>", methods=["PUT"])
def update_offer_by_id(offer_id):
    data = request.json

    offer = db.session.query(Offer).filter(Offer.id == offer_id).first()
    if offer is None:
        return "Выбранное предложение на исполнение заказа отсутствует."

    db.session.query(Offer).filter(Offer.id == offer_id).update(data)
    db.session.commit()

    return "Данные по предложению на исполнение заказа обновлены."


# удаление предложения на выполнение заказа
@app.route("/offers/<int:offer_id>", methods=["DELETE"])
def delete_offer_by_id(offer_id):
    offer = db.session.query(Offer).filter(Offer.id == offer_id).first()
    if offer is None:
        return "Выбранное предложение на исполнение заказа отсутствует."

    db.session.query(Offer).filter(Offer.id == offer_id).delete()
    db.session.commit()

    return "Данные по предложению на исполнение заказа удалены."


if __name__ == "__main__":
    app.run(debug=True)


