from kivy.config import Config
# Desactivar el cierre automático con Esc, bloquear redimensionamiento y evitar pantalla completa
Config.set('kivy', 'exit_on_escape', '0')
Config.set('graphics', 'resizable', '0')
Config.set('graphics', 'fullscreen', '0')

import sqlite3
import shutil
import random
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button  # ¡IMPORTANTE!

# ----------------- BASE DE DATOS -----------------
conn = sqlite3.connect("mi_base_de_datos.db", check_same_thread=False)

def init_db():
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS datos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campo1 TEXT,
            campo2 TEXT,
            campo3 TEXT,
            campo4 TEXT
        )
    """)
    conn.commit()
    cursor.execute("SELECT COUNT(*) FROM datos")
    if cursor.fetchone()[0] == 0:
        sample_data = [
            ("apple", "red", "sweet", "fruit"),
            ("banana", "yellow", "sweet", "tropical"),
            ("orange", "orange", "citrus", "juicy"),
            ("kiwi", "green", "sour", "exotic"),
            ("grape", "purple", "sweet", "small"),
            ("mango", "orange", "tropical", "juicy")
        ]
        cursor.executemany("INSERT INTO datos (campo1, campo2, campo3, campo4) VALUES (?, ?, ?, ?)", sample_data)
        conn.commit()

init_db()

# ----------------- PANTALLA SPLASH (Cinemática Terminal) -----------------
class SplashScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = FloatLayout()
        with self.layout.canvas.before:
            Color(0, 0, 0, 1)
            self.bg_rect = Rectangle(pos=(0, 0), size=Window.size)
        self.layout.bind(pos=self.update_bg, size=self.update_bg)
        self.terminal_label = Label(text="", font_size=18, color=(0, 1, 0, 1),
                                    size_hint=(1, 1), halign="left", valign="top")
        self.terminal_label.bind(size=self.terminal_label.setter('text_size'))
        self.layout.add_widget(self.terminal_label)
        self.add_widget(self.layout)
        
        self.lines = [
            "Verificando usuario...",
            "Verificando estado de red...",
            "Verificando datos...",
            "Reloading...",
            "accediendo...",
            "Bienvenido Usuario.  --  [CONFIDENCIAL]\n\nTodo lo que vea aquí es de suma confidencialidad, \nexponerlo afuera puede comprometer su integridad."
        ]
        self.current_line = 0
        self.current_char = 0
        self.displayed_text = ""
    
    def update_bg(self, *args):
        self.bg_rect.pos = (0, 0)
        self.bg_rect.size = self.layout.size

    def on_enter(self):
        Clock.schedule_interval(self.type_effect, 0.05)
    
    def type_effect(self, dt):
        if self.current_line >= len(self.lines):
            Clock.unschedule(self.type_effect)
            Clock.schedule_once(lambda dt: setattr(self.manager, "current", "main"), 1)
            return False
        current_full_line = self.lines[self.current_line]
        if self.current_char < len(current_full_line):
            self.displayed_text += current_full_line[self.current_char]
            self.current_char += 1
        else:
            self.displayed_text += "\n"
            self.current_line += 1
            self.current_char = 0
        self.terminal_label.text = self.displayed_text
        return True

# ----------------- PANTALLA PRINCIPAL (Búsqueda) -----------------
class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="vertical", spacing=10, padding=20)
        layout.add_widget(Label(text="Pantalla Principal", font_size=20))
        
        self.text_input = TextInput(hint_text="Escribe para buscar...", font_size=16, size_hint=(1, 0.2))
        self.text_input.bind(text=self.on_text_change)
        layout.add_widget(self.text_input)
        
        self.data_display = TextInput(readonly=True, hint_text="Resultados de búsqueda", font_size=14, size_hint=(1, 0.4))
        layout.add_widget(self.data_display)
        
        button_layout = BoxLayout(orientation="horizontal", spacing=10, size_hint=(1, 0.2))
        close_button = Button(text="Cerrar", size_hint=(0.5, 1), background_color=(1,0,0,1))
        close_button.bind(on_press=lambda instance: App.get_running_app().stop())
        button_layout.add_widget(close_button)
        ingresar_button = Button(text="Ingresar", size_hint=(0.5,1), background_color=(0,0.5,1,1))
        ingresar_button.bind(on_press=self.open_second_window)
        button_layout.add_widget(ingresar_button)
        
        layout.add_widget(button_layout)
        self.add_widget(layout)
    
    def on_text_change(self, instance, value):
        cursor = conn.cursor()
        query = "SELECT campo1, campo2, campo3, campo4 FROM datos WHERE campo1 LIKE ?"
        param = ('%' + value + '%',)
        cursor.execute(query, param)
        rows = cursor.fetchall()
        results = "\n".join(" | ".join(row) for row in rows)
        self.data_display.text = results if results else "No se encontraron resultados."
    
    def open_second_window(self, instance):
        self.manager.current = "second"

# ----------------- PANTALLA DE LOGIN -----------------
class SecondScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="vertical", spacing=10, padding=20)
        layout.add_widget(Label(text="Login", font_size=20))
        
        self.password_input = TextInput(hint_text="Ingrese contraseña", password=True, font_size=16, size_hint=(1,0.2))
        layout.add_widget(self.password_input)
        
        self.error_label = Label(text="", font_size=14, color=(1,0,0,1), size_hint=(1,0.1))
        layout.add_widget(self.error_label)
        
        validate_button = Button(text="Validar", font_size=16, size_hint=(1,0.2), background_color=(0,0.5,1,1))
        validate_button.bind(on_press=self.validate_password)
        layout.add_widget(validate_button)
        
        back_button = Button(text="Volver", font_size=16, size_hint=(1,0.2), background_color=(1,0,0,1))
        back_button.bind(on_press=self.go_back_to_main)
        layout.add_widget(back_button)
        
        self.add_widget(layout)
    
    def validate_password(self, instance):
        if self.password_input.text == "admin123":
            self.error_label.text = ""
            self.password_input.text = ""
            self.manager.current = "matrix"
        else:
            self.error_label.text = "Contraseña incorrecta. Intente nuevamente."
    
    def go_back_to_main(self, instance):
        self.manager.current = "main"

# ----------------- PANTALLA MATRIX (Cinemática de lluvia de 0 y 1 con blinking de fondo) -----------------
class MatrixScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.flayout = FloatLayout()
        with self.flayout.canvas.before:
            self.bg_color = Color(0, 0, 0, 1)
            self.bg_rect = Rectangle(pos=(0, 0), size=Window.size)
        self.flayout.bind(pos=self.update_bg, size=self.update_bg)
        self.add_widget(self.flayout)
        
        self.matrix_label = Label(text="", font_size=18, color=(0, 1, 0, 1),
                                  size_hint=(1, 1), halign="center", valign="top")
        self.matrix_label.bind(size=self.matrix_label.setter('text_size'))
        self.flayout.add_widget(self.matrix_label)
        
        self.matrix_lines = []
        self.num_lines = 0
        self.num_digits = 0
        self.blink_state = False
    
    def update_bg(self, *args):
        self.bg_rect.pos = (0, 0)
        self.bg_rect.size = self.flayout.size
    
    def on_enter(self):
        self.matrix_label.text_size = self.size
        font_size = self.matrix_label.font_size
        self.num_lines = int(self.height / (font_size * 1.2))
        self.num_digits = int(self.width / (font_size * 0.6))
        self.matrix_lines = [' '.join(random.choice("01") for _ in range(self.num_digits))
                             for _ in range(self.num_lines)]
        self.event_phase1 = Clock.schedule_interval(self.update_matrix, 0.03)
        Clock.schedule_once(self.start_phase2, 3)
    
    def update_matrix(self, dt):
        new_line = ' '.join(random.choice("01") for _ in range(self.num_digits))
        self.matrix_lines.insert(0, new_line)
        self.matrix_lines.pop()
        self.matrix_label.text = "\n".join(self.matrix_lines)
        return True
    
    def start_phase2(self, dt):
        Clock.unschedule(self.event_phase1)
        self.matrix_label.text = "ES ACCESO APROVADO, INGRESANDO"
        self.matrix_label.font_size = 50
        self.matrix_label.halign = "center"
        self.matrix_label.valign = "middle"
        self.matrix_label.size_hint = (0.8, 0.3)
        self.matrix_label.pos_hint = {'center_x':0.5, 'center_y':0.5}
        self.event_blink = Clock.schedule_interval(self.blink_background, 0.5)
        Clock.schedule_once(self.finish_phase2, 3)
    
    def blink_background(self, dt):
        self.blink_state = not self.blink_state
        if self.blink_state:
            self.bg_color.rgba = (0, 0, 0, 1)
        else:
            self.bg_color.rgba = (0.8, 1, 0.8, 1)
        return True
    
    def finish_phase2(self, dt):
        Clock.unschedule(self.event_blink)
        self.bg_color.rgba = (0, 0, 0, 1)
        self.manager.current = "third"

# ----------------- PANTALLA DE CRUD -----------------
class ThirdScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="vertical", spacing=10, padding=20)
        
        row1 = BoxLayout(orientation="horizontal", size_hint=(1, 0.1))
        row1.add_widget(Label(text="Campo 1:", size_hint=(0.3, 1)))
        self.entry1 = TextInput(multiline=False, size_hint=(0.7, 1))
        row1.add_widget(self.entry1)
        layout.add_widget(row1)
        
        row2 = BoxLayout(orientation="horizontal", size_hint=(1, 0.1))
        row2.add_widget(Label(text="Campo 2:", size_hint=(0.3, 1)))
        self.entry2 = TextInput(multiline=False, size_hint=(0.7, 1))
        row2.add_widget(self.entry2)
        layout.add_widget(row2)
        
        row3 = BoxLayout(orientation="horizontal", size_hint=(1, 0.1))
        row3.add_widget(Label(text="Campo 3:", size_hint=(0.3, 1)))
        self.entry3 = TextInput(multiline=False, size_hint=(0.7, 1))
        row3.add_widget(self.entry3)
        layout.add_widget(row3)
        
        row4 = BoxLayout(orientation="horizontal", size_hint=(1, 0.1))
        row4.add_widget(Label(text="Campo 4:", size_hint=(0.3, 1)))
        self.entry4 = TextInput(multiline=False, size_hint=(0.7, 1))
        row4.add_widget(self.entry4)
        layout.add_widget(row4)
        
        button_layout = BoxLayout(orientation="horizontal", spacing=10, size_hint=(1, 0.2))
        add_button = Button(text="Agregar", background_color=(0, 1, 0, 1))
        add_button.bind(on_press=self.add_data)
        button_layout.add_widget(add_button)
        
        modify_button = Button(text="Modificar", background_color=(0, 0, 1, 1))
        modify_button.bind(on_press=self.open_modify_select)
        button_layout.add_widget(modify_button)
        
        backup_button = Button(text="Hacer back-up", background_color=(0.7, 0.7, 0.2, 1))
        backup_button.bind(on_press=self.hacer_backup)
        button_layout.add_widget(backup_button)
        
        recuperar_button = Button(text="Recuperar back-up", background_color=(0.7, 0.7, 0.2, 1))
        recuperar_button.bind(on_press=self.recuperar_backup)
        button_layout.add_widget(recuperar_button)
        
        volver_button = Button(text="Volver al inicio", background_color=(0.5, 0.5, 0.5, 1))
        volver_button.bind(on_press=self.go_back_to_main)
        button_layout.add_widget(volver_button)
        
        layout.add_widget(button_layout)
        self.add_widget(layout)
    
    def show_alert(self, title, message):
        content = BoxLayout(orientation="vertical", spacing=10, padding=10)
        content.add_widget(Label(text=message))
        close_btn = Button(text="Cerrar", size_hint=(1, 0.3))
        content.add_widget(close_btn)
        popup = Popup(title=title, content=content, size_hint=(0.6, 0.4))
        close_btn.bind(on_press=popup.dismiss)
        popup.open()
    
    def add_data(self, instance):
        campo1 = self.entry1.text.strip()
        campo2 = self.entry2.text.strip()
        campo3 = self.entry3.text.strip()
        campo4 = self.entry4.text.strip()
        if not (campo1 and campo2 and campo3 and campo4):
            self.show_alert("Error", "Debes rellenar los 4 campos.")
            return
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM datos WHERE campo1 = ?", (campo1,))
        exists = cursor.fetchone()
        if exists:
            self.show_alert("Error", "El item ya existe. Usa 'Modificar' para actualizarlo.")
        else:
            cursor.execute("INSERT INTO datos (campo1, campo2, campo3, campo4) VALUES (?, ?, ?, ?)",
                           (campo1, campo2, campo3, campo4))
            conn.commit()
            self.show_alert("Éxito", "Item agregado correctamente.")
    
    def open_modify_select(self, instance):
        self.manager.current = "modify"
    
    def go_back_to_main(self, instance):
        self.manager.current = "main"
    
    def hacer_backup(self, instance):
        try:
            conn.commit()
            shutil.copyfile("mi_base_de_datos.db", "mi_base_de_datos_backup.db")
            self.show_alert("Éxito", "Back-up realizado correctamente.")
        except Exception as e:
            self.show_alert("Error", f"Error al hacer back-up: {str(e)}")
    
    def recuperar_backup(self, instance):
        global conn
        try:
            conn.commit()
            conn.close()
            shutil.copyfile("mi_base_de_datos_backup.db", "mi_base_de_datos.db")
            conn = sqlite3.connect("mi_base_de_datos.db", check_same_thread=False)
            self.show_alert("Éxito", "Back-up recuperado correctamente.")
        except Exception as e:
            self.show_alert("Error", f"Error al recuperar back-up: {str(e)}")

# -------------- PANTALLA DE SELECCIÓN PARA MODIFICAR --------------
class ModifySelectScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="vertical", spacing=10)
        layout.add_widget(Label(text="Selecciona el item a modificar", font_size=20, size_hint=(1, 0.1)))
        scroll = ScrollView(size_hint=(1, 0.8))
        self.record_layout = BoxLayout(orientation="vertical", spacing=10, size_hint_y=None)
        self.record_layout.bind(minimum_height=self.record_layout.setter("height"))
        scroll.add_widget(self.record_layout)
        layout.add_widget(scroll)
        cancel_button = Button(text="Volver", size_hint=(1, 0.1), background_color=(1, 0, 0, 1))
        cancel_button.bind(on_press=self.go_back)
        layout.add_widget(cancel_button)
        self.add_widget(layout)
    
    def on_enter(self):
        self.record_layout.clear_widgets()
        cursor = conn.cursor()
        cursor.execute("SELECT id, campo1, campo2, campo3, campo4 FROM datos")
        records = cursor.fetchall()
        for record in records:
            btn_text = f"ID: {record[0]} | {record[1]} | {record[2]} | {record[3]} | {record[4]}"
            btn = Button(text=btn_text, size_hint_y=None, height=40)
            btn.bind(on_press=lambda inst, rec=record: self.select_record(rec))
            self.record_layout.add_widget(btn)
    
    def select_record(self, record):
        edit_screen = self.manager.get_screen("edit")
        edit_screen.set_record(record)
        self.manager.current = "edit"
    
    def go_back(self, instance):
        self.manager.current = "third"

# -------------- PANTALLA DE EDICIÓN DE REGISTRO --------------
class EditRecordScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="vertical", spacing=10, padding=20)
        layout.add_widget(Label(text="Editar Registro", font_size=20))
        row1 = BoxLayout(orientation="horizontal", size_hint=(1, 0.1))
        row1.add_widget(Label(text="Campo 1:", size_hint=(0.3, 1)))
        self.edit_entry1 = TextInput(multiline=False, size_hint=(0.7, 1))
        row1.add_widget(self.edit_entry1)
        layout.add_widget(row1)
        row2 = BoxLayout(orientation="horizontal", size_hint=(1, 0.1))
        row2.add_widget(Label(text="Campo 2:", size_hint=(0.3, 1)))
        self.edit_entry2 = TextInput(multiline=False, size_hint=(0.7, 1))
        row2.add_widget(self.edit_entry2)
        layout.add_widget(row2)
        row3 = BoxLayout(orientation="horizontal", size_hint=(1, 0.1))
        row3.add_widget(Label(text="Campo 3:", size_hint=(0.3, 1)))
        self.edit_entry3 = TextInput(multiline=False, size_hint=(0.7, 1))
        row3.add_widget(self.edit_entry3)
        layout.add_widget(row3)
        row4 = BoxLayout(orientation="horizontal", size_hint=(1, 0.1))
        row4.add_widget(Label(text="Campo 4:", size_hint=(0.3, 1)))
        self.edit_entry4 = TextInput(multiline=False, size_hint=(0.7, 1))
        row4.add_widget(self.edit_entry4)
        layout.add_widget(row4)
        
        btn_layout = BoxLayout(orientation="horizontal", spacing=10, size_hint=(1, 0.2))
        save_button = Button(text="Guardar", background_color=(0, 1, 0, 1))
        save_button.bind(on_press=self.save_changes)
        btn_layout.add_widget(save_button)
        delete_button = Button(text="Eliminar", background_color=(1, 0.5, 0, 1))
        delete_button.bind(on_press=self.delete_current_record)
        btn_layout.add_widget(delete_button)
        volver_button = Button(text="Volver", background_color=(1, 0, 0, 1))
        volver_button.bind(on_press=self.go_back)
        btn_layout.add_widget(volver_button)
        layout.add_widget(btn_layout)
        
        self.add_widget(layout)
        self.record_id = None
    
    def set_record(self, record):
        self.record_id = record[0]
        self.edit_entry1.text = record[1]
        self.edit_entry2.text = record[2]
        self.edit_entry3.text = record[3]
        self.edit_entry4.text = record[4]
    
    def save_changes(self, instance):
        campo1 = self.edit_entry1.text.strip()
        campo2 = self.edit_entry2.text.strip()
        campo3 = self.edit_entry3.text.strip()
        campo4 = self.edit_entry4.text.strip()
        if not (campo1 and campo2 and campo3 and campo4):
            self.show_alert("Error", "Debes rellenar los 4 campos.")
            return
        cursor = conn.cursor()
        cursor.execute("UPDATE datos SET campo1=?, campo2=?, campo3=?, campo4=? WHERE id=?",
                       (campo1, campo2, campo3, campo4, self.record_id))
        conn.commit()
        self.show_alert("Éxito", "Registro modificado correctamente.")
        self.manager.current = "third"
    
    def delete_current_record(self, instance):
        if self.record_id is None:
            self.show_alert("Error", "No hay registro seleccionado.")
            return
        cursor = conn.cursor()
        cursor.execute("DELETE FROM datos WHERE id=?", (self.record_id,))
        conn.commit()
        self.show_alert("Éxito", "Registro eliminado correctamente.")
        self.manager.current = "third"
    
    def show_alert(self, title, message):
        content = BoxLayout(orientation="vertical", spacing=10, padding=10)
        content.add_widget(Label(text=message))
        close_btn = Button(text="Cerrar", size_hint=(1, 0.3))
        content.add_widget(close_btn)
        popup = Popup(title=title, content=content, size_hint=(0.6, 0.4))
        close_btn.bind(on_press=popup.dismiss)
        popup.open()
    
    def go_back(self, instance):
        self.manager.current = "modify"

# ----------------- CLASE PRINCIPAL DE LA APLICACIÓN -----------------
class MyApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(SplashScreen(name="splash"))
        sm.add_widget(MainScreen(name="main"))
        sm.add_widget(SecondScreen(name="second"))
        sm.add_widget(MatrixScreen(name="matrix"))
        sm.add_widget(ThirdScreen(name="third"))
        sm.add_widget(ModifySelectScreen(name="modify"))
        sm.add_widget(EditRecordScreen(name="edit"))
        sm.current = "splash"
        return sm
    
    def on_stop(self):
        conn.close()

if __name__ == "__main__":
    MyApp().run()
