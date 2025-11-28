"""
Cliente Modbus RTU - Lector de registros
Lee valores desde dispositivo Modbus RTU por puerto serial USB
Comando: 01 03 00 00 00 0E (lee 14 registros desde dirección 0)
Formato: 32-bit float con little endian byte swap
"""

import serial
import struct
import time
import requests
import json

# Configuración del puerto serial
#SERIAL_PORTS = ['/dev/ttyUSB0']
SERIAL_PORTS = ['COM8']
BAUDRATE = 9600
PARITY = serial.PARITY_NONE
STOPBITS = serial.STOPBITS_ONE
BYTESIZE = serial.EIGHTBITS
TIMEOUT = 1

# Configuración de la API
import os
from dotenv import load_dotenv
load_dotenv()
HOST = os.getenv("HOSTNAME")
API_KEY = os.getenv("API_KEY")

# Mapeo de registros a variables
REGISTER_MAP = {
    0: "Temperatura",
    2: "Metros cúbicos/h",
    4: "Presión",
    6: "Frecuencia",
    8: "Multiplicador",
    10: "Flujo Total",
    12: "Desconocido 2"
}

def calculate_crc(data):
    """Calcula el CRC-16 Modbus"""
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
    """
    Convierte 4 bytes con little endian byte swap a float
    Formato: los bytes vienen intercambiados por pares [1,0,3,2] -> [0,1,2,3]
    """
    # Deshacer el byte swap: [1,0,3,2] -> [0,1,2,3]
    unswapped = bytes([data[1], data[0], data[3], data[2]])
    
    # Convertir a float en formato little endian
    value = struct.unpack('<f', unswapped)[0]
    
    return value

def create_request(slave_id, function_code, start_addr, quantity):
    """Crea una solicitud Modbus RTU completa con CRC"""
    request = bytearray()
    request.append(slave_id)
    request.append(function_code)
    request.append((start_addr >> 8) & 0xFF)  # Start address high
    request.append(start_addr & 0xFF)  # Start address low
    request.append((quantity >> 8) & 0xFF)  # Quantity high
    request.append(quantity & 0xFF)  # Quantity low
    
    # Calcular y añadir CRC
    crc = calculate_crc(request)
    request.append(crc & 0xFF)  # CRC Low
    request.append((crc >> 8) & 0xFF)  # CRC High
    
    return bytes(request)

def parse_response(response):
    """Parsea una respuesta Modbus RTU"""
    if len(response) < 5:
        return None
    
    slave_id = response[0]
    function_code = response[1]
    byte_count = response[2]
    
    # Verificar que tenemos suficientes bytes
    expected_length = 3 + byte_count + 2  # header + data + CRC
    if len(response) < expected_length:
        print(f"Respuesta incompleta: esperados {expected_length} bytes, recibidos {len(response)}")
        return None
    
    data_bytes = response[3:3+byte_count]
    crc_received = response[3+byte_count] | (response[3+byte_count+1] << 8)
    
    # Verificar CRC
    crc_calculated = calculate_crc(response[:3+byte_count])
    if crc_received != crc_calculated:
        print(f"Error de CRC: recibido {crc_received:04X}, calculado {crc_calculated:04X}")
        return None
    
    return {
        'slave_id': slave_id,
        'function_code': function_code,
        'byte_count': byte_count,
        'data': data_bytes
    }

def parse_float_registers(data_bytes):
    """
    Parsea los registros y convierte a valores float
    Cada float ocupa 4 bytes (2 registros)
    """
    values = {}
    
    # Procesar cada float (4 bytes)
    for i in range(0, len(data_bytes), 4):
        if i + 4 <= len(data_bytes):
            register_num = i // 2  # Número de registro (cada 2 bytes = 1 registro)
            float_bytes = data_bytes[i:i+4]
            float_value = bytes_to_float_little_endian_byte_swap(float_bytes)
            
            # Obtener nombre del registro
            register_name = REGISTER_MAP.get(register_num, f"Registro {register_num}")
            values[register_name] = float_value
    
    return values

