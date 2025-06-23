# dashboard_widgets.py
import sys
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

# Usar un estilo visualmente atractivo para los gráficos
plt.style.use('seaborn-v0_8-darkgrid')

class MplCanvas(FigureCanvas):
    """Clase base para un lienzo de Matplotlib integrable en PyQt."""
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor='#ECEFF1')
        self.axes = self.fig.add_subplot(111)
        self.axes.set_facecolor('#ECEFF1')
        self.axes.tick_params(axis='x', colors='black')
        self.axes.tick_params(axis='y', colors='black')
        self.axes.spines['bottom'].set_color('black')
        self.axes.spines['top'].set_color('black') 
        self.axes.spines['right'].set_color('black')
        self.axes.spines['left'].set_color('black')
        super(MplCanvas, self).__init__(self.fig)

class BarChartWidget(QWidget):
    """Widget que contiene un gráfico de barras."""
    def __init__(self, *args, **kwargs):
        super(BarChartWidget, self).__init__(*args, **kwargs)
        self.canvas = MplCanvas(self, width=5, height=4, dpi=100)
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)

    def update_chart(self, labels, values):
        self.canvas.axes.cla() # Limpiar el gráfico anterior
        bars = self.canvas.axes.bar(labels, values, color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b'])
        self.canvas.axes.set_title('Total de Equipos por Categoría', color='black')
        self.canvas.axes.tick_params(axis='x', rotation=15, labelsize='small')
        
        # Añadir etiquetas de valor encima de las barras
        self.canvas.axes.bar_label(bars, fmt='%d', color='black')
        
        self.canvas.fig.tight_layout()
        self.canvas.draw()

class PieChartWidget(QWidget):
    """Widget que contiene un gráfico de tarta."""
    def __init__(self, *args, **kwargs):
        super(PieChartWidget, self).__init__(*args, **kwargs)
        self.canvas = MplCanvas(self, width=4, height=4, dpi=100)
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)

    def update_chart(self, labels, sizes):
        self.canvas.axes.cla() # Limpiar el gráfico anterior
        if not sizes or sum(sizes) == 0:
            self.canvas.axes.text(0.5, 0.5, 'Sin datos de S.O.', ha='center', va='center', size=12, color='grey')
            self.canvas.axes.set_title('Distribución de Sistemas Operativos', color='black')
        else:
            wedges, texts, autotexts = self.canvas.axes.pie(
                sizes, 
                autopct='%1.1f%%', 
                startangle=90,
                pctdistance=0.85,
                colors=plt.cm.Paired.colors
            )
            # Dibujar un círculo en el centro para hacer un "donut chart"
            centre_circle = plt.Circle((0,0),0.70,fc='#ECEFF1')
            self.canvas.axes.add_artist(centre_circle)

            # Mejorar legibilidad de las etiquetas
            plt.setp(autotexts, size=8, weight="bold", color="black")
            
            self.canvas.axes.set_title('Distribución de Sistemas Operativos', color='black')
            self.canvas.axes.legend(wedges, labels, title="Sistemas", loc="center left", bbox_to_anchor=(0.9, 0, 0.5, 1), fontsize='small')
        
        self.canvas.axes.axis('equal')  # Asegura que el gráfico de tarta sea un círculo.
        self.canvas.fig.tight_layout()
        self.canvas.draw()