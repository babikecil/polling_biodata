from flask import Flask, jsonify, request, send_from_directory
from flask_socketio import SocketIO, emit
from flask_swagger_ui import get_swaggerui_blueprint

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")  # Menambahkan SocketIO

# Data polling (untuk demo)
polls = {
    1: {'question': 'Apa warna favorit Anda?', 'options': ['Merah', 'Biru', 'Hijau'], 'votes': [0, 0, 0]},
    2: {'question': 'Apa jenis makanan favorit Anda?', 'options': ['Pizza', 'Sushi', 'Burger'], 'votes': [0, 0, 0]},
    3: {'question': 'Apa kegiatan akhir pekan favorit Anda?', 'options': ['Berkemah', 'Berbelanja', 'Menonton Film'], 'votes': [0, 0, 0]},
    4: {'question': 'Apa hobi Anda?', 'options': ['Membaca', 'Olahraga', 'Memasak'], 'votes': [0, 0, 0]},
    5: {'question': 'Apa jenis musik yang Anda suka?', 'options': ['Pop', 'Rock', 'Jazz'], 'votes': [0, 0, 0]},
}

@app.route('/')
def index():
    return send_from_directory('statics', 'index.html')

@app.route('/api/polls', methods=['GET'])
def get_polls():
    return jsonify(polls)

@app.route('/api/polls/<int:poll_id>/vote', methods=['POST'])
def vote_poll(poll_id):
    poll = polls.get(poll_id)
    if not poll:
        return jsonify({'error': 'Poll not found'}), 404
    data = request.get_json()
    option_index = data.get('option_index')
    if option_index is None or option_index < 0 or option_index >= len(poll['options']):
        return jsonify({'error': 'Invalid option index'}), 400
    poll['votes'][option_index] += 1
    socketio.emit('poll_update', {poll_id: poll})  # Emit event ke semua client
    return jsonify({'message': 'Vote recorded'}), 200

# WebSocket Event
@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'Resource not found', 'message': str(error)}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error', 'message': str(error)}), 500

@app.errorhandler(400)
def bad_request_error(error):
    return jsonify({'error': 'Bad request', 'message': str(error)}), 400

@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f"Unexpected error: {e}")
    return jsonify({'error': 'An unexpected error occurred', 'message': str(e)}), 500

# Setup Swagger UI
SWAGGER_URL = '/api/docs'
API_URL = '/statics/swagger.yaml'  # URL untuk file swagger.yaml
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={'app_name': "Polling API"}
)
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

# Serve Swagger YAML dan file statis lainnya 
@app.route('/statics/<path:path>')
def send_statics(path):
    if path == 'swagger.yaml':
        return send_from_directory('statics', path, mimetype='application/x-yaml')
    return send_from_directory('statics', path)

if __name__ == '__main__':
    socketio.run(app, debug=True)
