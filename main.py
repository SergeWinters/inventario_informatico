# main.py
import sys
import os
import sqlite3
from PyQt6.QtWidgets import QApplication, QMainWindow, QTableWidgetItem, QMessageBox, QFileDialog, QDialog, QLabel
from PyQt6.uic import loadUi
from PyQt6.QtCore import QDate
from PyQt6.QtGui import QIcon, QAction
from database import DatabaseManager
from pdf_generator import generate_pdf

# --- Función Auxiliar para PyInstaller ---
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- Ventana de Login/Selección de Centro ---
class LoginDialog(QDialog):
    def __init__(self, db):
        super().__init__()
        loadUi(resource_path("ui_login.ui"), self)
        self.db = db
        self.selected_inventory_id = None
        self.load_centros()

        self.btn_seleccionar.clicked.connect(self.accept_selection)
        self.btn_crear.clicked.connect(self.create_and_accept)

    def load_centros(self):
        self.combo_centros.clear()
        inventories = self.db.fetch_all("SELECT id, cliente FROM inventarios ORDER BY cliente")
        self.combo_centros.addItem("--- Seleccione un centro ---", -1)
        for inv_id, cliente in inventories:
            self.combo_centros.addItem(cliente, inv_id)

    def accept_selection(self):
        if self.combo_centros.currentData() != -1:
            self.selected_inventory_id = self.combo_centros.currentData()
            self.accept()
        else:
            QMessageBox.warning(self, "Selección Requerida", "Por favor, seleccione un centro de la lista.")

    def create_and_accept(self):
        cliente_name = self.input_nuevo_centro.text().strip()
        if not cliente_name:
            QMessageBox.warning(self, "Nombre Requerido", "Por favor, ingrese un nombre para el nuevo centro.")
            return

        try:
            cursor = self.db.execute_query("INSERT INTO inventarios (cliente, fecha) VALUES (?, ?)", 
                                           (cliente_name, QDate.currentDate().toString("dd/MM/yyyy")))
            if cursor:
                self.selected_inventory_id = cursor.lastrowid
                self.accept()
            else:
                 QMessageBox.critical(self, "Error", "No se pudo crear el centro. Verifique los logs.")
        except sqlite3.IntegrityError:
             QMessageBox.critical(self, "Error", "Ya existe un centro con ese nombre.")

