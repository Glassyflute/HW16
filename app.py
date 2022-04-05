from flask import Flask, jsonify
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
# customer_id should not be equal to executor_id for one order


class Offer(db.Model):
    __tablename__ = 'offers'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"))
    executor_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    executor = relationship("User")
    order = relationship("Order")


db.drop_all()
db.create_all()


# import json data to file
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





#
# db.session.add_all(users)
# db.session.commit()


# Users
def serialize_user(user_data):
    """
    Serialize implementation
    """
    return {
        "id": user_data.id,
        "first_name": user_data.first_name,
        "last_name": user_data.last_name,
        "age": user_data.age,
        "email": user_data.email,
        "role": user_data.role,
        "phone": user_data.phone,
    }


# @app.route("/users/<int:uid>", methods=['GET'])
# def get_one(uid):
#     user = User.query.get(uid)
#     if user is None:
#         return "Такого пользователя не существует"
#
#     return jsonify(serialize_user(user))
#
#
# @app.route("/users")
# def get_all_users():
#     all_users = User.query.all()
#
#     users_to_show = []
#     for user in all_users:
#         user_dict = serialize_user(user)
#         users_to_show.append(user_dict)
#
#     return jsonify(users_to_show)


# serialize func for Orders, Offers separately. main approach is identical




# @app.route("/guides", methods=['POST'])
# def create_guide():
#     data = request.json
#     guide = Guide(
#         surname=data.get('surname'),
#         full_name=data.get('full_name'),
#         tours_count=data.get('tours_count'),
#         bio=data.get('bio'),
#         is_pro=data.get('is_pro'),
#         company=data.get('company')
#     )
#     db.session.add(guide)
#     db.session.commit()
#     return jsonify(instance_to_dict(guide))


# def update_tours_count():
#     guide = Guide.query.get(1)
#     guide.tours_count = 6
#     db.session.add(guide)
#     db.session.commit()
#     db.session.close()

# @app.route("/guides/<int:gid>/delete")
# def delete_guide_by_gid(gid):
#     guide = Guide.query.get(gid)
#     db.session.delete(guide)
#     db.session.commit()
#
#     return jsonify("")








if __name__ == "__main__":
    app.run(debug=True)


