# main.py
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QTableWidgetItem, QMessageBox, QFileDialog
from PyQt6.uic import loadUi
from PyQt6.QtCore import QDate
from database import DatabaseManager
from pdf_generator import generate_pdf

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        loadUi("ui_inventario.ui", self)
        
        self.db = DatabaseManager()
        self.current_inventory_id = None

        self.setup_ui()
        self.connect_signals()
        self.load_inventories_list()

    def setup_ui(self):
        # Configurar tablas para que no sean editables directamente
        self.table_pcs.setEditTriggers(self.table_pcs.EditTrigger.NoEditTriggers)
        self.table_proyectores.setEditTriggers(self.table_proyectores.EditTrigger.NoEditTriggers)
        self.table_impresoras.setEditTriggers(self.table_impresoras.EditTrigger.NoEditTriggers)
        self.table_servidores.setEditTriggers(self.table_servidores.EditTrigger.NoEditTriggers)
        self.table_red.setEditTriggers(self.table_red.EditTrigger.NoEditTriggers)
        self.table_software.setEditTriggers(self.table_software.EditTrigger.NoEditTriggers)
        
        # Ocultar IDs de las tablas
        self.table_pcs.setColumnHidden(0, True)
        self.table_proyectores.setColumnHidden(0, True)
        self.table_impresoras.setColumnHidden(0, True)
        self.table_servidores.setColumnHidden(0, True)
        self.table_red.setColumnHidden(0, True)
        self.table_software.setColumnHidden(0, True)
        
        self.date_fecha.setDate(QDate.currentDate())


    def connect_signals(self):
        # Botones de gestión de inventario
        self.btn_nuevo_inventario.clicked.connect(self.new_inventory)
        self.btn_guardar_inventario.clicked.connect(self.save_inventory)
        self.btn_eliminar_inventario.clicked.connect(self.delete_inventory)
        self.btn_exportar_pdf.clicked.connect(self.export_to_pdf)
        self.combo_inventarios.currentIndexChanged.connect(self.load_selected_inventory)

        # Botones de añadir
        self.btn_add_pc.clicked.connect(self.add_pc)
        self.btn_add_proyector.clicked.connect(self.add_proyector)
        self.btn_add_impresora.clicked.connect(self.add_impresora)
        self.btn_add_servidor.clicked.connect(self.add_servidor)
        self.btn_add_red.clicked.connect(self.add_red)
        self.btn_add_software.clicked.connect(self.add_software)

        # Botones de eliminar
        self.btn_del_pc.clicked.connect(lambda: self.delete_item('pcs', self.table_pcs))
        self.btn_del_proyector.clicked.connect(lambda: self.delete_item('proyectores', self.table_proyectores))
        self.btn_del_impresora.clicked.connect(lambda: self.delete_item('impresoras', self.table_impresoras))
        self.btn_del_servidor.clicked.connect(lambda: self.delete_item('servidores', self.table_servidores))
        self.btn_del_red.clicked.connect(lambda: self.delete_item('red', self.table_red))
        self.btn_del_software.clicked.connect(lambda: self.delete_item('software', self.table_software))
        
        # Botón para seleccionar plano
        self.btn_select_plano.clicked.connect(self.select_plano)

    # --- Gestión de Inventarios ---
    def load_inventories_list(self):
        self.combo_inventarios.blockSignals(True)
        self.combo_inventarios.clear()
        inventories = self.db.fetch_all("SELECT id, cliente, ubicacion FROM inventarios ORDER BY cliente")
        self.combo_inventarios.addItem("--- Seleccione un inventario ---", -1)
        for inv_id, cliente, ubicacion in inventories:
            self.combo_inventarios.addItem(f"{cliente} - {ubicacion}", inv_id)
        self.combo_inventarios.blockSignals(False)

    def new_inventory(self):
        self.clear_all_fields()
        self.current_inventory_id = None
        self.input_cliente.setFocus()

    def save_inventory(self):
        cliente = self.input_cliente.text()
        if not cliente:
            QMessageBox.warning(self, "Campo requerido", "El nombre del cliente es obligatorio.")
            return

        data = (
            cliente,
            self.input_ubicacion.text(),
            self.input_responsable.text(),
            self.date_fecha.date().toString("dd/MM/yyyy"),
            self.text_estructura.toPlainText(),
            self.text_ubicacion_manuales.toPlainText(),
            self.text_historico.toPlainText(),
            self.text_modo_trabajo.toPlainText(),
            self.text_equipos_extra.toPlainText(),
            self.label_plano_path.text()
        )

        if self.current_inventory_id:
            query = """UPDATE inventarios SET cliente=?, ubicacion=?, responsable=?, fecha=?,
                       estructura_info=?, ubicacion_manuales=?, historico_problemas=?, modo_trabajo=?,
                       equipos_extra=?, plano_path=? WHERE id=?"""
            self.db.execute_query(query, data + (self.current_inventory_id,))
            QMessageBox.information(self, "Éxito", "Inventario actualizado correctamente.")
        else:
            query = """INSERT INTO inventarios (cliente, ubicacion, responsable, fecha,
                       estructura_info, ubicacion_manuales, historico_problemas, modo_trabajo,
                       equipos_extra, plano_path) VALUES (?,?,?,?,?,?,?,?,?,?)"""
            cursor = self.db.execute_query(query, data)
            self.current_inventory_id = cursor.lastrowid
            QMessageBox.information(self, "Éxito", "Nuevo inventario guardado.")
        
        self.load_inventories_list()
        self.combo_inventarios.setCurrentText(f"{data[0]} - {data[1]}")


    def load_selected_inventory(self):
        self.current_inventory_id = self.combo_inventarios.currentData()
        if not self.current_inventory_id or self.current_inventory_id == -1:
            self.clear_all_fields()
            return
        
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
            
            # Cargar datos de las tablas
            self.refresh_table('pcs', self.table_pcs, ['ID', 'Código', 'Placa', 'RAM', 'Core', 'Disco', 'S.O.', 'Fuente', 'Ubicación', 'Obs.'])
            self.refresh_table('proyectores', self.table_proyectores, ['ID', 'Código', 'Modelo', 'Ubicación', 'Obs.'])
            self.refresh_table('impresoras', self.table_impresoras, ['ID', 'Código', 'Modelo', 'Ubicación', 'Obs.'])
            self.refresh_table('servidores', self.table_servidores, ['ID', 'Código', 'Modelo', 'Uso', 'Ubicación', 'Obs.'])
            self.refresh_table('red', self.table_red, ['ID', 'Código', 'Tipo', 'Modelo', 'Ubicación', 'Obs.'])
            self.refresh_table('software', self.table_software, ['ID', 'Nombre', 'Licencia'])

    def delete_inventory(self):
        if not self.current_inventory_id:
            QMessageBox.warning(self, "Error", "No hay ningún inventario seleccionado para eliminar.")
            return
        
        reply = QMessageBox.question(self, 'Confirmar eliminación', 
                                     f"¿Está seguro de que desea eliminar el inventario '{self.combo_inventarios.currentText()}' y todos sus datos asociados? Esta acción no se puede deshacer.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            self.db.execute_query("DELETE FROM inventarios WHERE id=?", (self.current_inventory_id,))
            self.new_inventory()
            self.load_inventories_list()
            QMessageBox.information(self, "Éxito", "Inventario eliminado.")

    # --- Gestión de Items ---
    def add_pc(self):
        if not self.check_inventory_selected(): return
        data = (self.current_inventory_id, self.input_pc_codigo.text(), self.input_pc_placa.text(), self.input_pc_ram.text(), self.input_pc_core.text(), self.input_pc_disco.text(), self.input_pc_so.text(), self.input_pc_fuente.text(), self.input_pc_ubicacion.text(), self.input_pc_obs.text())
        self.db.execute_query("INSERT INTO pcs (inventario_id, codigo, placa, ram, core, disco, so, fuente, ubicacion_equipo, observaciones) VALUES (?,?,?,?,?,?,?,?,?,?)", data)
        self.refresh_table('pcs', self.table_pcs, ['ID', 'Código', 'Placa', 'RAM', 'Core', 'Disco', 'S.O.', 'Fuente', 'Ubicación', 'Obs.'])
        self.clear_inputs([self.input_pc_codigo, self.input_pc_placa, self.input_pc_ram, self.input_pc_core, self.input_pc_disco, self.input_pc_so, self.input_pc_fuente, self.input_pc_ubicacion, self.input_pc_obs])

    def add_proyector(self):
        if not self.check_inventory_selected(): return
        data = (self.current_inventory_id, self.input_proy_codigo.text(), self.input_proy_modelo.text(), self.input_proy_ubicacion.text(), self.input_proy_obs.text())
        self.db.execute_query("INSERT INTO proyectores (inventario_id, codigo, modelo, ubicacion_equipo, observaciones) VALUES (?,?,?,?,?)", data)
        self.refresh_table('proyectores', self.table_proyectores, ['ID', 'Código', 'Modelo', 'Ubicación', 'Obs.'])
        self.clear_inputs([self.input_proy_codigo, self.input_proy_modelo, self.input_proy_ubicacion, self.input_proy_obs])
        
    def add_impresora(self):
        if not self.check_inventory_selected(): return
        data = (self.current_inventory_id, self.input_imp_codigo.text(), self.input_imp_modelo.text(), self.input_imp_ubicacion.text(), self.input_imp_obs.text())
        self.db.execute_query("INSERT INTO impresoras (inventario_id, codigo, modelo, ubicacion_equipo, observaciones) VALUES (?,?,?,?,?)", data)
        self.refresh_table('impresoras', self.table_impresoras, ['ID', 'Código', 'Modelo', 'Ubicación', 'Obs.'])
        self.clear_inputs([self.input_imp_codigo, self.input_imp_modelo, self.input_imp_ubicacion, self.input_imp_obs])

    def add_servidor(self):
        if not self.check_inventory_selected(): return
        data = (self.current_inventory_id, self.input_srv_codigo.text(), self.input_srv_modelo.text(), self.input_srv_uso.text(), self.input_srv_ubicacion.text(), self.input_srv_obs.text())
        self.db.execute_query("INSERT INTO servidores (inventario_id, codigo, modelo, uso, ubicacion_equipo, observaciones) VALUES (?,?,?,?,?,?)", data)
        self.refresh_table('servidores', self.table_servidores, ['ID', 'Código', 'Modelo', 'Uso', 'Ubicación', 'Obs.'])
        self.clear_inputs([self.input_srv_codigo, self.input_srv_modelo, self.input_srv_uso, self.input_srv_ubicacion, self.input_srv_obs])
    
    def add_red(self):
        if not self.check_inventory_selected(): return
        data = (self.current_inventory_id, self.input_red_codigo.text(), self.combo_red_tipo.currentText(), self.input_red_modelo.text(), self.input_red_ubicacion.text(), self.input_red_obs.text())
        self.db.execute_query("INSERT INTO red (inventario_id, codigo, tipo, modelo, ubicacion_equipo, observaciones) VALUES (?,?,?,?,?,?)", data)
        self.refresh_table('red', self.table_red, ['ID', 'Código', 'Tipo', 'Modelo', 'Ubicación', 'Obs.'])
        self.clear_inputs([self.input_red_codigo, self.input_red_modelo, self.input_red_ubicacion, self.input_red_obs])

    def add_software(self):
        if not self.check_inventory_selected(): return
        data = (self.current_inventory_id, self.input_sw_nombre.text(), self.input_sw_licencia.text())
        self.db.execute_query("INSERT INTO software (inventario_id, nombre, licencia) VALUES (?,?,?)", data)
        self.refresh_table('software', self.table_software, ['ID', 'Nombre', 'Licencia'])
        self.clear_inputs([self.input_sw_nombre, self.input_sw_licencia])

    def delete_item(self, table_name, table_widget):
        selected_row = table_widget.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Selección requerida", "Por favor, seleccione un elemento de la tabla para eliminar.")
            return

        item_id = table_widget.item(selected_row, 0).text()
        self.db.execute_query(f"DELETE FROM {table_name} WHERE id=?", (item_id,))
        table_widget.removeRow(selected_row)
        QMessageBox.information(self, "Éxito", "Elemento eliminado.")

    def select_plano(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Seleccionar Plano", "", "Images (*.png *.xpm *.jpg *.jpeg)")
        if filename:
            self.label_plano_path.setText(filename)


    # --- Utilidades ---
    def refresh_table(self, table_name, table_widget, headers):
        table_widget.setRowCount(0)
        table_widget.setColumnCount(len(headers))
        table_widget.setHorizontalHeaderLabels(headers)
        data = self.db.fetch_all(f"SELECT * FROM {table_name} WHERE inventario_id=?", (self.current_inventory_id,))
        for row_num, row_data in enumerate(data):
            table_widget.insertRow(row_num)
            for col_num, col_data in enumerate(row_data):
                table_widget.setItem(row_num, col_num, QTableWidgetItem(str(col_data)))
        table_widget.resizeColumnsToContents()

    def check_inventory_selected(self):
        if not self.current_inventory_id:
            QMessageBox.warning(self, "Inventario no guardado", "Debe guardar la información general del inventario antes de añadir equipos.")
            self.tabs_main.setCurrentIndex(0) # Mover a la pestaña de info general
            return False
        return True

    def clear_all_fields(self):
        # Limpiar info general
        self.input_cliente.clear()
        self.input_ubicacion.clear()
        self.input_responsable.clear()
        self.date_fecha.setDate(QDate.currentDate())
        self.text_estructura.clear()
        self.text_ubicacion_manuales.clear()
        self.text_historico.clear()
        self.text_modo_trabajo.clear()
        self.text_equipos_extra.clear()
        self.label_plano_path.clear()
        self.combo_inventarios.setCurrentIndex(0)

        # Limpiar todas las tablas
        self.table_pcs.setRowCount(0)
        self.table_proyectores.setRowCount(0)
        self.table_impresoras.setRowCount(0)
        self.table_servidores.setRowCount(0)
        self.table_red.setRowCount(0)
        self.table_software.setRowCount(0)
        
        self.current_inventory_id = None

    def clear_inputs(self, inputs_list):
        for input_widget in inputs_list:
            input_widget.clear()
    
    def export_to_pdf(self):
        if not self.current_inventory_id:
            QMessageBox.warning(self, "Error", "Debe seleccionar y cargar un inventario para exportar.")
            return

        # Recopilar todos los datos de la base de datos
        inv_data = self.db.fetch_one("SELECT * FROM inventarios WHERE id=?", (self.current_inventory_id,))
        pdf_data = {
            "cliente": inv_data[1], "ubicacion": inv_data[2], "responsable": inv_data[3], "fecha": inv_data[4],
            "estructura_info": inv_data[5], "ubicacion_manuales": inv_data[6], "historico_problemas": inv_data[7],
            "modo_trabajo": inv_data[8], "equipos_extra": inv_data[9], "plano_path": inv_data[10],
            "pcs": self.db.fetch_all("SELECT * FROM pcs WHERE inventario_id=?", (self.current_inventory_id,)),
            "proyectores": self.db.fetch_all("SELECT * FROM proyectores WHERE inventario_id=?", (self.current_inventory_id,)),
            "impresoras": self.db.fetch_all("SELECT * FROM impresoras WHERE inventario_id=?", (self.current_inventory_id,)),
            "servidores": self.db.fetch_all("SELECT * FROM servidores WHERE inventario_id=?", (self.current_inventory_id,)),
            "red": self.db.fetch_all("SELECT * FROM red WHERE inventario_id=?", (self.current_inventory_id,)),
            "software": self.db.fetch_all("SELECT * FROM software WHERE inventario_id=?", (self.current_inventory_id,))
        }

        filename, _ = QFileDialog.getSaveFileName(self, "Guardar PDF", f"Auditoria_{pdf_data['cliente']}.pdf", "PDF Files (*.pdf)")
        if filename:
            try:
                generate_pdf(filename, pdf_data)
                QMessageBox.information(self, "Éxito", f"PDF generado correctamente en:\n{filename}")
            except Exception as e:
                QMessageBox.critical(self, "Error de Exportación", f"No se pudo generar el PDF. Error: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())