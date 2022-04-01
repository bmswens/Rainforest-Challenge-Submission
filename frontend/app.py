# 3rd party 
from flask import Flask

# custom
from matrix_completion import matrix_completion

app = Flask(__name__)
app.register_blueprint(matrix_completion, url_prefix="/matrix-completion")