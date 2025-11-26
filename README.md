# Lector Modbus RTU para Medidor Vortex de Gas

![Python](https://img.shields.io/badge/python-3.7+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

Sistema de lectura y monitoreo en tiempo real de un medidor de flujo tipo Vortex mediante comunicación Modbus RTU a través de RS485. Este proyecto permite obtener e interpretar datos del medidor de gas utilizando un adaptador USB a RS485, ofreciendo una alternativa gratuita y de código abierto al software propietario **Modbus Poll**.

## 🎯 Motivación del Proyecto

El software recomendado en el manual del medidor (Modbus Poll) es de pago y puede resultar costoso para proyectos pequeños o de uso ocasional. Este script en Python ofrece la misma funcionalidad de forma completamente gratuita, permitiendo:

- ✅ Lectura de registros Modbus RTU
- ✅ Interpretación automática de datos del medidor
- ✅ Monitoreo en tiempo real
- ✅ Código abierto y personalizable
- ✅ Sin costo de licencias

## 📋 Características

- **Lectura continua** de registros Modbus RTU
- **Interpretación automática** de valores en formato float (32-bit Little Endian Byte Swap)
- **Validación de CRC-16** para garantizar integridad de datos
- **Mapeo de registros** con nombres descriptivos:
  - Temperatura
  - Metros cúbicos/hora (caudal)
  - Presión
  - Frecuencia
  - Multiplicador
  - Flujo Total acumulado
- **Visualización en tiempo real** de todas las variables del medidor
- **Manejo robusto de errores** de comunicación

## 🔧 Requisitos del Sistema

### Hardware
- Medidor de flujo tipo Vortex con soporte Modbus RTU
- Adaptador USB a RS485
- Cable RS485 (par trenzado, recomendado con blindaje)
- PC con puerto USB disponible

### Software
- Python 3.7 o superior
- Biblioteca `pyserial`

## 📦 Instalación

### 1. Clonar el repositorio
```bash
git clone https://github.com/tu-usuario/RS485.git
cd RS485
```

### 2. Instalar dependencias
```bash
pip install pyserial
```

O si usas un entorno virtual (recomendado):
```bash
python -m venv venv
venv\Scripts\activate  # En Windows
pip install pyserial
```

## ⚙️ Configuración

### 1. Identificar el puerto COM

Conecta el adaptador USB a RS485 y verifica el puerto asignado en el Administrador de Dispositivos de Windows.

### 2. Configurar el script

Abre `modbus_rtu_simulator.py` y modifica las siguientes variables según tu configuración:

```python
SERIAL_PORT = 'COM8'  # Cambiar al puerto correcto (ej: COM3, COM4, etc.)
BAUDRATE = 9600       # Verificar en manual del medidor
PARITY = serial.PARITY_NONE
STOPBITS = serial.STOPBITS_ONE
```

### 3. Configurar el medidor

Asegúrate de que tu medidor Vortex esté configurado con:
- **Slave ID**: 1 (por defecto en el script)
- **Baudrate**: 9600 (o el que hayas configurado)
- **Paridad**: None
- **Stop bits**: 1
- **Data bits**: 8

## 🚀 Uso

### Ejecución básica
```bash
python modbus_rtu_simulator.py
```

### Salida esperada
```
=== Cliente Modbus RTU - Lector de Registros ===
Puerto: COM8
Baudrate: 9600
Comando: 01 03 00 00 00 0E (Slave 1, Función 3, Dir 0, Cant 14)
Formato: 32-bit float, Little Endian Byte Swap
Puerto COM8 abierto correctamente

Enviando solicitud: 01 03 00 00 00 0E 44 0C
Respuesta recibida: 01 03 1C 42 12 33 44 41 C8 00 00 3F 80 00 00 ...

✓ Respuesta válida (CRC correcto)
  Slave ID: 1
  Función: 3
  Bytes de datos: 28

--- Valores Leídos ---
  Temperatura         :    25.456789
  Metros cúbicos/h    :    12.345678
  Presión             :    1.013250
  Frecuencia          :    50.000000
  Multiplicador       :    1.000000
  Flujo Total         :  1234.567890
  Desconocido 2       :    0.000000
----------------------
```

### Detener el programa
Presiona `Ctrl+C` para detener la lectura de forma segura.

## 📡 Protocolo Modbus RTU

### Comando enviado
El script envía el siguiente comando Modbus:
```
01 03 00 00 00 0E 44 0C
```

**Desglose:**
- `01`: Slave ID (dirección del dispositivo)
- `03`: Función 3 (Read Holding Registers)
- `00 00`: Dirección inicial (registro 0)
- `00 0E`: Cantidad de registros (14 registros = 28 bytes)
- `44 0C`: CRC-16 (calculado automáticamente)

### Formato de datos
Los valores se almacenan como **float de 32 bits** con formato **Little Endian Byte Swap**:
- Cada valor ocupa 4 bytes (2 registros Modbus)
- Los bytes vienen intercambiados por pares: `[B1, B0, B3, B2]`
- El script realiza la conversión automáticamente

## 🗺️ Mapeo de Registros

| Registro | Variable          | Descripción                    | Unidad      |
|----------|-------------------|--------------------------------|-------------|
| 0-1      | Temperatura       | Temperatura del fluido         | °C          |
| 2-3      | Metros cúbicos/h  | Caudal instantáneo             | m³/h        |
| 4-5      | Presión           | Presión del fluido             | Bar/PSI     |
| 6-7      | Frecuencia        | Frecuencia del vortex          | Hz          |
| 8-9      | Multiplicador     | Factor de multiplicación       | -           |
| 10-11    | Flujo Total       | Volumen total acumulado        | m³          |
| 12-13    | Desconocido 2     | Registro adicional             | -           |

## 🔍 Solución de Problemas

### Error: "No se recibió respuesta del dispositivo"
- Verifica las conexiones físicas RS485 (A con A, B con B)
- Comprueba que el medidor esté encendido y configurado correctamente
- Verifica el Slave ID del medidor (debe coincidir con el del script)
- Prueba invertir los cables A y B si persiste el problema

### Error: "Error al abrir el puerto serial"
- Verifica que el puerto COM sea el correcto
- Cierra cualquier otro programa que esté usando el puerto
- Verifica que los drivers del adaptador USB-RS485 estén instalados

### Error de CRC
- Puede indicar ruido en la línea RS485
- Verifica la calidad de los cables y conexiones
- Considera usar cable blindado y terminadores de línea

### Valores incorrectos o sin sentido
- Verifica el formato de datos en el manual del medidor
- El script asume formato Little Endian Byte Swap
- Algunos medidores pueden usar Big Endian o sin byte swap

## 📝 Personalización

### Cambiar el intervalo de lectura
Modifica el valor en la línea:
```python
time.sleep(2)  # Cambia el valor en segundos
```

### Agregar más registros
Actualiza el diccionario `REGISTER_MAP`:
```python
REGISTER_MAP = {
    0: "Temperatura",
    2: "Metros cúbicos/h",
    # ... agregar más registros aquí
    14: "Nuevo Registro"
}
```

### Cambiar Slave ID
Modifica en la función `main()`:
```python
request = create_request(
    slave_id=0x02,  # Cambiar a 2, 3, etc.
    ...
)
```

## 📚 Referencias

- [Especificación Modbus RTU](https://modbus.org/docs/Modbus_Application_Protocol_V1_1b3.pdf)
- [Protocolo RS485](https://en.wikipedia.org/wiki/RS-485)
- [Documentación pySerial](https://pyserial.readthedocs.io/)

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:
1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto es de código abierto y está disponible bajo la Licencia MIT.

## 👤 Autor

Christofer Borrayo

## 🙏 Agradecimientos

- Proyecto creado como alternativa gratuita a Modbus Poll
- Gracias a la comunidad de Python y Modbus por la documentación

---

**¿Preguntas o sugerencias?** Abre un issue en el repositorio.

**¿Te resultó útil?** Dale una ⭐ al proyecto.
