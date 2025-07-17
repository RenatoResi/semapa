from flask import jsonify

def response_success(data=None, message=None, status=200):
    resp = {'status': 'success'}
    if message:
        resp['message'] = message
    if data is not None:
        resp['data'] = data
    return jsonify(resp), status

def response_error(message, status=400):
    return jsonify({'status': 'error', 'message': message}), status
