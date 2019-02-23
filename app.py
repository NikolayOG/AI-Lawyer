from flask import Flask
from flask import jsonify
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, request
from flask_pymongo import PyMongo, ObjectId
from flask import make_response

app = Flask(__name__)
app.config['MONGO_DBNAME'] = 'reports' # name of database on mongo
app.config["MONGO_URI"] = "mongodb://127.0.0.1:27017/glh"

mongo = PyMongo(app)


questions = {
    'q1': 'How old are you'
}

# @app.route('/')
# def hello_world():
#     print(mongo.db)
#
#     user_id = mongo.db.claimants.insert_one({'name': 'david'}).inserted_id
#
#     print(user_id)
#
#
#     return 'Hello World'


@app.route('/create_user', methods=['POST'])
def create_user():
    content = request.json

    name = content['name']

    user_id = mongo.db.claimants.insert_one({'name': name}).inserted_i


    return jsonify(
        user_id=str(user_id)
    )


@app.route('/get_question/<string:user_id>', methods=['POST'])
def get_question(user_id):
    content = request.json

    print('heeeeeree', mongo.db.claimants.find_one({"_id": ObjectId(str(user_id))}))

    # name = content['name']

    return jsonify(
        {
            'q1': 'How old are you?'
        }
    )


@app.route('/answer_question/<string:user_id>', methods=['POST'])
def answer_question(user_id):
    content = request.json

    question_id = content['question_id']
    answer = content['answer']

    mongo.db.claimants.find_one_and_update(
        {"_id": ObjectId(str(user_id))},
        {"$set": {question_id: answer}}
    )

    return '200'


if __name__ == '__main__':
    app.run(debug=True)
