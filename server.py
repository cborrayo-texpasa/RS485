# Server temporal que permita solo verificar que el script principal funciona
from flask import Flask, request, jsonify
app = Flask(__name__)
@app.route('/api/gasmeter', methods=['POST'])
def gasmeter():
    data = request.get_json()
    print("Datos recibidos en la API:")
    print(data)
    return jsonify({"status": "success", "message": "Datos recibidos"}), 200
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)