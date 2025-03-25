import os
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.camera import Camera
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive


class GoogleDriveApp(App):
    def build(self):
        self.gauth = GoogleAuth()
        self.drive = None
        self.folder_id = None
        self.folders = {}  # Словарь для хранения доступных папок

        # Главный макет
        self.root_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Вкладки
        self.tabs = TabbedPanel(do_default_tab=False)
        
        # Вкладка: Создание папки
        self.create_tab = TabbedPanelItem(text='Создание папки')
        self.create_layout = BoxLayout(orientation='vertical', spacing=10)
        
        self.folder_name_input = TextInput(hint_text='Введите название папки', multiline=False)
        self.create_folder_button = Button(text='Создать папку', size_hint=(1, 0.3))
        self.create_folder_button.bind(on_press=self.create_folder)
        self.create_folder_button.disabled = True

        self.create_layout.add_widget(self.folder_name_input)
        self.create_layout.add_widget(self.create_folder_button)
        self.create_tab.add_widget(self.create_layout)

        # Вкладка: Сделать фото и загрузить
        self.camera_tab = TabbedPanelItem(text='Сделать фото')
        self.camera_layout = BoxLayout(orientation='vertical', spacing=10)
        
        self.folder_spinner = Spinner(text='Выберите папку', values=[], size_hint=(1, 0.3))
        self.camera_button = Button(text='Открыть камеру', size_hint=(1, 0.3))
        self.camera_button.bind(on_press=self.open_camera)
        self.camera_button.disabled = True

        self.camera_layout.add_widget(self.folder_spinner)
        self.camera_layout.add_widget(self.camera_button)
        self.camera_tab.add_widget(self.camera_layout)

        # Добавляем вкладки в панель
        self.tabs.add_widget(self.create_tab)
        self.tabs.add_widget(self.camera_tab)

        # Кнопка авторизации
        self.auth_button = Button(text='Авторизация с Google', size_hint=(1, 0.3))
        self.auth_button.bind(on_press=self.authenticate)

        # Информационное сообщение
        self.info_label = Label(text='Нажмите "Авторизация с Google" для начала работы.')

        # Добавляем виджеты в главный макет
        self.root_layout.add_widget(self.auth_button)
        self.root_layout.add_widget(self.info_label)
        self.root_layout.add_widget(self.tabs)

        return self.root_layout

    def authenticate(self, instance):
        """Авторизация с Google."""
        self.gauth.LocalWebserverAuth()
        self.drive = GoogleDrive(self.gauth)

        self.info_label.text = 'Авторизация прошла успешно!'
        self.auth_button.disabled = True
        self.create_folder_button.disabled = False
        self.camera_button.disabled = False

        self.load_folders()

    def load_folders(self):
        """Загружаем список существующих папок."""
        folder_list = self.drive.ListFile({'q': "mimeType='application/vnd.google-apps.folder' and trashed=false"}).GetList()
        self.folders = {folder['title']: folder['id'] for folder in folder_list}
        self.folder_spinner.values = list(self.folders.keys())
        self.info_label.text = 'Список папок обновлен.'

    def create_folder(self, instance):
        """Создание новой папки."""
        folder_name = self.folder_name_input.text.strip()
        if not folder_name:
            self.info_label.text = 'Введите название папки!'
            return

        folder = self.drive.CreateFile({'title': folder_name, 'mimeType': 'application/vnd.google-apps.folder'})
        folder.Upload()

        # Обновляем список папок
        self.load_folders()
        self.info_label.text = f'Папка "{folder_name}" успешно создана!'

    def open_camera(self, instance):
        """Открытие камеры и сохранение фото."""
        selected_folder = self.folder_spinner.text
        if selected_folder not in self.folders:
            self.info_label.text = 'Выберите существующую папку!'
            return

        # Открываем окно с камерой
        camera_layout = BoxLayout(orientation='vertical', spacing=10)
        camera = Camera(resolution=(640, 480), play=True)

        def capture_photo(instance):
            # Сохраняем снимок в файл
            photo_path = 'photo.png'
            camera.export_to_png(photo_path)
            popup.dismiss()
            self.upload_photo(photo_path, self.folders[selected_folder])

        capture_button = Button(text='Сделать фото', size_hint=(1, 0.2))
        capture_button.bind(on_press=capture_photo)

        camera_layout.add_widget(camera)
        camera_layout.add_widget(capture_button)

        popup = Popup(title="Камера", content=camera_layout, size_hint=(0.9, 0.9))
        popup.open()

    def upload_photo(self, photo_path, folder_id):
        """Загрузка сделанного фото в папку."""
        if not photo_path:
            self.info_label.text = 'Ошибка: файл не выбран.'
            return

        file = self.drive.CreateFile({'title': os.path.basename(photo_path), 'parents': [{'id': folder_id}]})
        file.SetContentFile(photo_path)
        file.Upload()

        self.info_label.text = f'Фото "{os.path.basename(photo_path)}" загружено в папку.'


if __name__ == '__main__':
    GoogleDriveApp().run()
