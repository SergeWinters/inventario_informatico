# database.py
import sqlite3

class DatabaseManager:
    def __init__(self, db_name="inventario.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.setup_tables()

    def setup_tables(self):
        # Tabla principal para cada inventario/auditoría
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente TEXT UNIQUE,
                ubicacion TEXT,
                responsable TEXT,
                fecha TEXT,
                estructura_info TEXT,
                ubicacion_manuales TEXT,
                historico_problemas TEXT,
                modo_trabajo TEXT,
                equipos_extra TEXT,
                plano_path TEXT
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS pcs (
                id INTEGER PRIMARY KEY AUTOINCREMENT, inventario_id INTEGER,
                codigo TEXT, placa TEXT, ram TEXT, core TEXT, disco TEXT, so TEXT,
                fuente TEXT, antivirus TEXT, ubicacion_equipo TEXT, observaciones TEXT,
                FOREIGN KEY (inventario_id) REFERENCES inventarios (id) ON DELETE CASCADE
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS proyectores (
                id INTEGER PRIMARY KEY AUTOINCREMENT, inventario_id INTEGER,
                codigo TEXT, modelo TEXT, tactil TEXT, ubicacion_equipo TEXT, observaciones TEXT,
                FOREIGN KEY (inventario_id) REFERENCES inventarios (id) ON DELETE CASCADE
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS impresoras (
                id INTEGER PRIMARY KEY AUTOINCREMENT, inventario_id INTEGER,
                codigo TEXT, modelo TEXT, conexion TEXT, ubicacion_equipo TEXT, observaciones TEXT,
                FOREIGN KEY (inventario_id) REFERENCES inventarios (id) ON DELETE CASCADE
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS servidores (
                id INTEGER PRIMARY KEY AUTOINCREMENT, inventario_id INTEGER,
                codigo TEXT, modelo TEXT, uso TEXT, ubicacion_equipo TEXT, observaciones TEXT,
                FOREIGN KEY (inventario_id) REFERENCES inventarios (id) ON DELETE CASCADE
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS red (
                id INTEGER PRIMARY KEY AUTOINCREMENT, inventario_id INTEGER,
                codigo TEXT, tipo TEXT, modelo TEXT, ubicacion_equipo TEXT, observaciones TEXT,
                FOREIGN KEY (inventario_id) REFERENCES inventarios (id) ON DELETE CASCADE
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS software (
                id INTEGER PRIMARY KEY AUTOINCREMENT, inventario_id INTEGER,
                nombre TEXT, licencia TEXT,
                FOREIGN KEY (inventario_id) REFERENCES inventarios (id) ON DELETE CASCADE
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS cctv_recorders (
                id INTEGER PRIMARY KEY AUTOINCREMENT, inventario_id INTEGER,
                marca TEXT, modelo TEXT, canales TEXT, ubicacion TEXT, observaciones TEXT,
                FOREIGN KEY (inventario_id) REFERENCES inventarios (id) ON DELETE CASCADE
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS cctv_cameras (
                id INTEGER PRIMARY KEY AUTOINCREMENT, inventario_id INTEGER,
                marca TEXT, modelo TEXT, tipo_lente TEXT, ubicacion TEXT, observaciones TEXT,
                FOREIGN KEY (inventario_id) REFERENCES inventarios (id) ON DELETE CASCADE
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS accesos (
                id INTEGER PRIMARY KEY AUTOINCREMENT, inventario_id INTEGER,
                marca TEXT, modelo TEXT, tipo TEXT, ubicacion TEXT, observaciones TEXT,
                FOREIGN KEY (inventario_id) REFERENCES inventarios (id) ON DELETE CASCADE
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS credenciales (
                id INTEGER PRIMARY KEY AUTOINCREMENT, inventario_id INTEGER,
                elemento TEXT, usuario TEXT, clave TEXT, notas TEXT,
                FOREIGN KEY (inventario_id) REFERENCES inventarios (id) ON DELETE CASCADE
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_type TEXT NOT NULL,
                item_id INTEGER NOT NULL,
                image_path TEXT NOT NULL
            )
        ''')

        # --- NUEVA TABLA PARA CONEXIONES ---
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS connections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parent_item_type TEXT NOT NULL,
                parent_item_id INTEGER NOT NULL,
                child_item_type TEXT NOT NULL,
                child_item_id INTEGER NOT NULL,
                notes TEXT
            )
        ''')

        self.conn.commit()

    def execute_query(self, query, params=()):
        try:
            self.cursor.execute(query, params)
            self.conn.commit()
            return self.cursor
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return None

    def fetch_all(self, query, params=()):
        try:
            self.cursor.execute(query, params)
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return []
            
    def fetch_one(self, query, params=()):
        try:
            self.cursor.execute(query, params)
            return self.cursor.fetchone()
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return None

    def close(self):
        self.conn.close()