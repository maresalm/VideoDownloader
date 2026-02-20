import sys
import os
from PyQt5 import QtCore, QtWidgets, QtGui
#from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,QWidget, QLabel, QLineEdit, QPushButton,QProgressBar, QComboBox, QFileDialog, QMessageBox,QStackedWidget, QFrame)
#from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
#from PyQt5.QtGui import QFont,QIcon
import pytubefix



def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class VideoInfoThread(QtCore.QThread):
    """Video bilgilerini almak için thread"""
    info_received = QtCore.pyqtSignal(dict)
    error_occurred = QtCore.pyqtSignal(str)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        try:
            yt = pytubefix.YouTube(self.url)
            print(yt)
            # Video bilgilerini topla
            info = {
                'title': yt.title,
                'author': yt.author,
                'length': yt.length,
                'views': yt.views,
                'description': yt.description[:500] + "..." if len(yt.description) > 500 else yt.description,
                'thumbnail_url': yt.thumbnail_url,
                'streams': []
            }
            # Mevcut stream'leri al
            for stream in yt.streams.filter(adaptive=True):
                stream_info = {
                    'itag': stream.itag,
                    'resolution': stream.resolution or 'Audio Only',
                    
                    'file_extension': stream.subtype,
                    'filesize': stream.filesize,
                    'stream': stream
                }
                print(stream)
                info['streams'].append(stream_info)

            self.info_received.emit(info)

        except Exception as e:
            self.error_occurred.emit(f"Hata: {str(e)}")


class DownloadThread(QtCore.QThread):
    """İndirme işlemi için thread"""
    progress_updated = QtCore.pyqtSignal(int)
    download_completed = QtCore.pyqtSignal(str)
    error_occurred = QtCore.pyqtSignal(str)

    def __init__(self, stream, output_path):
        super().__init__()
        self.stream = stream
        self.output_path = output_path

    def run(self):
        try:
            self.stream.download(output_path=self.output_path)
            self.download_completed.emit("Download is Succesfuly completed !")
        except Exception as e:
            self.error_occurred.emit(f"Downloading Error: {str(e)}")


