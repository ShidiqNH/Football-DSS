from flask import Flask, request, render_template
import mysql.connector

app = Flask(__name__)


@app.route('/')
def index():
    return "Test"

if __name__ == '__main__':
    app.run(debug=True)