def print_hex(data, label=""):
    """Imprime datos en formato hexadecimal"""
    hex_str = ' '.join(f'{b:02X}' for b in data)
    print(f"{label}: {hex_str}")

def send_to_api(values, COM):
    headers = {
        'Content-Type': 'application/json',
        'x-api-key': API_KEY
    }

    payload = {
        "com_port": COM,
        "temperatura": values.get("Temperatura"),
        "metros_cubicos_por_hora": values.get("Metros cúbicos/h"),
        "presion": values.get("Presión"),
        "frecuencia": values.get("Frecuencia"),
        "multiplicador": values.get("Multiplicador"),
        "flujo_total": values.get("Flujo Total"),
        "desconocido": values.get("Desconocido 2")
    }

    try:
        response = requests.post(HOST, headers=headers, data=json.dumps(payload))
        if response.status_code == 200:
            print("Datos enviados correctamente a la API")
        else:
            print(f"Error al enviar datos a la API: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Excepción al enviar datos a la API: {e}")

def main():
    print("=== Cliente Modbus RTU - Lector de Registros ===")
    print(f"Puertos a usar: {', '.join(SERIAL_PORTS)}")
    print(f"Baudrate: {BAUDRATE}")
    print(f"Comando: 01 03 00 00 00 0E (Slave 1, Función 3, Dir 0, Cant 14)")
    print(f"Formato: 32-bit float, Little Endian Byte Swap")
    
    SERIAL_CONNECTED = []    
    try:
        for SERIAL_PORT in SERIAL_PORTS:
            # Abrir puerto serial
            ser = serial.Serial(
                port=SERIAL_PORT,
                baudrate=BAUDRATE,
                parity=PARITY,
                stopbits=STOPBITS,
                bytesize=BYTESIZE,
                timeout=TIMEOUT
            )
        
            print(f"Puerto {SERIAL_PORT} abierto correctamente\n")
            SERIAL_CONNECTED.append(ser)   
        while True:
            # Crear solicitud: Slave 1, Función 3, Dirección 0, Cantidad 14 registros
            request = create_request(
                slave_id=0x01,
                function_code=0x03,
                start_addr=0x0000,
                quantity=0x000E
            )
            
            print_hex(request, "Enviando solicitud")
            
            for ser in SERIAL_CONNECTED:
                # Limpiar buffer de entrada
                ser.reset_input_buffer()
                
                # Enviar solicitud
                ser.write(request)
                
                # Esperar respuesta
                time.sleep(0.1)  # Dar tiempo al dispositivo para responder
                
                if ser.in_waiting > 0:
                    response_bytes = ser.read(ser.in_waiting)
                    print_hex(response_bytes, "Respuesta recibida")
                    
                    # Parsear respuesta
                    parsed = parse_response(response_bytes)
                    
                    if parsed:
                        print(f"\n✓ Respuesta válida (CRC correcto)")
                        print(f"  Slave ID: {parsed['slave_id']}")
                        print(f"  Función: {parsed['function_code']}")
                        print(f"  Bytes de datos: {parsed['byte_count']}")
                        
                        # Extraer valores float
                        values = parse_float_registers(parsed['data'])
                        
                        print(f"\n--- Valores Leídos en {ser.port} ---")
                        for name, value in values.items():
                            print(f"  {name:20s}: {value:12.6f}")
                        print("----------------------\n")
                        send_to_api(values, ser.port)
                    else:
                        print(f"✗ Error al parsear la respuesta en {ser.port}\n")
                else:
                    print(f"✗ No se recibió respuesta del dispositivo en {ser.port}\n")
            
            # Esperar antes de la siguiente lectura
            time.sleep(2)
            
    except serial.SerialException as e:
        print(f"\nError al abrir el puerto serial: {e}")
        print(f"Verifica que el puerto {SERIAL_PORT} esté disponible")
    except KeyboardInterrupt:
        print("\n\nLectura detenida por el usuario")
    finally:        
        for ser in SERIAL_CONNECTED:
            if ser.is_open:
                ser.close()
                print(f"Puerto serial {ser.port} cerrado")

if __name__ == "__main__":
    main()