# --- Ventana Principal ---
class MainWindow(QMainWindow):
    # --- CORRECCIÓN AQUÍ ---
    # El 'parent' es opcional y por defecto es None.
    def __init__(self, inventory_id, app_instance=None):
        super(MainWindow, self).__init__() # No pasamos el 'parent' al constructor de QMainWindow
        self.app_instance = app_instance # Guardamos la referencia a nuestra App
        # --- FIN DE LA CORRECCIÓN ---
        
        loadUi(resource_path("ui_inventario.ui"), self)
        
        self.db = DatabaseManager()
        self.current_inventory_id = inventory_id
        
        self.editing_pc_id = None
        self.editing_proy_id = None
        self.editing_imp_id = None
        self.editing_srv_id = None
        self.editing_red_id = None
        self.editing_recorder_id = None
        self.editing_camera_id = None
        self.editing_acceso_id = None
        self.editing_sw_id = None
        self.editing_cred_id = None

        self.setup_ui()
        self.connect_signals()
        self.load_selected_inventory()

    def setup_ui(self):
        # Configurar tablas
        self.table_pcs.setEditTriggers(self.table_pcs.EditTrigger.NoEditTriggers)
        self.table_proyectores.setEditTriggers(self.table_proyectores.EditTrigger.NoEditTriggers)
        self.table_impresoras.setEditTriggers(self.table_impresoras.EditTrigger.NoEditTriggers)
        self.table_servidores.setEditTriggers(self.table_servidores.EditTrigger.NoEditTriggers)
        self.table_red.setEditTriggers(self.table_red.EditTrigger.NoEditTriggers)
        self.table_cctv_recorders.setEditTriggers(self.table_cctv_recorders.EditTrigger.NoEditTriggers)
        self.table_cctv_cameras.setEditTriggers(self.table_cctv_cameras.EditTrigger.NoEditTriggers)
        self.table_accesos.setEditTriggers(self.table_accesos.EditTrigger.NoEditTriggers)
        self.table_software.setEditTriggers(self.table_software.EditTrigger.NoEditTriggers)
        self.table_credenciales.setEditTriggers(self.table_credenciales.EditTrigger.NoEditTriggers)
        
        # Ocultar IDs de las tablas
        self.table_pcs.setColumnHidden(0, True)
        self.table_proyectores.setColumnHidden(0, True)
        self.table_impresoras.setColumnHidden(0, True)
        self.table_servidores.setColumnHidden(0, True)
        self.table_red.setColumnHidden(0, True)
        self.table_cctv_recorders.setColumnHidden(0, True)
        self.table_cctv_cameras.setColumnHidden(0, True)
        self.table_accesos.setColumnHidden(0, True)
        self.table_software.setColumnHidden(0, True)
        self.table_credenciales.setColumnHidden(0, True)
        
        self.statusbar.addPermanentWidget(QLabel("Hecho por ForgeNEX (www.forgenex.com)"))
        
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&Archivo")
        
        switch_action = QAction("Cambiar de Centro", self)
        switch_action.triggered.connect(self.switch_center)
        file_menu.addAction(switch_action)

        exit_action = QAction("Salir", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def switch_center(self):
        # --- CORRECCIÓN AQUÍ ---
        # Usamos la referencia guardada 'app_instance'
        if self.app_instance:
            self.app_instance.should_switch_user = True
        # --- FIN DE LA CORRECCIÓN ---
        self.close()

    def connect_signals(self):
        self.btn_guardar_inventario.clicked.connect(self.save_general_info)
        self.btn_select_plano.clicked.connect(self.select_plano)
        self.btn_exportar_pdf.clicked.connect(self.export_to_pdf)

        self.btn_save_pc.clicked.connect(self.save_pc)
        self.btn_save_proyector.clicked.connect(self.save_proyector)
        self.btn_save_impresora.clicked.connect(self.save_impresora)
        self.btn_save_servidor.clicked.connect(self.save_servidor)
        self.btn_save_red.clicked.connect(self.save_red)
        self.btn_save_cctv_recorder.clicked.connect(self.save_recorder) 
        self.btn_save_cctv_camera.clicked.connect(self.save_camera)
        self.btn_save_acceso.clicked.connect(self.save_acceso)
        self.btn_save_software.clicked.connect(self.save_software)
        self.btn_save_credencial.clicked.connect(self.save_credencial)

        self.btn_clear_pc.clicked.connect(self.clear_pc_inputs)
        self.btn_clear_proyector.clicked.connect(self.clear_proyector_inputs)
        self.btn_clear_impresora.clicked.connect(self.clear_impresora_inputs)
        self.btn_clear_servidor.clicked.connect(self.clear_servidor_inputs)
        self.btn_clear_red.clicked.connect(self.clear_red_inputs)
        self.btn_clear_cctv_recorder.clicked.connect(self.clear_recorder_inputs)
        self.btn_clear_cctv_camera.clicked.connect(self.clear_camera_inputs)
        self.btn_clear_acceso.clicked.connect(self.clear_acceso_inputs)
        self.btn_clear_software.clicked.connect(self.clear_software_inputs)
        self.btn_clear_credencial.clicked.connect(self.clear_credencial_inputs)

        self.btn_del_pc.clicked.connect(lambda: self.delete_item('pcs', self.table_pcs, self.clear_pc_inputs))
        self.btn_del_proyector.clicked.connect(lambda: self.delete_item('proyectores', self.table_proyectores, self.clear_proyector_inputs))
        self.btn_del_impresora.clicked.connect(lambda: self.delete_item('impresoras', self.table_impresoras, self.clear_impresora_inputs))
        self.btn_del_servidor.clicked.connect(lambda: self.delete_item('servidores', self.table_servidores, self.clear_servidor_inputs))
        self.btn_del_red.clicked.connect(lambda: self.delete_item('red', self.table_red, self.clear_red_inputs))
        self.btn_del_cctv_recorder.clicked.connect(lambda: self.delete_item('cctv_recorders', self.table_cctv_recorders, self.clear_recorder_inputs))
        self.btn_del_cctv_camera.clicked.connect(lambda: self.delete_item('cctv_cameras', self.table_cctv_cameras, self.clear_camera_inputs))
        self.btn_del_acceso.clicked.connect(lambda: self.delete_item('accesos', self.table_accesos, self.clear_acceso_inputs))
        self.btn_del_software.clicked.connect(lambda: self.delete_item('software', self.table_software, self.clear_software_inputs))
        self.btn_del_credencial.clicked.connect(lambda: self.delete_item('credenciales', self.table_credenciales, self.clear_credencial_inputs))
        
        self.table_pcs.cellDoubleClicked.connect(self.edit_pc)
        self.table_proyectores.cellDoubleClicked.connect(self.edit_proyector)
        self.table_impresoras.cellDoubleClicked.connect(self.edit_impresora)
        self.table_servidores.cellDoubleClicked.connect(self.edit_servidor)
        self.table_red.cellDoubleClicked.connect(self.edit_red)
        self.table_cctv_recorders.cellDoubleClicked.connect(self.edit_recorder)
        self.table_cctv_cameras.cellDoubleClicked.connect(self.edit_camera)
        self.table_accesos.cellDoubleClicked.connect(self.edit_acceso)
        self.table_software.cellDoubleClicked.connect(self.edit_software)
        self.table_credenciales.cellDoubleClicked.connect(self.edit_credencial)

    def load_selected_inventory(self):
        data = self.db.fetch_one("SELECT * FROM inventarios WHERE id=?", (self.current_inventory_id,))
        if data:
            self.input_cliente.setText(data[1])
            self.input_ubicacion.setText(data[2])
            self.input_responsable.setText(data[3])
            self.date_fecha.setDate(QDate.fromString(data[4], "dd/MM/yyyy"))
            self.text_estructura.setPlainText(data[5])
            self.text_ubicacion_manuales.setPlainText(data[6])
            self.text_historico.setPlainText(data[7])
            self.text_modo_trabajo.setPlainText(data[8])
            self.text_equipos_extra.setPlainText(data[9])
            self.label_plano_path.setText(data[10])
            self.setWindowTitle(f"Inventario - {data[1]}")
            
            self.refresh_all_tables()

    def save_general_info(self):
        data = (
            self.input_cliente.text(), self.input_ubicacion.text(), self.input_responsable.text(),
            self.date_fecha.date().toString("dd/MM/yyyy"), self.text_estructura.toPlainText(),
            self.text_ubicacion_manuales.toPlainText(), self.text_historico.toPlainText(),
            self.text_modo_trabajo.toPlainText(), self.text_equipos_extra.toPlainText(),
            self.label_plano_path.text()
        )
        query = """UPDATE inventarios SET cliente=?, ubicacion=?, responsable=?, fecha=?,
                   estructura_info=?, ubicacion_manuales=?, historico_problemas=?, modo_trabajo=?,
                   equipos_extra=?, plano_path=? WHERE id=?"""
        self.db.execute_query(query, data + (self.current_inventory_id,))
        self.setWindowTitle(f"Inventario - {data[0]}")
        QMessageBox.information(self, "Éxito", "Información general actualizada.")

    def select_plano(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Seleccionar Plano", "", "Images (*.png *.xpm *.jpg *.jpeg)")
        if filename:
            self.label_plano_path.setText(filename)
    
    def refresh_all_tables(self):
        self.refresh_table('pcs', self.table_pcs, ['ID', 'Código', 'Placa', 'RAM', 'Core', 'Disco', 'S.O.', 'Fuente', 'Antivirus', 'Ubicación', 'Obs.'])
        self.refresh_table('proyectores', self.table_proyectores, ['ID', 'Código', 'Modelo', 'Táctil', 'Ubicación', 'Obs.'])
        self.refresh_table('impresoras', self.table_impresoras, ['ID', 'Código', 'Modelo', 'Conexión', 'Ubicación', 'Obs.'])
        self.refresh_table('servidores', self.table_servidores, ['ID', 'Código', 'Modelo', 'Uso', 'Ubicación', 'Obs.'])
        self.refresh_table('red', self.table_red, ['ID', 'Código', 'Tipo', 'Modelo', 'Ubicación', 'Obs.'])
        self.refresh_table('cctv_recorders', self.table_cctv_recorders, ['ID', 'Marca', 'Modelo', 'Canales', 'Ubicación', 'Obs.'])
        self.refresh_table('cctv_cameras', self.table_cctv_cameras, ['ID', 'Marca', 'Modelo', 'Lente', 'Ubicación', 'Obs.'])
        self.refresh_table('accesos', self.table_accesos, ['ID', 'Marca', 'Modelo', 'Tipo', 'Ubicación', 'Obs.'])
        self.refresh_table('software', self.table_software, ['ID', 'Software', 'Licencia'])
        self.refresh_table('credenciales', self.table_credenciales, ['ID', 'Elemento', 'Usuario', 'Contraseña', 'Notas'])

    def refresh_table(self, table_name, table_widget, headers):
        table_widget.setRowCount(0)
        table_widget.setColumnCount(len(headers))
        table_widget.setHorizontalHeaderLabels(headers)
        data = self.db.fetch_all(f"SELECT * FROM {table_name} WHERE inventario_id=?", (self.current_inventory_id,))
        for row_num, row_data in enumerate(data):
            table_widget.insertRow(row_num)
            for col_num, col_data in enumerate(row_data):
                item = QTableWidgetItem(str(col_data))
                table_widget.setItem(row_num, col_num, item)
        table_widget.resizeColumnsToContents()
        table_widget.setColumnHidden(0, True)

    def delete_item(self, table_name, table_widget, clear_func):
        selected_row = table_widget.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Selección requerida", "Por favor, seleccione un elemento de la tabla para eliminar.")
            return

        reply = QMessageBox.question(self, 'Confirmar eliminación', 
                                     "¿Está seguro de que desea eliminar este elemento?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            item_id = table_widget.item(selected_row, 0).text()
            self.db.execute_query(f"DELETE FROM {table_name} WHERE id=?", (item_id,))
            table_widget.removeRow(selected_row)
            clear_func()
            QMessageBox.information(self, "Éxito", "Elemento eliminado.")

    # --- SECCIÓN PC ---
    def clear_pc_inputs(self):
        self.editing_pc_id = None
        self.input_pc_codigo.clear(); self.input_pc_placa.clear(); self.input_pc_ram.clear()
        self.input_pc_core.clear(); self.input_pc_disco.clear(); self.input_pc_so.clear()
        self.input_pc_fuente.clear(); self.input_pc_antivirus.clear(); self.input_pc_ubicacion.clear()
        self.input_pc_obs.clear()

    def edit_pc(self, row, _):
        pc_id = self.table_pcs.item(row, 0).text()
        data = self.db.fetch_one("SELECT * FROM pcs WHERE id = ?", (pc_id,))
        if data:
            self.editing_pc_id = data[0]
            self.input_pc_codigo.setText(data[2]); self.input_pc_placa.setText(data[3]); self.input_pc_ram.setText(data[4])
            self.input_pc_core.setText(data[5]); self.input_pc_disco.setText(data[6]); self.input_pc_so.setText(data[7])
            self.input_pc_fuente.setText(data[8]); self.input_pc_antivirus.setText(data[9]); self.input_pc_ubicacion.setText(data[10])
            self.input_pc_obs.setText(data[11])
    
    def save_pc(self):
        data_tuple = (
            self.input_pc_codigo.text(), self.input_pc_placa.text(), self.input_pc_ram.text(), self.input_pc_core.text(),
            self.input_pc_disco.text(), self.input_pc_so.text(), self.input_pc_fuente.text(), self.input_pc_antivirus.text(),
            self.input_pc_ubicacion.text(), self.input_pc_obs.text()
        )
        if self.editing_pc_id is None:
            query = "INSERT INTO pcs (inventario_id, codigo, placa, ram, core, disco, so, fuente, antivirus, ubicacion_equipo, observaciones) VALUES (?,?,?,?,?,?,?,?,?,?,?)"
            self.db.execute_query(query, (self.current_inventory_id,) + data_tuple)
        else:
            query = "UPDATE pcs SET codigo=?, placa=?, ram=?, core=?, disco=?, so=?, fuente=?, antivirus=?, ubicacion_equipo=?, observaciones=? WHERE id=?"
            self.db.execute_query(query, data_tuple + (self.editing_pc_id,))
        self.refresh_table('pcs', self.table_pcs, ['ID', 'Código', 'Placa', 'RAM', 'Core', 'Disco', 'S.O.', 'Fuente', 'Antivirus', 'Ubicación', 'Obs.'])
        self.clear_pc_inputs()

    # --- SECCIÓN PROYECTOR ---
    def clear_proyector_inputs(self):
        self.editing_proy_id = None
        self.input_proy_codigo.clear(); self.input_proy_modelo.clear(); self.combo_proy_tactil.setCurrentIndex(0)
        self.input_proy_ubicacion.clear(); self.input_proy_obs.clear()
        
    def edit_proyector(self, row, _):
        proy_id = self.table_proyectores.item(row, 0).text()
        data = self.db.fetch_one("SELECT * FROM proyectores WHERE id=?", (proy_id,))
        if data:
            self.editing_proy_id = data[0]
            self.input_proy_codigo.setText(data[2]); self.input_proy_modelo.setText(data[3]); 
            self.combo_proy_tactil.setCurrentText(data[4]); self.input_proy_ubicacion.setText(data[5]); self.input_proy_obs.setText(data[6])

    def save_proyector(self):
        data_tuple = (self.input_proy_codigo.text(), self.input_proy_modelo.text(), self.combo_proy_tactil.currentText(), self.input_proy_ubicacion.text(), self.input_proy_obs.text())
        if self.editing_proy_id is None:
            self.db.execute_query("INSERT INTO proyectores (inventario_id, codigo, modelo, tactil, ubicacion_equipo, observaciones) VALUES (?,?,?,?,?,?)", (self.current_inventory_id,) + data_tuple)
        else:
            self.db.execute_query("UPDATE proyectores SET codigo=?, modelo=?, tactil=?, ubicacion_equipo=?, observaciones=? WHERE id=?", data_tuple + (self.editing_proy_id,))
        self.refresh_table('proyectores', self.table_proyectores, ['ID', 'Código', 'Modelo', 'Táctil', 'Ubicación', 'Obs.'])
        self.clear_proyector_inputs()
    
    # --- SECCIÓN IMPRESORA ---
    def clear_impresora_inputs(self):
        self.editing_imp_id = None
        self.input_imp_codigo.clear(); self.input_imp_modelo.clear(); self.combo_imp_conexion.setCurrentIndex(0)
        self.input_imp_ubicacion.clear(); self.input_imp_obs.clear()

    def edit_impresora(self, row, _):
        imp_id = self.table_impresoras.item(row, 0).text()
        data = self.db.fetch_one("SELECT * FROM impresoras WHERE id=?", (imp_id,))
        if data:
            self.editing_imp_id = data[0]
            self.input_imp_codigo.setText(data[2]); self.input_imp_modelo.setText(data[3]);
            self.combo_imp_conexion.setCurrentText(data[4]); self.input_imp_ubicacion.setText(data[5]); self.input_imp_obs.setText(data[6])

    def save_impresora(self):
        data_tuple = (self.input_imp_codigo.text(), self.input_imp_modelo.text(), self.combo_imp_conexion.currentText(), self.input_imp_ubicacion.text(), self.input_imp_obs.text())
        if self.editing_imp_id is None:
            self.db.execute_query("INSERT INTO impresoras (inventario_id, codigo, modelo, conexion, ubicacion_equipo, observaciones) VALUES (?,?,?,?,?,?)", (self.current_inventory_id,) + data_tuple)
        else:
            self.db.execute_query("UPDATE impresoras SET codigo=?, modelo=?, conexion=?, ubicacion_equipo=?, observaciones=? WHERE id=?", data_tuple + (self.editing_imp_id,))
        self.refresh_table('impresoras', self.table_impresoras, ['ID', 'Código', 'Modelo', 'Conexión', 'Ubicación', 'Obs.'])
        self.clear_impresora_inputs()

    # --- SECCIÓN SERVIDOR ---
    def clear_servidor_inputs(self):
        self.editing_srv_id = None
        self.input_srv_codigo.clear(); self.input_srv_modelo.clear(); self.input_srv_uso.clear()
        self.input_srv_ubicacion.clear(); self.input_srv_obs.clear()
        
    def edit_servidor(self, row, _):
        srv_id = self.table_servidores.item(row, 0).text()
        data = self.db.fetch_one("SELECT * FROM servidores WHERE id=?", (srv_id,))
        if data:
            self.editing_srv_id = data[0]
            self.input_srv_codigo.setText(data[2]); self.input_srv_modelo.setText(data[3]);
            self.input_srv_uso.setText(data[4]); self.input_srv_ubicacion.setText(data[5]); self.input_srv_obs.setText(data[6])

    def save_servidor(self):
        data_tuple = (self.input_srv_codigo.text(), self.input_srv_modelo.text(), self.input_srv_uso.text(), self.input_srv_ubicacion.text(), self.input_srv_obs.text())
        if self.editing_srv_id is None:
            self.db.execute_query("INSERT INTO servidores (inventario_id, codigo, modelo, uso, ubicacion_equipo, observaciones) VALUES (?,?,?,?,?,?)", (self.current_inventory_id,) + data_tuple)
        else:
            self.db.execute_query("UPDATE servidores SET codigo=?, modelo=?, uso=?, ubicacion_equipo=?, observaciones=? WHERE id=?", data_tuple + (self.editing_srv_id,))
        self.refresh_table('servidores', self.table_servidores, ['ID', 'Código', 'Modelo', 'Uso', 'Ubicación', 'Obs.'])
        self.clear_servidor_inputs()

    # --- SECCIÓN RED ---
    def clear_red_inputs(self):
        self.editing_red_id = None
        self.input_red_codigo.clear(); self.combo_red_tipo.setCurrentIndex(0); self.input_red_modelo.clear()
        self.input_red_ubicacion.clear(); self.input_red_obs.clear()
        
    def edit_red(self, row, _):
        red_id = self.table_red.item(row, 0).text()
        data = self.db.fetch_one("SELECT * FROM red WHERE id=?", (red_id,))
        if data:
            self.editing_red_id = data[0]
            self.input_red_codigo.setText(data[2]); self.combo_red_tipo.setCurrentText(data[3]);
            self.input_red_modelo.setText(data[4]); self.input_red_ubicacion.setText(data[5]); self.input_red_obs.setText(data[6])

    def save_red(self):
        data_tuple = (self.input_red_codigo.text(), self.combo_red_tipo.currentText(), self.input_red_modelo.text(), self.input_red_ubicacion.text(), self.input_red_obs.text())
        if self.editing_red_id is None:
            self.db.execute_query("INSERT INTO red (inventario_id, codigo, tipo, modelo, ubicacion_equipo, observaciones) VALUES (?,?,?,?,?,?)", (self.current_inventory_id,) + data_tuple)
        else:
            self.db.execute_query("UPDATE red SET codigo=?, tipo=?, modelo=?, ubicacion_equipo=?, observaciones=? WHERE id=?", data_tuple + (self.editing_red_id,))
        self.refresh_table('red', self.table_red, ['ID', 'Código', 'Tipo', 'Modelo', 'Ubicación', 'Obs.'])
        self.clear_red_inputs()

    # --- SECCIÓN CCTV GRABADOR ---
    def clear_recorder_inputs(self):
        self.editing_recorder_id = None
        self.input_cctv_rec_marca.clear(); self.input_cctv_rec_modelo.clear(); self.input_cctv_rec_canales.clear()
        self.input_cctv_rec_ubicacion.clear(); self.input_cctv_rec_obs.clear()
        
    def edit_recorder(self, row, _):
        rec_id = self.table_cctv_recorders.item(row, 0).text()
        data = self.db.fetch_one("SELECT * FROM cctv_recorders WHERE id=?", (rec_id,))
        if data:
            self.editing_recorder_id = data[0]
            self.input_cctv_rec_marca.setText(data[2]); self.input_cctv_rec_modelo.setText(data[3]);
            self.input_cctv_rec_canales.setText(data[4]); self.input_cctv_rec_ubicacion.setText(data[5]); self.input_cctv_rec_obs.setText(data[6])

    def save_recorder(self):
        data_tuple = (self.input_cctv_rec_marca.text(), self.input_cctv_rec_modelo.text(), self.input_cctv_rec_canales.text(), self.input_cctv_rec_ubicacion.text(), self.input_cctv_rec_obs.text())
        if self.editing_recorder_id is None:
            self.db.execute_query("INSERT INTO cctv_recorders (inventario_id, marca, modelo, canales, ubicacion, observaciones) VALUES (?,?,?,?,?,?)", (self.current_inventory_id,) + data_tuple)
        else:
            self.db.execute_query("UPDATE cctv_recorders SET marca=?, modelo=?, canales=?, ubicacion=?, observaciones=? WHERE id=?", data_tuple + (self.editing_recorder_id,))
        self.refresh_table('cctv_recorders', self.table_cctv_recorders, ['ID', 'Marca', 'Modelo', 'Canales', 'Ubicación', 'Obs.'])
        self.clear_recorder_inputs()

    # --- SECCIÓN CCTV CÁMARA ---
    def clear_camera_inputs(self):
        self.editing_camera_id = None
        self.input_cctv_cam_marca.clear(); self.input_cctv_cam_modelo.clear(); self.input_cctv_cam_lente.clear()
        self.input_cctv_cam_ubicacion.clear(); self.input_cctv_cam_obs.clear()

    def edit_camera(self, row, _):
        cam_id = self.table_cctv_cameras.item(row, 0).text()
        data = self.db.fetch_one("SELECT * FROM cctv_cameras WHERE id=?", (cam_id,))
        if data:
            self.editing_camera_id = data[0]
            self.input_cctv_cam_marca.setText(data[2]); self.input_cctv_cam_modelo.setText(data[3]);
            self.input_cctv_cam_lente.setText(data[4]); self.input_cctv_cam_ubicacion.setText(data[5]); self.input_cctv_cam_obs.setText(data[6])

    def save_camera(self):
        data_tuple = (self.input_cctv_cam_marca.text(), self.input_cctv_cam_modelo.text(), self.input_cctv_cam_lente.text(), self.input_cctv_cam_ubicacion.text(), self.input_cctv_cam_obs.text())
        if self.editing_camera_id is None:
            self.db.execute_query("INSERT INTO cctv_cameras (inventario_id, marca, modelo, tipo_lente, ubicacion, observaciones) VALUES (?,?,?,?,?,?)", (self.current_inventory_id,) + data_tuple)
        else:
            self.db.execute_query("UPDATE cctv_cameras SET marca=?, modelo=?, tipo_lente=?, ubicacion=?, observaciones=? WHERE id=?", data_tuple + (self.editing_camera_id,))
        self.refresh_table('cctv_cameras', self.table_cctv_cameras, ['ID', 'Marca', 'Modelo', 'Lente', 'Ubicación', 'Obs.'])
        self.clear_camera_inputs()

    # --- SECCIÓN CONTROL ACCESO ---
    def clear_acceso_inputs(self):
        self.editing_acceso_id = None
        self.input_acceso_marca.clear(); self.input_acceso_modelo.clear(); self.combo_acceso_tipo.setCurrentIndex(0)
        self.input_acceso_ubicacion.clear(); self.input_acceso_obs.clear()

    def edit_acceso(self, row, _):
        acceso_id = self.table_accesos.item(row, 0).text()
        data = self.db.fetch_one("SELECT * FROM accesos WHERE id=?", (acceso_id,))
        if data:
            self.editing_acceso_id = data[0]
            self.input_acceso_marca.setText(data[2]); self.input_acceso_modelo.setText(data[3]);
            self.combo_acceso_tipo.setCurrentText(data[4]); self.input_acceso_ubicacion.setText(data[5]); self.input_acceso_obs.setText(data[6])

    def save_acceso(self):
        data_tuple = (self.input_acceso_marca.text(), self.input_acceso_modelo.text(), self.combo_acceso_tipo.currentText(), self.input_acceso_ubicacion.text(), self.input_acceso_obs.text())
        if self.editing_acceso_id is None:
            self.db.execute_query("INSERT INTO accesos (inventario_id, marca, modelo, tipo, ubicacion, observaciones) VALUES (?,?,?,?,?,?)", (self.current_inventory_id,) + data_tuple)
        else:
            self.db.execute_query("UPDATE accesos SET marca=?, modelo=?, tipo=?, ubicacion=?, observaciones=? WHERE id=?", data_tuple + (self.editing_acceso_id,))
        self.refresh_table('accesos', self.table_accesos, ['ID', 'Marca', 'Modelo', 'Tipo', 'Ubicación', 'Obs.'])
        self.clear_acceso_inputs()

    # --- SECCIÓN SOFTWARE ---
    def clear_software_inputs(self):
        self.editing_sw_id = None
        self.input_sw_nombre.clear(); self.input_sw_licencia.clear()

    def edit_software(self, row, _):
        sw_id = self.table_software.item(row, 0).text()
        data = self.db.fetch_one("SELECT * FROM software WHERE id=?", (sw_id,))
        if data:
            self.editing_sw_id = data[0]
            self.input_sw_nombre.setText(data[2]); self.input_sw_licencia.setText(data[3])

    def save_software(self):
        data_tuple = (self.input_sw_nombre.text(), self.input_sw_licencia.text())
        if self.editing_sw_id is None:
            self.db.execute_query("INSERT INTO software (inventario_id, nombre, licencia) VALUES (?,?,?)", (self.current_inventory_id,) + data_tuple)
        else:
            self.db.execute_query("UPDATE software SET nombre=?, licencia=? WHERE id=?", data_tuple + (self.editing_sw_id,))
        self.refresh_table('software', self.table_software, ['ID', 'Software', 'Licencia'])
        self.clear_software_inputs()

    # --- SECCIÓN CREDENCIALES ---
    def clear_credencial_inputs(self):
        self.editing_cred_id = None
        self.input_cred_elemento.clear(); self.input_cred_usuario.clear()
        self.input_cred_clave.clear(); self.input_cred_notas.clear()
    
    def edit_credencial(self, row, _):
        cred_id = self.table_credenciales.item(row, 0).text()
        data = self.db.fetch_one("SELECT * FROM credenciales WHERE id=?", (cred_id,))
        if data:
            self.editing_cred_id = data[0]
            self.input_cred_elemento.setText(data[2]); self.input_cred_usuario.setText(data[3])
            self.input_cred_clave.setText(data[4]); self.input_cred_notas.setText(data[5])
            
    def save_credencial(self):
        data_tuple = (self.input_cred_elemento.text(), self.input_cred_usuario.text(), self.input_cred_clave.text(), self.input_cred_notas.text())
        if self.editing_cred_id is None:
            self.db.execute_query("INSERT INTO credenciales (inventario_id, elemento, usuario, clave, notas) VALUES (?,?,?,?,?)", (self.current_inventory_id,) + data_tuple)
        else:
            self.db.execute_query("UPDATE credenciales SET elemento=?, usuario=?, clave=?, notas=? WHERE id=?", data_tuple + (self.editing_cred_id,))
        self.refresh_table('credenciales', self.table_credenciales, ['ID', 'Elemento', 'Usuario', 'Contraseña', 'Notas'])
        self.clear_credencial_inputs()

    # --- Exportación ---
    def export_to_pdf(self):
        inv_data = self.db.fetch_one("SELECT * FROM inventarios WHERE id=?", (self.current_inventory_id,))
        if not inv_data:
            QMessageBox.warning(self, "Error", "No se encontró información del inventario.")
            return

        pdf_data = {
            "cliente": inv_data[1], "ubicacion": inv_data[2], "responsable": inv_data[3], "fecha": inv_data[4],
            "estructura_info": inv_data[5] or "", "ubicacion_manuales": inv_data[6] or "", 
            "historico_problemas": inv_data[7] or "", "modo_trabajo": inv_data[8] or "", 
            "equipos_extra": inv_data[9] or "", "plano_path": inv_data[10] or "",
            "pcs": self.db.fetch_all("SELECT * FROM pcs WHERE inventario_id=?", (self.current_inventory_id,)),
            "proyectores": self.db.fetch_all("SELECT * FROM proyectores WHERE inventario_id=?", (self.current_inventory_id,)),
            "impresoras": self.db.fetch_all("SELECT * FROM impresoras WHERE inventario_id=?", (self.current_inventory_id,)),
            "servidores": self.db.fetch_all("SELECT * FROM servidores WHERE inventario_id=?", (self.current_inventory_id,)),
            "red": self.db.fetch_all("SELECT * FROM red WHERE inventario_id=?", (self.current_inventory_id,)),
            "cctv_recorders": self.db.fetch_all("SELECT * FROM cctv_recorders WHERE inventario_id=?", (self.current_inventory_id,)),
            "cctv_cameras": self.db.fetch_all("SELECT * FROM cctv_cameras WHERE inventario_id=?", (self.current_inventory_id,)),
            "accesos": self.db.fetch_all("SELECT * FROM accesos WHERE inventario_id=?", (self.current_inventory_id,)),
            "software": self.db.fetch_all("SELECT * FROM software WHERE inventario_id=?", (self.current_inventory_id,)),
            "credenciales": self.db.fetch_all("SELECT * FROM credenciales WHERE inventario_id=?", (self.current_inventory_id,))
        }

        filename, _ = QFileDialog.getSaveFileName(self, "Guardar PDF", f"Auditoria_{pdf_data['cliente']}.pdf", "PDF Files (*.pdf)")
        if filename:
            try:
                generate_pdf(filename, pdf_data)
                QMessageBox.information(self, "Éxito", f"PDF generado correctamente en:\n{filename}")
            except Exception as e:
                QMessageBox.critical(self, "Error de Exportación", f"No se pudo generar el PDF. Error: {e}")

# --- Bucle principal de la aplicación ---
class App(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        self.db = DatabaseManager()
        self.main_window = None
        self.should_switch_user = False

    def run(self):
        while True:
            self.should_switch_user = False
            login = LoginDialog(self.db)
            
            if not login.exec():
                break

            inventory_id = login.selected_inventory_id
            # --- CORRECCIÓN AQUÍ ---
            # Pasamos 'self' como la instancia de la app.
            self.main_window = MainWindow(inventory_id, app_instance=self)
            # --- FIN DE LA CORRECCIÓN ---
            self.main_window.show()
            self.exec()
            
            if not self.should_switch_user:
                break
        
        self.db.close()
        return 0

if __name__ == "__main__":
    app = App(sys.argv)
    sys.exit(app.run())