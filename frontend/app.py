# 3rd party 
from flask import Flask

# custom
from matrix_completion import matrix_completion
from estimation import estimation
from translation import translation

app = Flask(__name__)
app.register_blueprint(matrix_completion, url_prefix="/matrix-completion")
app.register_blueprint(estimation, url_prefix="/estimation")
app.register_blueprint(translation, url_prefix="/translation")