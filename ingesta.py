import pandas as pd
import psycopg2

# Configuración PostgreSQL
DB_HOST = 'localhost'
DB_PORT = 5432
DB_NAME = 'operaciones'
DB_USER = 'postgres'
DB_PASSWORD = '1234'

def limpiar_monto(valor):
    """Convierte monto a número decimal"""
    if pd.isna(valor):
        return None
    valor_str = str(valor).strip()
    # Formato 3.021,34 -> 3021.34
    if ',' in valor_str and '.' in valor_str:
        valor_str = valor_str.replace('.', '').replace(',', '.')
    elif ',' in valor_str:
        valor_str = valor_str.replace(',', '.')
    try:
        return float(valor_str)
    except:
        return None

def limpiar_fecha(valor):
    """Convierte fecha a formato YYYY-MM-DD"""
    if pd.isna(valor):
        return None
    try:
        fecha = pd.to_datetime(valor)
        return fecha.strftime('%Y-%m-%d')
    except:
        return None

def limpiar_estado(valor):
    """Normaliza estados"""
    if pd.isna(valor):
        return None
    estado = str(valor).strip().lower()
    if estado == 'completado':
        return 'Completado'
    elif estado == 'pendiente':
        return 'Pendiente'
    elif estado == 'rechazado':
        return 'Rechazado'
    return estado.capitalize()

# 1. Leer Excel
print("Leyendo Excel...")
df = pd.read_excel('reporte_chardon_enero2026.xlsx', sheet_name='Reporte', header=2)
df.columns = ['id_operacion', 'fecha_operacion', 'cliente', 'monto', 'estado', 'canal']
df = df[df['id_operacion'] != 'TOTAL GENERAL'].reset_index(drop=True)
print(f"✓ {len(df)} registros leídos")

# 2. Limpiar datos
print("\nLimpiando datos...")
# Borrar espacios antes y después en todos los campos de texto
df['id_operacion'] = df['id_operacion'].astype(str).str.strip()
df['cliente'] = df['cliente'].fillna('').astype(str).str.strip()
df['estado'] = df['estado'].fillna('').astype(str).str.strip()
df['canal'] = df['canal'].fillna('').astype(str).str.strip()
# Limpiar montos y fechas
df['monto'] = df['monto'].apply(limpiar_monto)
df['fecha_operacion'] = df['fecha_operacion'].apply(limpiar_fecha)
# Normalizar estados
df['estado'] = df['estado'].apply(limpiar_estado)
print("✓ Datos limpios (espacios removidos)")

# 3. Eliminar duplicados
print("\nEliminando duplicados...")
df_before = len(df)
df = df.drop_duplicates(subset=['id_operacion'], keep='first').reset_index(drop=True)
print(f"✓ {df_before - len(df)} duplicados eliminados")

# 4. Conectar a PostgreSQL
print("\nConectando a PostgreSQL...")
conn = psycopg2.connect(
    host=DB_HOST,
    port=DB_PORT,
    database=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD
)
cursor = conn.cursor()
print("✓ Conectado")

# 5. Crear tabla
print("\nCreando tabla...")
cursor.execute('''
    CREATE TABLE IF NOT EXISTS operaciones (
        id SERIAL PRIMARY KEY,
        id_operacion VARCHAR(50) UNIQUE NOT NULL,
        fecha_operacion DATE,
        cliente VARCHAR(255),
        monto DECIMAL(12, 2),
        estado VARCHAR(50),
        canal VARCHAR(50)
    )
''')
conn.commit()
print("✓ Tabla creada")

# 6. Cargar datos
print("\nCargando datos...")
insertados = 0
for idx, row in df.iterrows():
    try:
        cursor.execute('''
            INSERT INTO operaciones 
            (id_operacion, fecha_operacion, cliente, monto, estado, canal)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (
            row['id_operacion'],
            row['fecha_operacion'],
            row['cliente'] if row['cliente'] else None,
            row['monto'],
            row['estado'],
            row['canal']
        ))
        insertados += 1
    except psycopg2.IntegrityError:
        conn.rollback()
        print(f"  ⚠ Duplicado: {row['id_operacion']}")

conn.commit()
print(f"✓ {insertados} registros cargados")

# 7. Estadísticas
print("\nEstadísticas:")
cursor.execute("SELECT COUNT(*) FROM operaciones")
total = cursor.fetchone()[0]
cursor.execute("SELECT SUM(monto), AVG(monto) FROM operaciones")
suma, promedio = cursor.fetchone()
print(f"  Total: {total}")
print(f"  Suma: ${suma:,.2f}" if suma else "  Suma: $0.00")
print(f"  Promedio: ${promedio:,.2f}" if promedio else "  Promedio: $0.00")

cursor.close()
conn.close()
print("\n✅ Completado")
