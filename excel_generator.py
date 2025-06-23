# excel_generator.py
import pandas as pd

def create_and_write_sheet(writer, sheet_name, data_list, headers):
    """Crea una hoja de Excel a partir de una lista de datos."""
    if data_list:
        # Excluimos las dos primeras columnas (id, inventario_id) de los datos
        # y creamos el DataFrame
        df = pd.DataFrame([row[2:] for row in data_list], columns=headers)
        df.to_excel(writer, sheet_name=sheet_name, index=False)
        # Auto-ajustar el ancho de las columnas
        worksheet = writer.sheets[sheet_name]
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            if len(column) > 0:
                # Obtenemos la longitud del header
                max_length = len(str(worksheet[f'{column_letter}1'].value))
                # Iteramos sobre las celdas para encontrar la longitud máxima
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = (max_length + 2)
                worksheet.column_dimensions[column_letter].width = adjusted_width


def generate_excel(filename, data):
    """Genera un archivo Excel con múltiples hojas a partir del diccionario de datos."""
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        
        # Hoja 1: Información General
        general_info = {
            "Campo": ["Cliente", "Ubicación", "Responsable", "Fecha", "Estructura Informática", 
                      "Ubicación Manuales", "Histórico Problemas", "Modo de Trabajo", "Equipos Extra"],
            "Valor": [data["cliente"], data["ubicacion"], data["responsable"], data["fecha"], data["estructura_info"], 
                      data["ubicacion_manuales"], data["historico_problemas"], data["modo_trabajo"], data["equipos_extra"]]
        }
        df_general = pd.DataFrame(general_info)
        df_general.to_excel(writer, sheet_name='Informacion General', index=False)
        # Ajustar ancho de la hoja general
        worksheet = writer.sheets['Informacion General']
        worksheet.column_dimensions['A'].width = 30
        worksheet.column_dimensions['B'].width = 80

        # Crear hojas para cada tipo de equipo
        create_and_write_sheet(writer, 'PCs', data['pcs'], ['Cód.', 'Placa', 'RAM', 'Core', 'Disco', 'S.O', 'Fuente', 'Antivirus', 'Ubic.', 'Obs.'])
        create_and_write_sheet(writer, 'Proyectores', data['proyectores'], ['Cód.', 'Modelo', 'Táctil', 'Ubic.', 'Obs.'])
        create_and_write_sheet(writer, 'Impresoras', data['impresoras'], ['Cód.', 'Modelo', 'Conexión', 'Ubic.', 'Obs.'])
        create_and_write_sheet(writer, 'Servidores', data['servidores'], ['Cód.', 'Modelo', 'Uso', 'Ubic.', 'Obs.'])
        create_and_write_sheet(writer, 'Equipos de Red', data['red'], ['Cód.', 'Tipo', 'Modelo', 'Ubic.', 'Obs.'])
        create_and_write_sheet(writer, 'Grabadores CCTV', data['cctv_recorders'], ['Marca', 'Modelo', 'Canales', 'Ubic.', 'Obs.'])
        create_and_write_sheet(writer, 'Camaras CCTV', data['cctv_cameras'], ['Marca', 'Modelo', 'Lente', 'Ubic.', 'Obs.'])
        create_and_write_sheet(writer, 'Control de Acceso', data['accesos'], ['Marca', 'Modelo', 'Tipo', 'Ubic.', 'Obs.'])
        create_and_write_sheet(writer, 'Software', data['software'], ['Software', 'Licencia'])
        create_and_write_sheet(writer, 'Credenciales', data['credenciales'], ['Elemento', 'Usuario', 'Contraseña', 'Notas'])