class YouTubeDownloader(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_video_info = None
        self.selected_stream = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Video Download Manager")
        self.setGeometry(100, 100, 800, 600)
        self.setMinimumSize(600, 400)
        self.setWindowIcon(QtGui.QIcon(resource_path("icon.png")))

        # Ana widget ve layout
        main_widget = QtWidgets.QWidget()
        self.setCentralWidget(main_widget)

        # Stacked widget - sayfa geçişleri için
        self.stacked_widget = QtWidgets.QStackedWidget()

        # Ana layout
        main_layout = QtWidgets.QVBoxLayout(main_widget)
        main_layout.addWidget(self.stacked_widget)

        # Sayfaları oluştur
        self.create_search_page()
        self.create_download_page()

        # İlk sayfayı göster
        self.stacked_widget.setCurrentIndex(0)

    def create_search_page(self):
        """Arama sayfası oluştur"""
        search_page =QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(search_page)

        # Başlık
        title_label = QtWidgets.QLabel("Video Download Manager")
        title_label.setAlignment(QtCore.Qt.AlignCenter)
        title_font =QtGui.QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # Boşluk
        layout.addStretch()

        # URL giriş alanı
        url_layout = QtWidgets.QVBoxLayout()

        url_label = QtWidgets.QLabel("Video Link:")
        url_label.setFont(QtGui.QFont("Arial", 12))
        url_layout.addWidget(url_label)

        self.url_input =QtWidgets.QLineEdit()
        self.url_input.setPlaceholderText(
            "https://www.video.com/watch?v=...")
        self.url_input.setFont(QtGui.QFont("Arial", 11))
        self.url_input.setMinimumHeight(40)
        self.url_input.textChanged.connect(self.on_url_changed)
        url_layout.addWidget(self.url_input)

        layout.addLayout(url_layout)

        # Arama butonu
        self.search_button = QtWidgets.QPushButton("Take Video Information")
        self.search_button.setEnabled(False)
        self.search_button.setMinimumHeight(45)
        self.search_button.setFont(QtGui.QFont("Arial", 12, QtGui.QFont.Bold))
        self.search_button.setStyleSheet("""
            QPushButton:enabled {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
                border: none;
                border-radius: 5px;
            }
            QPushButton:enabled:hover {
                background-color: #45a049;
            }
        """)
        self.search_button.clicked.connect(self.search_video)
        layout.addWidget(self.search_button)

        # Boşluk
        layout.addStretch()

        self.stacked_widget.addWidget(search_page)

    def create_download_page(self):
        """İndirme sayfası oluştur"""
        download_page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(download_page)

        # Geri butonu
        back_button = QtWidgets.QPushButton("← Back")
        back_button.setMaximumWidth(100)
        back_button.clicked.connect(self.go_back)
        back_button.setStyleSheet("""QPushButton{
            background-color: #2196F3;
            color: white;
            border: none;
            border-radius: 5px;}
            QPushButton:hover{
                background-color: #1085E2;
                color: white;
                border: none;
                border-radius: 5px;}"""
            )
        layout.addWidget(back_button)

        # Video bilgileri alanı
        info_frame = QtWidgets.QFrame()
        info_frame.setFrameStyle(QtWidgets.QFrame.Box)
        info_layout =QtWidgets.QVBoxLayout(info_frame)

        self.video_title = QtWidgets.QLabel()
        self.video_title.setFont(QtGui.QFont("Arial", 14,QtGui.QFont.Bold))
        self.video_title.setWordWrap(True)
        info_layout.addWidget(self.video_title)

        self.video_author = QtWidgets.QLabel()
        self.video_author.setFont(QtGui.QFont("Arial", 10))
        info_layout.addWidget(self.video_author)

        self.video_stats = QtWidgets.QLabel()
        self.video_stats.setFont(QtGui.QFont("Arial", 10))
        info_layout.addWidget(self.video_stats)

        layout.addWidget(info_frame)

        # Kalite seçimi
        quality_layout = QtWidgets.QHBoxLayout()

        quality_label = QtWidgets.QLabel("Choose Quality:")
        quality_label.setFont(QtGui.QFont("Arial", 12))
        quality_layout.addWidget(quality_label)

        self.quality_combo =QtWidgets.QComboBox()
        self.quality_combo.setMinimumHeight(35)
        quality_layout.addWidget(self.quality_combo)

        layout.addLayout(quality_layout)

        # İndirme yolu seçimi
        path_layout = QtWidgets.QHBoxLayout()

        path_label = QtWidgets.QLabel("Download Path:")
        path_label.setFont(QtGui.QFont("Arial", 12))
        path_layout.addWidget(path_label)

        self.path_input = QtWidgets.QLineEdit()
        self.path_input.setText(os.path.expanduser("~/Downloads"))
        path_layout.addWidget(self.path_input)

        browse_button = QtWidgets.QPushButton("Browse")
        browse_button.clicked.connect(self.browse_folder)
        browse_button.setStyleSheet("""QPushButton{
            background-color: #2196F3;
            color: white;
            border: none;
            border-radius: 5px;}
            QPushButton:hover{
                background-color: #1085E2;
                color: white;
                border: none;
                border-radius: 5px;}"""
            )
        path_layout.addWidget(browse_button)
        

        layout.addLayout(path_layout)

        # İndirme butonu
        self.download_button = QtWidgets.QPushButton("Download")
        self.download_button.setMinimumHeight(45)
        self.download_button.setFont(QtGui.QFont("Arial", 12, QtGui.QFont.Bold))
        self.download_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        self.download_button.clicked.connect(self.start_download)
        layout.addWidget(self.download_button)

        # Progress bar
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Durum etiketi
        self.status_label = QtWidgets.QLabel()
        self.status_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.status_label)

        self.stacked_widget.addWidget(download_page)

    def on_url_changed(self):
        """URL değiştiğinde çağrılır"""
        url = self.url_input.text().strip()
        # Basit URL doğrulaması
        is_valid = url and ("youtube.com/watch" in url or "youtu.be/" in url)
        self.search_button.setEnabled(is_valid)

    def search_video(self):
        """Video bilgilerini al"""
        url = self.url_input.text().strip()

        self.search_button.setText("Loading ...")
        self.search_button.setEnabled(False)

        # Video bilgilerini almak için thread başlat
        self.video_thread = VideoInfoThread(url)
        self.video_thread.info_received.connect(self.on_video_info_received)
        self.video_thread.error_occurred.connect(self.on_search_error)
        self.video_thread.start()

    def on_video_info_received(self, info):
        """Video bilgileri alındığında çağrılır"""
        self.current_video_info = info

        # Video bilgilerini göster
        self.video_title.setText(info['title'])
        self.video_author.setText(f"Channel: {info['author']}")

        # İstatistikleri formatla
        duration_mins = info['length'] // 60
        duration_secs = info['length'] % 60
        views_formatted = f"{info['views']:,}".replace(',', '.')

        self.video_stats.setText(f"Duration: {duration_mins}:{duration_secs:02d} | Views: {views_formatted}")

        # Kalite seçeneklerini doldur
        self.quality_combo.clear()
        for stream_info in info['streams']:
            size_mb = stream_info['filesize'] / \
                (1024 * 1024) if stream_info['filesize'] else 0
            combo_text = f"{stream_info['resolution']} - {stream_info['file_extension']} ({size_mb:.1f} MB)"
            self.quality_combo.addItem(combo_text, stream_info)

        # İndirme sayfasına geç
        self.stacked_widget.setCurrentIndex(1)

        # Arama butonunu sıfırla
        self.search_button.setText("Take Video Information")
        self.search_button.setEnabled(True)

    def on_search_error(self, error_message):
        """Arama hatası durumunda çağrılır"""
        QtWidgets.QMessageBox.critical(self, "Error", error_message)

        self.search_button.setText("Take Video Information")
        self.search_button.setEnabled(True)

    def go_back(self):
        """Ana sayfaya dön"""
        self.stacked_widget.setCurrentIndex(0)
        self.status_label.setText("")
        self.progress_bar.setVisible(False)

    def browse_folder(self):
        """Klasör seç"""
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Choose Downloading Folder")
        if folder:
            self.path_input.setText(folder)

    def start_download(self):
        """İndirmeyi başlat"""
        if not self.current_video_info:
            return

        # Seçili stream'i al
        current_data = self.quality_combo.currentData()
        if not current_data:
            return

        output_path = self.path_input.text().strip()
        if not output_path or not os.path.exists(output_path):
            QtWidgets.QMessageBox.warning(
                self, "Attention", "Choose Valid Path !")
            return

        # UI'yi indirme moduna geçir
        self.download_button.setText("Downloading...")
        self.download_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Downloading Start...")

        # İndirme thread'ini başlat
        self.download_thread = DownloadThread(
            current_data['stream'], output_path)
        self.download_thread.download_completed.connect(
            self.on_download_completed)
        self.download_thread.error_occurred.connect(self.on_download_error)
        self.download_thread.start()

        # Sahte progress için timer (pytube progress callback karmaşık olabiliyor)
        self.progress_timer =QtCore.QTimer()
        self.progress_timer.timeout.connect(self.update_fake_progress)
        self.progress_value = 0
        self.progress_timer.start(200)

    def update_fake_progress(self):
        """Sahte progress güncellemesi"""
        self.progress_value += 2
        if self.progress_value >= 90:
            self.progress_timer.stop()
        self.progress_bar.setValue(self.progress_value)

    def on_download_completed(self, message):
        """İndirme tamamlandığında çağrılır"""
        self.progress_timer.stop()
        self.progress_bar.setValue(100)
        self.status_label.setText(message)

        self.download_button.setText("Download")
        self.download_button.setEnabled(True)

        QtWidgets.QMessageBox.information(self, "Succesful", "Video Succesfuly downloaded!")

    def on_download_error(self, error_message):
        """İndirme hatası durumunda çağrılır"""
        self.progress_timer.stop()
        self.progress_bar.setVisible(False)
        self.status_label.setText("")

        self.download_button.setText("Download")
        self.download_button.setEnabled(True)

        QtWidgets.QMessageBox.critical(self, "Download Error", error_message)


