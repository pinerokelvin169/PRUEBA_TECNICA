import psycopg2
import requests

#ES NECESARIO CREAR LA BASE DE DATOS CON ESTOS DATOS
# Configuracion
DB_HOST = 'localhost'
DB_PORT = '5432'
DB_NAME = 'operaciones'
DB_USER = 'postgres'
DB_PASSWORD = '1234'

API_URL = "https://gist.githubusercontent.com/wimontenegro/c674b389fee25b03a6ad10424d866a62/raw/api_chardon_snapshot.json"

print("Conectando a PostgreSQL...")
try:
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    cursor = conn.cursor()
    print("Conectado")
except Exception as e:
    print("Error: {}".format(e))
    exit(1)

print("\nLeyendo datos de BD...")
cursor.execute("SELECT id_operacion, fecha_operacion, cliente, monto, estado, canal FROM operaciones")
bd_data = {}
for row in cursor.fetchall():
    id_op = row[0]
    bd_data[id_op] = {
        'fecha_operacion': row[1],
        'cliente': row[2],
        'monto': row[3],
        'estado': row[4],
        'canal': row[5]
    }
print("Registros en BD: {}".format(len(bd_data)))

print("\nConsultando API...")
try:
    response = requests.get(API_URL, timeout=10)
    api_response = response.json()
    # Los datos estan dentro de ["operaciones"]
    api_data_raw = api_response.get('operaciones', [])
    print("Registros en API: {}".format(len(api_data_raw)))
except Exception as e:
    print("Error en API: {}".format(e))
    api_data_raw = []

# Normalizar datos de API
api_data = {}
for op in api_data_raw:
    if isinstance(op, dict):
        id_op = op.get('id_operacion')
        if id_op:
            api_data[id_op] = {
                'fecha_operacion': op.get('fecha'),  # Campo es 'fecha' no 'fecha_operacion'
                'cliente': op.get('cliente'),
                'monto': op.get('monto'),
                'estado': op.get('estado'),
                'canal': None  # No hay canal en la API
            }

print("\nCreando tabla de discrepancias...")
cursor.execute('DROP TABLE IF EXISTS discrepancias')
cursor.execute('''
    CREATE TABLE discrepancias (
        id SERIAL PRIMARY KEY,
        id_operacion VARCHAR(50),
        campo_en_conflicto VARCHAR(50),
        valor_excel VARCHAR(500),
        valor_api VARCHAR(500),
        tipo_de_discrepancia VARCHAR(255)
    )
''')
conn.commit()
print("Tabla creada")

print("\nComparando datos...")
discrepancias_count = 0

# IDs en BD pero no en API
bd_ids = set(bd_data.keys())
api_ids = set(api_data.keys())

for id_op in sorted(bd_ids - api_ids):
    cursor.execute('''
        INSERT INTO discrepancias 
        (id_operacion, campo_en_conflicto, valor_excel, valor_api, tipo_de_discrepancia)
        VALUES (%s, %s, %s, %s, %s)
    ''', (
        id_op,
        'REGISTRO_COMPLETO',
        'EXISTE',
        'NO_EXISTE',
        'Operacion en BD pero no en API'
    ))
    discrepancias_count += 1

# IDs en API pero no en BD
for id_op in sorted(api_ids - bd_ids):
    cursor.execute('''
        INSERT INTO discrepancias 
        (id_operacion, campo_en_conflicto, valor_excel, valor_api, tipo_de_discrepancia)
        VALUES (%s, %s, %s, %s, %s)
    ''', (
        id_op,
        'REGISTRO_COMPLETO',
        'NO_EXISTE',
        'EXISTE',
        'Operacion en API pero no en BD'
    ))
    discrepancias_count += 1

# Comparar campos en registros comunes
campos = ['fecha_operacion', 'cliente', 'monto', 'estado']
for id_op in sorted(bd_ids & api_ids):
    for campo in campos:
        valor_bd = bd_data[id_op][campo]
        valor_api = api_data[id_op][campo]
        
        if str(valor_bd) != str(valor_api):
            cursor.execute('''
                INSERT INTO discrepancias 
                (id_operacion, campo_en_conflicto, valor_excel, valor_api, tipo_de_discrepancia)
                VALUES (%s, %s, %s, %s, %s)
            ''', (
                id_op,
                campo,
                str(valor_bd),
                str(valor_api),
                'Diferencia en {}'.format(campo)
            ))
            discrepancias_count += 1

conn.commit()
print("Discrepancias insertadas: {}".format(discrepancias_count))

# Mostrar resumen
cursor.execute("SELECT COUNT(*) FROM discrepancias")
total = cursor.fetchone()[0]
print("\nTotal de discrepancias en BD: {}".format(total))

cursor.execute("SELECT tipo_de_discrepancia, COUNT(*) FROM discrepancias GROUP BY tipo_de_discrepancia ORDER BY COUNT(*) DESC")
print("\nDistribucion:")
for tipo, cantidad in cursor.fetchall():
    print("  {}: {}".format(tipo, cantidad))

cursor.close()
conn.close()
print("\nCompletado")
