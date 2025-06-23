# main.py
import sys
import os
import sqlite3
import shutil
import subprocess
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTableWidgetItem, QMessageBox, 
                             QFileDialog, QDialog, QLabel, QFormLayout, QWidget,
                             QListWidgetItem, QListWidget, QComboBox)
from PyQt6.uic import loadUi
from PyQt6.QtCore import QDate, Qt, QSize
from PyQt6.QtGui import QIcon, QAction, QPixmap
from database import DatabaseManager
from pdf_generator import generate_pdf
from excel_generator import generate_excel

# --- Funciones Auxiliares para manejo de rutas ---

def is_frozen():
    """ Devuelve True si la aplicación está 'congelada' (es un EXE) """
    return getattr(sys, 'frozen', False)

def get_base_path():
    """ Obtiene la ruta base para leer recursos (funciona en dev y EXE) """
    if is_frozen():
        # Ruta al directorio temporal _MEIPASS creado por PyInstaller
        return sys._MEIPASS
    else:
        # Ruta al directorio del script
        return os.path.dirname(os.path.abspath(__file__))

def get_writable_data_path(relative_path=''):
    """ Obtiene una ruta en un directorio donde se puede escribir, al lado del EXE o script """
    if is_frozen():
        # Ruta al directorio donde está el .exe
        base_path = os.path.dirname(sys.executable)
    else:
        # Ruta al directorio del script
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

# --- Ventana de Login ---
class LoginDialog(QDialog):
    def __init__(self, db):
        super().__init__()
        loadUi(os.path.join(get_base_path(), "ui_login.ui"), self)
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