def main():
    app = QtWidgets.QApplication(sys.argv)

    # Başlangıçta pytube versiyonunu kontrol et
    try:
        import pytube
        print(f"Pytube versiyonu: {pytube.__version__}")
    except:
        print("Pytube versiyonu tespit edilemedi")

    # Uygulama stili
    app.setStyleSheet("""
        QMainWindow {
            background-color: #f0f0f0;
        }
        QLabel {
            color: #333333;
        }
        QLineEdit {
            padding: 8px;
            border: 2px solid #ddd;
            border-radius: 5px;
            font-size: 11px;
        }
        QLineEdit:focus {
            border-color: #4CAF50;
        }
        QComboBox {
            padding: 5px;
            border: 2px solid #ddd;
            border-radius: 5px;
        }
        QPushButton {
            padding: 8px;
            border-radius: 5px;
            font-weight: bold;
        }
        QFrame {
            background-color: white;
            border-radius: 8px;
            padding: 10px;
        }
    """)

    # Hata durumunda kullanıcıya yardımcı mesaj göster
    try:
        window = YouTubeDownloader()
        window.show()

        # İlk açılışta ipuçları göster
        QtCore.QTimer.singleShot(1000, lambda: show_tips_if_needed())

    except Exception as e:
        QtWidgets.QMessageBox.critical(None, "Başlatma Hatası",
                             f"Uygulama başlatılırken hata oluştu:\n{ str(e)}\n\n"
                             f"Çözüm önerileri:\n"
                             f"1. pip install --upgrade pytube\n"
                             f"2. pip install PyQt5")
        return

    sys.exit(app.exec_())


def show_tips_if_needed():
    """İpuçlarını göster"""
    msg = QtWidgets.QMessageBox()
    msg.setWindowTitle("Kullanım İpuçları")
    msg.setText("HTTP 400 hatası alırsanız şu çözümleri deneyin:")
    msg.setDetailedText("""
1. Pytube'u güncelleyin:
   pip install --upgrade pytube

2. Alternatif olarak yt-dlp kullanın:
   pip install yt-dlp

3. VPN kullanarak farklı bir IP'den deneyin

4. Video linkinin doğru ve erişilebilir olduğundan emin olun

5. Video gizli/kısıtlı ise indirilemeyebilir

6. Birkaç dakika sonra tekrar deneyin
""")
    msg.setIcon(QtWidgets.QMessageBox.Information)
    msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
    # msg.exec_()  # Otomatik göstermeyi kapatıyoruz


if __name__ == '__main__':
    main()
