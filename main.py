import os
import codecs
from datetime import datetime
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.input import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.popup import Popup

class BuscadorForm(BoxLayout):
    def __init__(self, **kwargs):
        super(BuscadorForm, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 20
        self.spacing = 10

        # Título principal
        self.add_widget(Label(text="SEEKER MOBILE v1.0", font_size=24, size_hint_y=None, height=40))

        # Campo para la palabra clave
        self.add_widget(Label(text="Palabra clave a buscar:", size_hint_y=None, height=20))
        self.txt_keyword = TextInput(multiline=False, size_hint_y=None, height=40)
        self.add_widget(self.txt_keyword)

        # Botón para seleccionar la carpeta
        self.add_widget(Label(text="Selecciona la carpeta con los archivos:", size_hint_y=None, height=20))
        self.btn_carpeta = Button(text="Abrir Selector de Carpetas", size_hint_y=None, height=50)
        self.btn_carpeta.bind(on_press=self.abrir_selector)
        self.add_widget(self.btn_carpeta)

        # Etiqueta que muestra la ruta seleccionada
        self.lbl_ruta = Label(text="Ninguna carpeta seleccionada", size_hint_y=None, height=30, color=(0.3, 0.7, 1, 1))
        self.add_widget(self.lbl_ruta)
        self.ruta_seleccionada = ""

        # Botón para iniciar la búsqueda
        self.btn_buscar = Button(text="¡INICIAR BÚSQUEDA!", size_hint_y=None, height=60, background_color=(0, 1, 0, 1))
        self.btn_buscar.bind(on_press=self.procesar_busqueda)
        self.add_widget(self.btn_buscar)

        # Consola de resultados en pantalla (con scroll)
        self.scroll = ScrollView()
        self.lbl_consola = Label(text="Resultados:\n...", size_hint_y=None, markup=True)
        self.lbl_consola.bind(texture_size=self.lbl_consola.setter('size'))
        self.scroll.add_widget(self.lbl_consola)
        self.add_widget(self.scroll)

    def abrir_selector(self, instance):
        # Crear una ventana flotante (Popup) para elegir la carpeta
        contenido = BoxLayout(orientation='vertical')
        filechooser = FileChooserIconView(dirselect=True) # Habilita selección de carpetas
        contenido.add_widget(filechooser)

        btn_seleccionar = Button(text="Seleccionar esta carpeta", size_hint_y=None, height=50)
        contenido.add_widget(btn_seleccionar)

        popup = Popup(title='Elige una carpeta', content=contenido, size_hint=(0.9, 0.9))
        
        def confirmar_seleccion(inst):
            if filechooser.selection:
                self.ruta_seleccionada = filechooser.selection[0]
                self.lbl_ruta.text = f"Ruta: {self.ruta_seleccionada}"
            popup.dismiss()

        btn_seleccionar.bind(on_press=confirmar_seleccion)
        popup.open()

    def log(self, texto):
        self.lbl_consola.text += "\n" + texto

    def procesar_busqueda(self, instance):
        palabra = self.txt_keyword.text.strip().lower()
        if not palabra:
            self.lbl_consola.text = "[color=ff0000]Error: Escribe una palabra clave.[/color]"
            return
        if not self.ruta_seleccionada or not os.path.exists(self.ruta_seleccionada):
            self.lbl_consola.text = "[color=ff0000]Error: Selecciona una carpeta válida.[/color]"
            return

        self.lbl_consola.text = "Iniciando búsqueda..."
        
        try:
            contenido = os.listdir(self.ruta_seleccionada)
        except Exception as e:
            self.log(f"Error al abrir carpeta: {e}")
            return

        found = False
        
        # Guardar en la carpeta de descargas pública de Android para encontrar el TXT fácil
        # Si no se puede, lo guarda en la misma carpeta interna de la app
        try:
            carpeta_salida = "/sdcard/Download"
            if not os.path.exists(carpeta_salida):
                carpeta_salida = self.ruta_seleccionada
        except:
            carpeta_salida = self.ruta_seleccionada

        fecha_hora = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_archivo = f"resultados_{fecha_hora}.txt"
        archivo_salida = os.path.join(carpeta_salida, nombre_archivo)

        total_txt = len([f for f in contenido if f.endswith(".txt")])
        self.log(f"Archivos .txt detectados: {total_txt}")

        if total_txt == 0:
            return

        try:
            with open(archivo_salida, "w", encoding='utf-8') as output_file:
                for archivo in contenido:
                    if archivo.endswith(".txt"):
                        file_path = os.path.join(self.ruta_seleccionada, archivo)
                        
                        with codecs.open(file_path, mode='r', encoding='utf-8', errors='replace') as prueba:
                            lines_to_print = 0

                            for linea in prueba:
                                linea_limpia = linea.strip()
                                es_cabecera = (linea.startswith("Host:") or 
                                               linea.startswith("URL:") or 
                                               linea.startswith("http://") or 
                                               linea.startswith("https://"))

                                if es_cabecera:
                                    if palabra in linea.lower():
                                        self.log(f"[color=00ff00][¡OK!] -> {archivo}[/color]")
                                        self.log(linea_limpia)
                                        output_file.write(f"\nEnlace: {linea_limpia}\n")
                                        output_file.write(f"Archivo: {file_path}\n")
                                        found = True
                                        lines_to_print = 3
                                    else:
                                        lines_to_print = 0
                                    continue

                                if lines_to_print > 0:
                                    self.log(linea_limpia)
                                    output_file.write(linea)
                                    lines_to_print -= 1

                if not found:
                    self.log("No se encontraron coincidencias.")
                    output_file.write("No se encontró el enlace solicitado.\n")
                else:
                    self.log(f"\n[color=00ff00]ÉXITO: Guardado en Descargas como '{nombre_archivo}'[/color]")

        except PermissionError:
            self.log("[color=ff0000]Error de permisos al escribir el reporte.[/color]")
        except Exception as e:
            self.log(f"[color=ff0000]Error: {e}[/color]")

class SeekerApp(App):
    def build(self):
        return BuscadorForm()

if __name__ == '__main__':
    SeekerApp().run()