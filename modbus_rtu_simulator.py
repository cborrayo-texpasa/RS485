import serial
import struct
import time
import requests
import json

DEVICE_ID = "7"
SERIAL_PORTS = ['/dev/ttyUSB0', '/dev/ttyUSB1']
#SERIAL_PORTS = ['COM8']
BAUDRATE = 9600
PARITY = serial.PARITY_NONE
STOPBITS = serial.STOPBITS_ONE
BYTESIZE = serial.EIGHTBITS
TIMEOUT = 1

import os
from dotenv import load_dotenv
load_dotenv()
HOST = os.getenv("HOSTNAME")
API_KEY = os.getenv("API_KEY")

REGISTER_MAP = {
    0: "Temperatura",
    2: "Flujo",
    4: "Presión",
    6: "Frecuencia",
    8: "Multiplicador",
    10: "Flujo Total",
    12: "Unidad medida"
}

def calculate_crc(data):
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc >>= 1
                crc ^= 0xA001
            else:
                crc >>= 1
    return crc

def bytes_to_float_little_endian_byte_swap(data):
    unswapped = bytes([data[1], data[0], data[3], data[2]])
    value = struct.unpack('<f', unswapped)[0]
    return value

def create_request(slave_id, function_code, start_addr, quantity):
    request = bytearray()
    request.append(slave_id)
    request.append(function_code)
    request.append((start_addr >> 8) & 0xFF) 
    request.append(start_addr & 0xFF)
    request.append((quantity >> 8) & 0xFF)
    request.append(quantity & 0xFF)  
    crc = calculate_crc(request)
    request.append(crc & 0xFF) 
    request.append((crc >> 8) & 0xFF) 
    return bytes(request)

def parse_response(response):
    if len(response) < 5:
        return None    
    slave_id = response[0]
    function_code = response[1]
    byte_count = response[2]    
    expected_length = 3 + byte_count + 2 
    if len(response) < expected_length:
        return None    
    data_bytes = response[3:3+byte_count]
    crc_received = response[3+byte_count] | (response[3+byte_count+1] << 8)
    crc_calculated = calculate_crc(response[:3+byte_count])
    if crc_received != crc_calculated:
        return None    
    return {
        'slave_id': slave_id,
        'function_code': function_code,
        'byte_count': byte_count,
        'data': data_bytes
    }

def parse_float_registers(data_bytes):
    values = {}
    for i in range(0, len(data_bytes), 4):
        if i + 4 <= len(data_bytes):
            register_num = i // 2 
            float_bytes = data_bytes[i:i+4]
            float_value = bytes_to_float_little_endian_byte_swap(float_bytes)
            register_name = REGISTER_MAP.get(register_num, f"Registro {register_num}")
            values[register_name] = float_value
    
    return values

def saveErrorLog(message):
    with open("error_log.log", "a") as log_file:
        log_file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")

def get_raspberry_temperature():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp_str = f.read().strip()
            temp_c = int(temp_str) / 1000.0
            return temp_c
    except Exception as e:
        saveErrorLog(f"Error al leer la temperatura de la Raspberry Pi: {e}")
        return None

def send_to_api(values, COM, temperatura_raspberry):
    headers = {
        'Content-Type': 'application/json',
        'x-api-key': API_KEY
    }
    payload = {
        "device_id": DEVICE_ID,
        "com_port": COM,
        "temperatura": values.get("Temperatura"),
        "flujo": values.get("Flujo"),
        "presion": values.get("Presión"),
        "frecuencia": values.get("Frecuencia"),
        "multiplicador": values.get("Multiplicador"),
        "flujo_total": values.get("Flujo Total"),
        "unidad_medida": values.get("Unidad medida"),
        "temperatura_raspberry": temperatura_raspberry
    }
    try:
        response = requests.post(HOST, headers=headers, data=json.dumps(payload))
        if response.status_code != 200:
            saveErrorLog(f"Error al enviar datos a la API: {response.status_code} - {response.text}")
    except Exception as e:
        saveErrorLog(f"Excepción al enviar datos a la API: {e}")

def main():
    SERIAL_CONNECTED = []    
    try:
        for SERIAL_PORT in SERIAL_PORTS:
            ser = serial.Serial(
                port=SERIAL_PORT,
                baudrate=BAUDRATE,
                parity=PARITY,
                stopbits=STOPBITS,
                bytesize=BYTESIZE,
                timeout=TIMEOUT
            )        
            SERIAL_CONNECTED.append(ser)   
        while True:
            request = create_request(
                slave_id=0x01,
                function_code=0x03,
                start_addr=0x0000,
                quantity=0x000E
            )                      
            for ser in SERIAL_CONNECTED:
                ser.reset_input_buffer()       
                ser.write(request)
                time.sleep(0.1) 
                if ser.in_waiting > 0:
                    response_bytes = ser.read(ser.in_waiting)
                    parsed = parse_response(response_bytes)                    
                    if parsed:
                        values = parse_float_registers(parsed['data'])
                        temperatura_raspberry = get_raspberry_temperature()
                        send_to_api(values, ser.port, temperatura_raspberry)
                    else:
                        saveErrorLog(f"Error al parsear la respuesta en {ser.port}")
                else:
                    saveErrorLog(f"No se recibió respuesta del dispositivo en {ser.port}")
            time.sleep(2)            
    except serial.SerialException as e:
        saveErrorLog(f"Error al abrir el puerto serial: {e}")
    except KeyboardInterrupt:
        saveErrorLog("Lectura detenida por el usuario")
    finally:        
        for ser in SERIAL_CONNECTED:
            if ser.is_open:
                ser.close()
                print(f"Puerto serial {ser.port} cerrado")

if __name__ == "__main__":
    main()
