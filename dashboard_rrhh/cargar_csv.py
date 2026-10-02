import csv
import glob
import os
import sys
import time
from datetime import datetime
import pymysql
from config import Config

def get_connection():
    return pymysql.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD or '',
        database=Config.DB_NAME,
        charset='utf8mb4',
        autocommit=False,
        local_infile=True
    )

TABLE_FILE_PATTERNS = [
    ('eppartstatus', 'eppartstatus_*.csv'),
    ('tep_classificationpayroll', 'tep_classificationpayroll_*.csv'),
    ('grupospayroll', 'grupospayroll_*.csv'),
    ('areaspayroll', 'areaspayroll_*.csv'),
    ('departmentspayroll', 'departmentspayroll_*.csv'),
    ('zperiodos', 'zperiodos_*.csv'),
    ('userpayroll', 'userpayroll_*.csv'),
    ('zgrroles', 'zgrroles_*.csv'),
    ('zparte', 'zparte_*.csv'),
]

def clean_value(val):
    if val is None:
        return None
    val_str = str(val).strip()
    if val_str == '' or val_str.lower() == 'null':
        return None
    return val_str

def load_table(cursor, conn, table_name, csv_path, batch_size=5000):
    print(f"\n--- Cargando tabla: {table_name} desde {os.path.basename(csv_path)} ---")
    start_time = time.time()
    
    with open(csv_path, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.reader(f, delimiter=';', quotechar='"')
        headers = [h.strip().strip('"') for h in next(reader)]
        
        # Obtener columnas válidas de la tabla en la base de datos
        cursor.execute(f"DESCRIBE `{table_name}`")
        db_cols = {row[0]: row[1] for row in cursor.fetchall()}
        
        valid_indices = []
        valid_headers = []
        for idx, h in enumerate(headers):
            if h in db_cols:
                valid_indices.append(idx)
                valid_headers.append(h)
        
        cols_clause = ", ".join([f"`{h}`" for h in valid_headers])
        placeholders = ", ".join(["%s"] * len(valid_headers))
        insert_sql = f"INSERT INTO `{table_name}` ({cols_clause}) VALUES ({placeholders})"
        
        cursor.execute(f"TRUNCATE TABLE `{table_name}`")
        
        batch = []
        total_rows = 0
        for row in reader:
            cleaned_row = []
            for idx in valid_indices:
                raw_val = row[idx] if idx < len(row) else None
                col_name = valid_headers[len(cleaned_row)]
                col_type = db_cols[col_name].lower()
                
                val = clean_value(raw_val)
                if val is not None:
                    if 'int' in col_type or 'tinyint' in col_type or 'bigint' in col_type:
                        try:
                            val = int(val)
                        except ValueError:
                            try:
                                val = int(float(val))
                            except ValueError:
                                val = None
                    elif 'decimal' in col_type or 'float' in col_type or 'double' in col_type:
                        try:
                            val = float(val.replace(',', '.'))
                        except ValueError:
                            val = None
                    elif 'date' in col_type:
                        # Verificar fecha básica YYYY-MM-DD
                        if len(val) >= 10:
                            val = val[:10]
                        else:
                            val = None
                cleaned_row.append(val)
            
            batch.append(cleaned_row)
            if len(batch) >= batch_size:
                cursor.executemany(insert_sql, batch)
                conn.commit()
                total_rows += len(batch)
                batch = []
                elapsed = time.time() - start_time
                print(f"  Insertadas {total_rows} filas ({total_rows / elapsed:.0f} filas/seg)...", end='\r')
        
        if batch:
            cursor.executemany(insert_sql, batch)
            conn.commit()
            total_rows += len(batch)
            
    elapsed = time.time() - start_time
    print(f"  [OK] Total {total_rows} filas insertadas en {table_name} en {elapsed:.2f} segundos.")

def main(csv_dir='C:/Users/raman/Downloads/copia'):
    print(f"Buscando archivos CSV en: {csv_dir}")
    if not os.path.exists(csv_dir):
        print(f"Error: La carpeta {csv_dir} no existe.")
        return

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
        cursor.execute("SET UNIQUE_CHECKS = 0;")
        try:
            cursor.execute("SET sql_log_bin = 0;")
        except Exception:
            pass
        conn.commit()

        for table_name, pattern in TABLE_FILE_PATTERNS:
            matches = glob.glob(os.path.join(csv_dir, pattern))
            if not matches:
                print(f"No se encontró archivo para la tabla {table_name} con patrón {pattern}")
                continue
            csv_path = matches[0]
            load_table(cursor, conn, table_name, csv_path)

        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
        cursor.execute("SET UNIQUE_CHECKS = 1;")
        conn.commit()
        print("\n=== CARGA COMPLETA EXITOSA ===")
    except Exception as e:
        conn.rollback()
        print(f"\nError durante la carga: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    csv_dir = sys.argv[1] if len(sys.argv) > 1 else 'C:/Users/raman/Downloads/copia'
    main(csv_dir)
