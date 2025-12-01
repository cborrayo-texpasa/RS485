'''
Este proyecto lee en el puerto COM tty/USB0 datos enviados por el puerto COM tty/USB1 a través del protocolo RS485.
Desde el mismo puerto envia los datos desde un puerto COM hacia otro puerto COM.
Su proposito es solamente verifiacar la comunicacion entre dos puertos COM a traves del protocolo RS485.

SOLO FUNCIONAMIENTO INTERNO SIN ENVIO A SERVIDOR
'''

import serial
import time
import json

PORT_WRITE = 'COM9'  # Puerto COM para enviar datos (TX)
PORT_READ = 'COM10'   # Puerto COM para leer datos (RX)
BAUDRATE = 9600      # Velocidad de comunicación
TIMEOUT = 1          # Tiempo de espera para la lectura

def main():
    # Configurar el puerto serie para escritura
    ser_write = serial.Serial(PORT_WRITE, BAUDRATE, timeout=TIMEOUT)
    # Configurar el puerto serie para lectura
    ser_read = serial.Serial(PORT_READ, BAUDRATE, timeout=TIMEOUT)
    time.sleep(2)  # Esperar a que los puertos se inicialicen
    
    print("Iniciando comunicación RS485")
    print("Puerto TX (escritura): {}".format(PORT_WRITE))
    print("Puerto RX (lectura): {}".format(PORT_READ))
    print("-" * 50)
    
    contador = 0
    
    try:
        while True:
            # Crear datos JSON de prueba
            data_dict = {
                "timestamp": time.time(),
                "contador": contador,
                "temperatura": 25.5,
                "presion": 101.3,
                "mensaje": "Test RS485"
            }
            
            # Convertir JSON a bytes
            json_string = json.dumps(data_dict)
            data_to_send = (json_string + '\n').encode('utf-8')  # Agregar delimitador de línea
            
            # ENVIAR datos por PORT_WRITE
            print("\n[TX] Enviando JSON:", json_string)
            ser_write.write(data_to_send)
            ser_write.flush()  # Asegurar que se envíen los datos
            
            time.sleep(0.5)  # Esperar un poco para que lleguen los datos
            
            # LEER datos del PORT_READ
            if ser_read.in_waiting > 0:
                received_data = ser_read.readline()  # Leer hasta el delimitador '\n'
                try:
                    # Decodificar bytes a string y parsear JSON
                    received_string = received_data.decode('utf-8').strip()
                    received_json = json.loads(received_string)
                    print("[RX] JSON recibido:", received_json)
                    print("     Verificación: contador = {}".format(received_json.get('contador')))
                except json.JSONDecodeError as e:
                    print("[RX] Error al decodificar JSON:", e)
                    print("     Datos brutos:", received_data)
                except Exception as e:
                    print("[RX] Error:", e)
            else:
                print("[RX] No hay datos disponibles")
            
            contador += 1
            time.sleep(2)  # Pausa entre envíos
            
    except KeyboardInterrupt:
        print("\n\nComunicación interrumpida por el usuario")
    finally:
        ser_write.close()
        ser_read.close()
        print("Puertos cerrados")

if __name__ == "__main__":
    main()