# --- Ventana de Visor de Detalles ---
class DetailViewDialog(QDialog):
    def __init__(self, item_type, item_id, db, parent=None):
        super().__init__(parent)
        loadUi(os.path.join(get_base_path(), "detail_view_dialog.ui"), self)
        self.item_type = item_type
        self.item_id = item_id
        self.db = db
        self.main_window = parent

        self.image_dir = get_writable_data_path(os.path.join('data', 'images'))
        os.makedirs(self.image_dir, exist_ok=True)
        
        self.populate_details()
        self.load_images()

        self.btn_close.clicked.connect(self.accept)
        self.btn_edit_item.clicked.connect(self.request_edit)
        self.btn_delete_item.clicked.connect(self.request_delete)
        self.btn_add_image.clicked.connect(self.add_images)
        self.btn_delete_image.clicked.connect(self.delete_image)
        self.image_list_widget.itemDoubleClicked.connect(self.view_image)

    def populate_details(self):
        data = self.db.fetch_one(f"SELECT * FROM {self.item_type} WHERE id=?", (self.item_id,))
        if not data:
            self.close()
            return
        
        cursor = self.db.execute_query(f"SELECT * FROM {self.item_type} WHERE id=?", (self.item_id,))
        headers = [desc[0] for desc in cursor.description]
        
        while self.info_layout.count():
            child = self.info_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        for header, value in zip(headers[2:], data[2:]):
            label_header = QLabel(f"<b>{header.replace('_', ' ').title()}:</b>")
            label_value = QLabel(str(value))
            label_value.setWordWrap(True)
            self.info_layout.addRow(label_header, label_value)

    def load_images(self):
        self.image_list_widget.clear()
        self.image_list_widget.setIconSize(QSize(128, 128))
        self.image_list_widget.setViewMode(QListWidget.ViewMode.IconMode)
        self.image_list_widget.setResizeMode(QListWidget.ResizeMode.Adjust)

        images = self.db.fetch_all("SELECT id, image_path FROM images WHERE item_type=? AND item_id=?", (self.item_type, self.item_id))
        for img_id, relative_img_path in images:
            full_path = get_writable_data_path(relative_img_path)
            if os.path.exists(full_path):
                pixmap = QPixmap(full_path)
                icon = QIcon(pixmap)
                item = QListWidgetItem(icon, os.path.basename(full_path))
                item.setData(Qt.ItemDataRole.UserRole, (img_id, full_path, relative_img_path))
                self.image_list_widget.addItem(item)
    def add_images(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Seleccionar Imágenes", "", "Images (*.png *.jpg *.jpeg)")
        for file_path in files:
            filename = f"{self.item_type}_{self.item_id}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}{os.path.splitext(file_path)[1]}"
            destination_path = os.path.join(self.image_dir, filename)
            
            try:
                shutil.copy(file_path, destination_path)
                relative_path_to_save = os.path.join('data', 'images', filename)
                self.db.execute_query("INSERT INTO images (item_type, item_id, image_path) VALUES (?, ?, ?)", 
                                      (self.item_type, self.item_id, relative_path_to_save))
            except Exception as e:
                QMessageBox.critical(self, "Error al copiar", f"No se pudo guardar la imagen: {e}")
        
        self.load_images()

    def delete_image(self):
        selected_items = self.image_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Selección requerida", "Por favor, seleccione una imagen para eliminar.")
            return
        
        item = selected_items[0]
        img_id, full_path, _ = item.data(Qt.ItemDataRole.UserRole)

        reply = QMessageBox.question(self, 'Confirmar eliminación', 
                                     f"¿Está seguro de que desea eliminar la imagen '{os.path.basename(full_path)}'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            try:
                if os.path.exists(full_path):
                    os.remove(full_path)
                self.db.execute_query("DELETE FROM images WHERE id=?", (img_id,))
                self.load_images()
                QMessageBox.information(self, "Éxito", "Imagen eliminada.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo eliminar la imagen: {e}")

    def view_image(self, item):
        _, full_path, _ = item.data(Qt.ItemDataRole.UserRole)
        try:
            if sys.platform == "win32":
                os.startfile(full_path)
            elif sys.platform == "darwin":
                subprocess.call(["open", full_path])
            else:
                subprocess.call(["xdg-open", full_path])
        except Exception as e:
             QMessageBox.critical(self, "Error", f"No se pudo abrir la imagen: {e}")

    def request_edit(self):
        self.main_window.prepare_to_edit(self.item_type, self.item_id)
        self.accept()

    def request_delete(self):
        self.main_window.request_delete_from_viewer(self.item_type, self.item_id)
        self.accept()

# --- Ventana de Búsqueda ---
class SearchDialog(QDialog):
    def __init__(self, db, inventory_id, parent=None):
        super().__init__(parent)
        loadUi(os.path.join(get_base_path(), "search_dialog.ui"), self)
        self.db = db
        self.inventory_id = inventory_id
        self.main_window = parent
        self.all_items = []
        
        self.load_all_items()
        
        self.search_input.textChanged.connect(self.filter_results)
        self.results_list.itemDoubleClicked.connect(self.open_detail_view)
        self.btn_close.clicked.connect(self.accept)

    def load_all_items(self):
        self.all_items = []
        tables_to_search = {
            'pcs': ['PCs', 'codigo', 'placa', 'ubicacion_equipo'],
            'proyectores': ['Proyectores', 'codigo', 'modelo', 'ubicacion_equipo'],
            'impresoras': ['Impresoras', 'codigo', 'modelo', 'ubicacion_equipo'],
            'servidores': ['Servidores', 'codigo', 'modelo', 'uso'],
            'red': ['Red', 'codigo', 'tipo', 'modelo', 'ubicacion_equipo'],
            'cctv_recorders': ['Grabadores CCTV', 'marca', 'modelo', 'ubicacion'],
            'cctv_cameras': ['Cámaras CCTV', 'marca', 'modelo', 'ubicacion'],
            'accesos': ['Control de Acceso', 'marca', 'modelo', 'ubicacion'],
            'software': ['Software', 'nombre', 'licencia'],
            'credenciales': ['Credenciales', 'elemento', 'usuario'],
        }

        for table_name, fields in tables_to_search.items():
            display_name = fields[0]
            query_fields = ", ".join(fields[1:])
            query = f"SELECT id, {query_fields} FROM {table_name} WHERE inventario_id=?"
            results = self.db.fetch_all(query, (self.inventory_id,))
            for row in results:
                item_id = row[0]
                display_text = f"[{display_name}] " + " - ".join(map(str, row[1:]))
                searchable_text = display_text.lower()
                self.all_items.append((table_name, item_id, display_text, searchable_text))
        
        self.filter_results()

    def filter_results(self):
        search_term = self.search_input.text().lower()
        self.results_list.clear()
        
        if not search_term:
            for table_name, item_id, display_text, _ in self.all_items:
                item = QListWidgetItem(display_text)
                item.setData(Qt.ItemDataRole.UserRole, (table_name, item_id))
                self.results_list.addItem(item)
        else:
            for table_name, item_id, display_text, searchable_text in self.all_items:
                if search_term in searchable_text:
                    item = QListWidgetItem(display_text)
                    item.setData(Qt.ItemDataRole.UserRole, (table_name, item_id))
                    self.results_list.addItem(item)
    
    def open_detail_view(self, item):
        table_name, item_id = item.data(Qt.ItemDataRole.UserRole)
        self.main_window.open_detail_view(table_name, item_id)

# --- Ventana Principal ---
class MainWindow(QMainWindow):
    def __init__(self, inventory_id, app_instance=None):
        super(MainWindow, self).__init__()
        self.app_instance = app_instance
        
        loadUi(os.path.join(get_base_path(), "ui_inventario.ui"), self)
        
        self.db = DatabaseManager()
        self.current_inventory_id = inventory_id
        
        self.editing_item_id = None
        self.editing_item_type = None

        self.table_map = {
            'pcs': {
                'widget': self.table_pcs,
                'headers': ['ID', 'Código', 'Placa', 'RAM', 'Core', 'Disco', 'S.O.', 'Fuente', 'Antivirus', 'Ubicación', 'Obs.'],
                'db_cols': ['id', 'codigo', 'placa', 'ram', 'core', 'disco', 'so', 'fuente', 'antivirus', 'ubicacion_equipo', 'observaciones']
            },
            'proyectores': {
                'widget': self.table_proyectores,
                'headers': ['ID', 'Código', 'Modelo', 'Táctil', 'Ubicación', 'Obs.'],
                'db_cols': ['id', 'codigo', 'modelo', 'tactil', 'ubicacion_equipo', 'observaciones']
            },
            'impresoras': {
                'widget': self.table_impresoras,
                'headers': ['ID', 'Código', 'Modelo', 'Conexión', 'Ubicación', 'Obs.'],
                'db_cols': ['id', 'codigo', 'modelo', 'conexion', 'ubicacion_equipo', 'observaciones']
            },
            'servidores': {
                'widget': self.table_servidores,
                'headers': ['ID', 'Código', 'Modelo', 'Uso', 'Ubicación', 'Obs.'],
                'db_cols': ['id', 'codigo', 'modelo', 'uso', 'ubicacion_equipo', 'observaciones']
            },
            'red': {
                'widget': self.table_red,
                'headers': ['ID', 'Código', 'Tipo', 'Modelo', 'Ubicación', 'Obs.'],
                'db_cols': ['id', 'codigo', 'tipo', 'modelo', 'ubicacion_equipo', 'observaciones']
            },
            'cctv_recorders': {
                'widget': self.table_cctv_recorders,
                'headers': ['ID', 'Marca', 'Modelo', 'Canales', 'Ubicación', 'Obs.'],
                'db_cols': ['id', 'marca', 'modelo', 'canales', 'ubicacion', 'observaciones']
            },
            'cctv_cameras': {
                'widget': self.table_cctv_cameras,
                'headers': ['ID', 'Marca', 'Modelo', 'Lente', 'Ubicación', 'Obs.'],
                'db_cols': ['id', 'marca', 'modelo', 'tipo_lente', 'ubicacion', 'observaciones']
            },
            'accesos': {
                'widget': self.table_accesos,
                'headers': ['ID', 'Marca', 'Modelo', 'Tipo', 'Ubicación', 'Obs.'],
                'db_cols': ['id', 'marca', 'modelo', 'tipo', 'ubicacion', 'observaciones']
            },
            'software': {
                'widget': self.table_software,
                'headers': ['ID', 'Software', 'Licencia'],
                'db_cols': ['id', 'nombre', 'licencia']
            },
            'credenciales': {
                'widget': self.table_credenciales,
                'headers': ['ID', 'Elemento', 'Usuario', 'Contraseña', 'Notas'],
                'db_cols': ['id', 'elemento', 'usuario', 'clave', 'notas']
            }
        }

        self.setup_ui()
        self.connect_signals()
        self.load_selected_inventory()
    def setup_ui(self):
        for table_name in self.table_map:
            widget = self.table_map[table_name]['widget']
            widget.setEditTriggers(widget.EditTrigger.NoEditTriggers)
            widget.setColumnHidden(0, True)
        
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
        if self.app_instance:
            self.app_instance.should_switch_user = True
        self.close()

    def connect_signals(self):
        # Botones Globales
        self.btn_search.clicked.connect(self.open_search_dialog)
        self.btn_guardar_todo.clicked.connect(self.save_all_data)
        self.btn_exportar_excel.clicked.connect(self.export_to_excel)
        self.btn_exportar_pdf.clicked.connect(self.export_to_pdf)
        self.btn_select_plano.clicked.connect(self.select_plano)

        # Conexiones para GUARDAR (añadir/actualizar)
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

        # Conexiones para LIMPIAR CAMPOS
        self.btn_clear_pc.clicked.connect(self.clear_pcs_inputs)
        self.btn_clear_proyector.clicked.connect(self.clear_proyectores_inputs)
        self.btn_clear_impresora.clicked.connect(self.clear_impresoras_inputs)
        self.btn_clear_servidor.clicked.connect(self.clear_servidores_inputs)
        self.btn_clear_red.clicked.connect(self.clear_red_inputs)
        self.btn_clear_cctv_recorder.clicked.connect(self.clear_cctv_recorders_inputs)
        self.btn_clear_cctv_camera.clicked.connect(self.clear_cctv_cameras_inputs)
        self.btn_clear_acceso.clicked.connect(self.clear_accesos_inputs)
        self.btn_clear_software.clicked.connect(self.clear_software_inputs)
        self.btn_clear_credencial.clicked.connect(self.clear_credenciales_inputs)
        
        # Conexiones de DOBLE CLIC para ver detalles
        for table_name, table_info in self.table_map.items():
            table_info['widget'].cellDoubleClicked.connect(
                lambda row, col, name=table_name: self.open_detail_view_from_table(name, row)
            )

    def open_search_dialog(self):
        dialog = SearchDialog(self.db, self.current_inventory_id, self)
        dialog.exec()
        
    def open_detail_view_from_table(self, item_type, row):
        table_widget = self.table_map[item_type]['widget']
        item_id = table_widget.item(row, 0).text()
        self.open_detail_view(item_type, item_id)
        
    def open_detail_view(self, item_type, item_id):
        dialog = DetailViewDialog(item_type, item_id, self.db, self)
        dialog.exec()
        
    def prepare_to_edit(self, item_type, item_id):
        self.editing_item_type = item_type
        self.editing_item_id = item_id

        edit_map = {
            'pcs': (self.edit_pc, 1), 'proyectores': (self.edit_proyector, 2),
            'impresoras': (self.edit_impresora, 3), 'servidores': (self.edit_servidor, 4),
            'red': (self.edit_red, 4), 'cctv_recorders': (self.edit_recorder, 5),
            'cctv_cameras': (self.edit_camera, 5), 'accesos': (self.edit_acceso, 6),
            'software': (self.edit_software, 7), 'credenciales': (self.edit_credencial, 8)
        }
        
        if item_type in edit_map:
            edit_function, tab_index = edit_map[item_type]
            self.tabs_main.setCurrentIndex(tab_index)
            edit_function(item_id)

    def request_delete_from_viewer(self, item_type, item_id):
        clear_func_name = f"clear_{item_type}_inputs"
        clear_func = getattr(self, clear_func_name, lambda: None)
        table_widget = self.table_map[item_type]['widget']
        self.delete_item(item_type, item_id, table_widget, clear_func)

    def load_selected_inventory(self):
        data = self.db.fetch_one("SELECT * FROM inventarios WHERE id=?", (self.current_inventory_id,))
        if data:
            self.input_cliente.setText(data[1])
            self.input_ubicacion.setText(data[2])
            self.input_responsable.setText(data[3])
            try:
                self.date_fecha.setDate(QDate.fromString(data[4], "dd/MM/yyyy"))
            except:
                self.date_fecha.setDate(QDate.currentDate())
            self.text_estructura.setPlainText(data[5] or "")
            self.text_ubicacion_manuales.setPlainText(data[6] or "")
            self.text_historico.setPlainText(data[7] or "")
            self.text_modo_trabajo.setPlainText(data[8] or "")
            self.text_equipos_extra.setPlainText(data[9] or "")
            self.label_plano_path.setText(data[10] or "")
            self.setWindowTitle(f"Inventario - {data[1]}")
            
            self.populate_all_comboboxes()
            self.refresh_all_tables()

    def populate_combobox(self, combo_box, table, column):
        combo_box.blockSignals(True)
        current_text = combo_box.currentText()
        combo_box.clear()
        query = f"SELECT DISTINCT {column} FROM {table} WHERE {column} IS NOT NULL AND {column} != ''"
        items = self.db.fetch_all(query)
        unique_items = sorted(list(set([item[0] for item in items])))
        combo_box.addItems(unique_items)
        combo_box.setCurrentText(current_text)
        combo_box.blockSignals(False)
    
    def populate_all_comboboxes(self):
        self.populate_combobox(self.combo_pc_placa, 'pcs', 'placa')
        self.populate_combobox(self.combo_pc_ram, 'pcs', 'ram')
        self.populate_combobox(self.combo_pc_core, 'pcs', 'core')
        self.populate_combobox(self.combo_pc_disco, 'pcs', 'disco')
        self.populate_combobox(self.combo_pc_so, 'pcs', 'so')
        self.populate_combobox(self.combo_pc_fuente, 'pcs', 'fuente')
        self.populate_combobox(self.combo_pc_antivirus, 'pcs', 'antivirus')
        self.populate_combobox(self.combo_proy_modelo, 'proyectores', 'modelo')
        self.populate_combobox(self.combo_imp_modelo, 'impresoras', 'modelo')
        self.populate_combobox(self.combo_srv_modelo, 'servidores', 'modelo')
        self.populate_combobox(self.combo_red_modelo, 'red', 'modelo')
        self.populate_combobox(self.combo_cctv_rec_marca, 'cctv_recorders', 'marca')
        self.populate_combobox(self.combo_cctv_rec_modelo, 'cctv_recorders', 'modelo')
        self.populate_combobox(self.combo_cctv_cam_marca, 'cctv_cameras', 'marca')
        self.populate_combobox(self.combo_cctv_cam_modelo, 'cctv_cameras', 'modelo')
        self.populate_combobox(self.combo_cctv_cam_lente, 'cctv_cameras', 'tipo_lente')
        self.populate_combobox(self.combo_acceso_marca, 'accesos', 'marca')
        self.populate_combobox(self.combo_acceso_modelo, 'accesos', 'modelo')
        self.populate_combobox(self.combo_sw_nombre, 'software', 'nombre')
    def save_all_data(self):
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
        QMessageBox.information(self, "Éxito", "Toda la información general ha sido guardada.")

    def select_plano(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Seleccionar Plano", "", "Images (*.png *.xpm *.jpg *.jpeg)")
        if filename:
            self.label_plano_path.setText(filename)
    
    def refresh_all_tables(self):
        for table_name in self.table_map:
            self.refresh_table(table_name)

    def refresh_table(self, table_name):
        # CORRECCIÓN: Lógica de refresco robusta y explícita
        if table_name not in self.table_map:
            return
            
        table_info = self.table_map[table_name]
        table_widget = table_info['widget']
        headers = table_info['headers']
        db_cols = table_info['db_cols']

        table_widget.setRowCount(0)
        table_widget.setColumnCount(len(headers))
        table_widget.setHorizontalHeaderLabels(headers)
        
        # Construir la query pidiendo las columnas en el orden correcto
        query = f"SELECT {', '.join(db_cols)} FROM {table_name} WHERE inventario_id=?"
        data = self.db.fetch_all(query, (self.current_inventory_id,))
        
        for row_num, row_data in enumerate(data):
            table_widget.insertRow(row_num)
            for col_num, cell_data in enumerate(row_data):
                item = QTableWidgetItem(str(cell_data))
                table_widget.setItem(row_num, col_num, item)
                
        table_widget.resizeColumnsToContents()
        table_widget.setColumnHidden(0, True) # Ocultar la columna ID

    def delete_item(self, table_name, item_id, table_widget, clear_func):
        reply = QMessageBox.question(self, 'Confirmar eliminación', 
                                     "¿Está seguro de que desea eliminar este elemento y todas sus imágenes asociadas?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            images = self.db.fetch_all("SELECT image_path FROM images WHERE item_type=? AND item_id=?", (table_name, item_id))
            for (img_path,) in images:
                try:
                    full_path = get_writable_data_path(img_path)
                    if os.path.exists(full_path):
                        os.remove(full_path)
                except Exception as e:
                    print(f"No se pudo borrar el archivo de imagen {img_path}: {e}")
            self.db.execute_query("DELETE FROM images WHERE item_type=? AND item_id=?", (table_name, item_id))
            
            self.db.execute_query(f"DELETE FROM {table_name} WHERE id=?", (item_id,))
            
            self.refresh_table(table_name)
            self.populate_all_comboboxes()
            clear_func()
            QMessageBox.information(self, "Éxito", "Elemento eliminado.")

    def _save_item(self, item_type, data_tuple, insert_query, update_query):
        clear_func_name = f"clear_{item_type}_inputs"
        clear_func = getattr(self, clear_func_name)
        
        if self.editing_item_type == item_type and self.editing_item_id is not None:
            self.db.execute_query(update_query, data_tuple + (self.editing_item_id,))
        else:
            self.db.execute_query(insert_query, (self.current_inventory_id,) + data_tuple)
        
        self.refresh_table(item_type)
        self.populate_all_comboboxes()
        clear_func()
    
    def _get_combo_text(self, combo):
        return combo.currentText()

    # --- Métodos de edición, limpieza y guardado para cada tipo de item ---

    # --- PCs ---
    def edit_pc(self, item_id):
        data = self.db.fetch_one("SELECT * FROM pcs WHERE id = ?", (item_id,))
        if data:
            self.input_pc_codigo.setText(data[2]); self.combo_pc_placa.setCurrentText(data[3]); self.combo_pc_ram.setCurrentText(data[4])
            self.combo_pc_core.setCurrentText(data[5]); self.combo_pc_disco.setCurrentText(data[6]); self.combo_pc_so.setCurrentText(data[7])
            self.combo_pc_fuente.setCurrentText(data[8]); self.combo_pc_antivirus.setCurrentText(data[9]); self.input_pc_ubicacion.setText(data[10])
            self.input_pc_obs.setText(data[11])
            
    def clear_pcs_inputs(self):
        self.editing_item_id = None; self.editing_item_type = None
        self.input_pc_codigo.clear()
        self.combo_pc_placa.setCurrentText(""); self.combo_pc_ram.setCurrentText("")
        self.combo_pc_core.setCurrentText(""); self.combo_pc_disco.setCurrentText("")
        self.combo_pc_so.setCurrentText(""); self.combo_pc_fuente.setCurrentText("")
        self.combo_pc_antivirus.setCurrentText(""); self.input_pc_ubicacion.clear()
        self.input_pc_obs.clear()
        
    def save_pc(self):
        data_tuple = (
            self.input_pc_codigo.text(), self._get_combo_text(self.combo_pc_placa), self._get_combo_text(self.combo_pc_ram),
            self._get_combo_text(self.combo_pc_core), self._get_combo_text(self.combo_pc_disco), self._get_combo_text(self.combo_pc_so),
            self._get_combo_text(self.combo_pc_fuente), self._get_combo_text(self.combo_pc_antivirus),
            self.input_pc_ubicacion.text(), self.input_pc_obs.text()
        )
        insert_q = "INSERT INTO pcs (inventario_id, codigo, placa, ram, core, disco, so, fuente, antivirus, ubicacion_equipo, observaciones) VALUES (?,?,?,?,?,?,?,?,?,?,?)"
        update_q = "UPDATE pcs SET codigo=?, placa=?, ram=?, core=?, disco=?, so=?, fuente=?, antivirus=?, ubicacion_equipo=?, observaciones=? WHERE id=?"
        self._save_item('pcs', data_tuple, insert_q, update_q)
    
    # --- Proyectores ---
    def edit_proyector(self, item_id):
        data = self.db.fetch_one("SELECT * FROM proyectores WHERE id=?", (item_id,))
        if data:
            self.input_proy_codigo.setText(data[2]); self.combo_proy_modelo.setCurrentText(data[3]); 
            self.combo_proy_tactil.setCurrentText(data[4]); self.input_proy_ubicacion.setText(data[5]); self.input_proy_obs.setText(data[6])

    def clear_proyectores_inputs(self):
        self.editing_item_id = None; self.editing_item_type = None
        self.input_proy_codigo.clear(); self.combo_proy_modelo.setCurrentText(""); self.combo_proy_tactil.setCurrentIndex(0)
        self.input_proy_ubicacion.clear(); self.input_proy_obs.clear()
        
    def save_proyector(self):
        data_tuple = (self.input_proy_codigo.text(), self._get_combo_text(self.combo_proy_modelo), self.combo_proy_tactil.currentText(), self.input_proy_ubicacion.text(), self.input_proy_obs.text())
        insert_q = "INSERT INTO proyectores (inventario_id, codigo, modelo, tactil, ubicacion_equipo, observaciones) VALUES (?,?,?,?,?,?)"
        update_q = "UPDATE proyectores SET codigo=?, modelo=?, tactil=?, ubicacion_equipo=?, observaciones=? WHERE id=?"
        self._save_item('proyectores', data_tuple, insert_q, update_q)
    # --- Impresoras ---
    def edit_impresora(self, item_id):
        data = self.db.fetch_one("SELECT * FROM impresoras WHERE id=?", (item_id,))
        if data:
            self.input_imp_codigo.setText(data[2]); self.combo_imp_modelo.setCurrentText(data[3]);
            self.combo_imp_conexion.setCurrentText(data[4]); self.input_imp_ubicacion.setText(data[5]); self.input_imp_obs.setText(data[6])

    def clear_impresoras_inputs(self):
        self.editing_item_id = None; self.editing_item_type = None
        self.input_imp_codigo.clear(); self.combo_imp_modelo.setCurrentText(""); self.combo_imp_conexion.setCurrentIndex(0)
        self.input_imp_ubicacion.clear(); self.input_imp_obs.clear()

    def save_impresora(self):
        data_tuple = (self.input_imp_codigo.text(), self._get_combo_text(self.combo_imp_modelo), self.combo_imp_conexion.currentText(), self.input_imp_ubicacion.text(), self.input_imp_obs.text())
        insert_q = "INSERT INTO impresoras (inventario_id, codigo, modelo, conexion, ubicacion_equipo, observaciones) VALUES (?,?,?,?,?,?)"
        update_q = "UPDATE impresoras SET codigo=?, modelo=?, conexion=?, ubicacion_equipo=?, observaciones=? WHERE id=?"
        self._save_item('impresoras', data_tuple, insert_q, update_q)

    # --- Servidores ---
    def edit_servidor(self, item_id):
        data = self.db.fetch_one("SELECT * FROM servidores WHERE id=?", (item_id,))
        if data:
            self.input_srv_codigo.setText(data[2]); self.combo_srv_modelo.setCurrentText(data[3]);
            self.input_srv_uso.setText(data[4]); self.input_srv_ubicacion.setText(data[5]); self.input_srv_obs.setText(data[6])

    def clear_servidores_inputs(self):
        self.editing_item_id = None; self.editing_item_type = None
        self.input_srv_codigo.clear(); self.combo_srv_modelo.setCurrentText(""); self.input_srv_uso.clear()
        self.input_srv_ubicacion.clear(); self.input_srv_obs.clear()
        
    def save_servidor(self):
        data_tuple = (self.input_srv_codigo.text(), self._get_combo_text(self.combo_srv_modelo), self.input_srv_uso.text(), self.input_srv_ubicacion.text(), self.input_srv_obs.text())
        insert_q = "INSERT INTO servidores (inventario_id, codigo, modelo, uso, ubicacion_equipo, observaciones) VALUES (?,?,?,?,?,?)"
        update_q = "UPDATE servidores SET codigo=?, modelo=?, uso=?, ubicacion_equipo=?, observaciones=? WHERE id=?"
        self._save_item('servidores', data_tuple, insert_q, update_q)

    # --- Red ---
    def edit_red(self, item_id):
        data = self.db.fetch_one("SELECT * FROM red WHERE id=?", (item_id,))
        if data:
            self.input_red_codigo.setText(data[2]); self.combo_red_tipo.setCurrentText(data[3]);
            self.combo_red_modelo.setCurrentText(data[4]); self.input_red_ubicacion.setText(data[5]); self.input_red_obs.setText(data[6])

    def clear_red_inputs(self):
        self.editing_item_id = None; self.editing_item_type = None
        self.input_red_codigo.clear(); self.combo_red_tipo.setCurrentIndex(0); self.combo_red_modelo.setCurrentText("")
        self.input_red_ubicacion.clear(); self.input_red_obs.clear()
        
    def save_red(self):
        data_tuple = (self.input_red_codigo.text(), self.combo_red_tipo.currentText(), self._get_combo_text(self.combo_red_modelo), self.input_red_ubicacion.text(), self.input_red_obs.text())
        insert_q = "INSERT INTO red (inventario_id, codigo, tipo, modelo, ubicacion_equipo, observaciones) VALUES (?,?,?,?,?,?)"
        update_q = "UPDATE red SET codigo=?, tipo=?, modelo=?, ubicacion_equipo=?, observaciones=? WHERE id=?"
        self._save_item('red', data_tuple, insert_q, update_q)
        
    # --- CCTV Grabadores ---
    def edit_recorder(self, item_id):
        data = self.db.fetch_one("SELECT * FROM cctv_recorders WHERE id=?", (item_id,))
        if data:
            self.combo_cctv_rec_marca.setCurrentText(data[2]); self.combo_cctv_rec_modelo.setCurrentText(data[3]);
            self.input_cctv_rec_canales.setText(data[4]); self.input_cctv_rec_ubicacion.setText(data[5]); self.input_cctv_rec_obs.setText(data[6])

    def clear_cctv_recorders_inputs(self):
        self.editing_item_id = None; self.editing_item_type = None
        self.combo_cctv_rec_marca.setCurrentText(""); self.combo_cctv_rec_modelo.setCurrentText(""); self.input_cctv_rec_canales.clear()
        self.input_cctv_rec_ubicacion.clear(); self.input_cctv_rec_obs.clear()
        
    def save_recorder(self):
        data_tuple = (self._get_combo_text(self.combo_cctv_rec_marca), self._get_combo_text(self.combo_cctv_rec_modelo), self.input_cctv_rec_canales.text(), self.input_cctv_rec_ubicacion.text(), self.input_cctv_rec_obs.text())
        insert_q = "INSERT INTO cctv_recorders (inventario_id, marca, modelo, canales, ubicacion, observaciones) VALUES (?,?,?,?,?,?)"
        update_q = "UPDATE cctv_recorders SET marca=?, modelo=?, canales=?, ubicacion=?, observaciones=? WHERE id=?"
        self._save_item('cctv_recorders', data_tuple, insert_q, update_q)

    # --- CCTV Cámaras ---
    def edit_camera(self, item_id):
        data = self.db.fetch_one("SELECT * FROM cctv_cameras WHERE id=?", (item_id,))
        if data:
            self.combo_cctv_cam_marca.setCurrentText(data[2]); self.combo_cctv_cam_modelo.setCurrentText(data[3]);
            self.combo_cctv_cam_lente.setCurrentText(data[4]); self.input_cctv_cam_ubicacion.setText(data[5]); self.input_cctv_cam_obs.setText(data[6])

    def clear_cctv_cameras_inputs(self):
        self.editing_item_id = None; self.editing_item_type = None
        self.combo_cctv_cam_marca.setCurrentText(""); self.combo_cctv_cam_modelo.setCurrentText(""); self.combo_cctv_cam_lente.setCurrentText("")
        self.input_cctv_cam_ubicacion.clear(); self.input_cctv_cam_obs.clear()

    def save_camera(self):
        data_tuple = (self._get_combo_text(self.combo_cctv_cam_marca), self._get_combo_text(self.combo_cctv_cam_modelo), self._get_combo_text(self.combo_cctv_cam_lente), self.input_cctv_cam_ubicacion.text(), self.input_cctv_cam_obs.text())
        insert_q = "INSERT INTO cctv_cameras (inventario_id, marca, modelo, tipo_lente, ubicacion, observaciones) VALUES (?,?,?,?,?,?)"
        update_q = "UPDATE cctv_cameras SET marca=?, modelo=?, tipo_lente=?, ubicacion=?, observaciones=? WHERE id=?"
        self._save_item('cctv_cameras', data_tuple, insert_q, update_q)

    # --- Control de Acceso ---
    def edit_acceso(self, item_id):
        data = self.db.fetch_one("SELECT * FROM accesos WHERE id=?", (item_id,))
        if data:
            self.combo_acceso_marca.setCurrentText(data[2]); self.combo_acceso_modelo.setCurrentText(data[3]);
            self.combo_acceso_tipo.setCurrentText(data[4]); self.input_acceso_ubicacion.setText(data[5]); self.input_acceso_obs.setText(data[6])

    def clear_accesos_inputs(self):
        self.editing_item_id = None; self.editing_item_type = None
        self.combo_acceso_marca.setCurrentText(""); self.combo_acceso_modelo.setCurrentText(""); self.combo_acceso_tipo.setCurrentIndex(0)
        self.input_acceso_ubicacion.clear(); self.input_acceso_obs.clear()

    def save_acceso(self):
        data_tuple = (self._get_combo_text(self.combo_acceso_marca), self._get_combo_text(self.combo_acceso_modelo), self.combo_acceso_tipo.currentText(), self.input_acceso_ubicacion.text(), self.input_acceso_obs.text())
        insert_q = "INSERT INTO accesos (inventario_id, marca, modelo, tipo, ubicacion, observaciones) VALUES (?,?,?,?,?,?)"
        update_q = "UPDATE accesos SET marca=?, modelo=?, tipo=?, ubicacion=?, observaciones=? WHERE id=?"
        self._save_item('accesos', data_tuple, insert_q, update_q)
    # --- Software ---
    def edit_software(self, item_id):
        data = self.db.fetch_one("SELECT * FROM software WHERE id=?", (item_id,))
        if data:
            self.combo_sw_nombre.setCurrentText(data[2]); self.input_sw_licencia.setText(data[3])
            
    def clear_software_inputs(self):
        self.editing_item_id = None; self.editing_item_type = None
        self.combo_sw_nombre.setCurrentText(""); self.input_sw_licencia.clear()

    def save_software(self):
        data_tuple = (self._get_combo_text(self.combo_sw_nombre), self.input_sw_licencia.text())
        insert_q = "INSERT INTO software (inventario_id, nombre, licencia) VALUES (?,?,?)"
        update_q = "UPDATE software SET nombre=?, licencia=? WHERE id=?"
        self._save_item('software', data_tuple, insert_q, update_q)

    # --- Credenciales ---
    def edit_credencial(self, item_id):
        data = self.db.fetch_one("SELECT * FROM credenciales WHERE id=?", (item_id,))
        if data:
            self.input_cred_elemento.setText(data[2]); self.input_cred_usuario.setText(data[3])
            self.input_cred_clave.setText(data[4]); self.input_cred_notas.setText(data[5])
            
    def clear_credenciales_inputs(self):
        self.editing_item_id = None; self.editing_item_type = None
        self.input_cred_elemento.clear(); self.input_cred_usuario.clear()
        self.input_cred_clave.clear(); self.input_cred_notas.clear()
    
    def save_credencial(self):
        data_tuple = (self.input_cred_elemento.text(), self.input_cred_usuario.text(), self.input_cred_clave.text(), self.input_cred_notas.text())
        insert_q = "INSERT INTO credenciales (inventario_id, elemento, usuario, clave, notas) VALUES (?,?,?,?,?)"
        update_q = "UPDATE credenciales SET elemento=?, usuario=?, clave=?, notas=? WHERE id=?"
        self._save_item('credenciales', data_tuple, insert_q, update_q)

    # --- Exportación ---
    def _get_full_data_for_export(self):
        inv_data = self.db.fetch_one("SELECT * FROM inventarios WHERE id=?", (self.current_inventory_id,))
        if not inv_data: return None
        return {
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

    def export_to_pdf(self):
        export_data = self._get_full_data_for_export()
        if not export_data:
            QMessageBox.warning(self, "Datos insuficientes", "No hay datos que exportar.")
            return
        
        cliente_name_safe = "".join(x for x in export_data['cliente'] if x.isalnum() or x in " -_").rstrip()
        default_filename = f"Auditoria_{cliente_name_safe}.pdf"

        filename, _ = QFileDialog.getSaveFileName(self, "Guardar PDF", default_filename, "PDF Files (*.pdf)")
        if filename:
            try:
                generate_pdf(filename, export_data)
                QMessageBox.information(self, "Éxito", f"PDF generado correctamente en:\n{filename}")
            except Exception as e:
                QMessageBox.critical(self, "Error de Exportación", f"No se pudo generar el PDF. Error: {e}")

    def export_to_excel(self):
        export_data = self._get_full_data_for_export()
        if not export_data:
            QMessageBox.warning(self, "Datos insuficientes", "No hay datos que exportar.")
            return
        
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
        cliente_name_safe = "".join(x for x in export_data['cliente'] if x.isalnum() or x in " -_").rstrip()
        default_filename = f"Inventario_{cliente_name_safe}_{timestamp}.xlsx"

        filename, _ = QFileDialog.getSaveFileName(self, "Guardar Excel", default_filename, "Excel Files (*.xlsx)")
        if filename:
            try:
                generate_excel(filename, export_data)
                QMessageBox.information(self, "Éxito", f"Archivo Excel generado correctamente en:\n{filename}")
            except Exception as e:
                QMessageBox.critical(self, "Error de Exportación", f"No se pudo generar el archivo Excel. Error: {e}")

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
            self.main_window = MainWindow(inventory_id, app_instance=self)
            self.main_window.show()
            self.exec()
            
            if not self.should_switch_user:
                break
        
        self.db.close()
        return 0

if __name__ == "__main__":
    os.makedirs(get_writable_data_path('data/images'), exist_ok=True)
    app = App(sys.argv)
    sys.exit(app.run())