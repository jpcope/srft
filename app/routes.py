from app import app
from flask import make_response

@app.route('/healthcheck', methods=['GET'], strict_slashes=False)
def healthcheck():
    return make_response('ok', 200)
