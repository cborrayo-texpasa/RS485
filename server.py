# Server temporal que permita solo verificar que el script principal funciona
from flask import Flask, request, jsonify
app = Flask(__name__)
@app.route('/api/gasmonitor', methods=['POST'])
def gasmeter():
    data = request.get_json()
    print("INICIO------------------------------")
    print("Datos recibidos en la API:")
    print(data)
    # Print x-api-key
    print("x-api-key:", request.headers.get('x-api-key'))
    print("FIN--------------------------------")
    return jsonify({"status": "success", "message": "Datos recibidos"}), 200
if __name__ == '__main__':
    app.run(host='192.168.16.13', port=80)