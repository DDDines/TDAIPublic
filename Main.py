#main.py

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QTableWidgetItem, QMessageBox, QLineEdit, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit
from backend import loadDataFromSheets, searchAndGenerate, writeData
import logging
from threading import Thread


class SearchDialog(QtWidgets.QDialog):
    centralwidget = None

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Pesquisa em andamento...")
        self.resize(600, 600)
        layout = QVBoxLayout(self)

        # Label de progresso
        self.progressLabel = QLabel(self)
        self.progressLabel.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.progressLabel)

        # Barra de progresso
        self.progressBar = QtWidgets.QProgressBar(self)
        layout.addWidget(self.progressBar)

        # Caixa de texto para logs
        self.logTextEdit = QTextEdit(self)
        self.logTextEdit.setReadOnly(True)
        layout.addWidget(self.logTextEdit)

        # Resultados da pesquisa
        self.resultList = QtWidgets.QListWidget(self)
        self.resultList.setHidden(True)
        layout.addWidget(self.resultList)

        # Botão de OK
        self.okButton = QtWidgets.QPushButton(self)
        self.okButton.setText("OK")
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.okButton.clicked.connect(self.accept)
        layout.addWidget(self.okButton)

        self.setLayout(layout)

        # Conexão dos sinais do SearchThread
        self.searchThread = SearchThread()
        self.searchThread.progressChanged.connect(self.updateProgress)
        self.searchThread.statusChanged.connect(self.updateStatus)
        self.searchThread.logChanged.connect(self.updateLogs)

        # Inicia a thread
        self.searchThread.start()

        # Cria um QTimer para atualizar a janela a cada 100 milissegundos
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(100)

    def update(self):
        # Atualiza a janela de pesquisa para mostrar as informações mais recentes
        QtWidgets.QApplication.processEvents()

    def updateProgress(self, value):
        self.progressBar.setValue(value)

    def updateStatus(self, status):
        self.progressLabel.setText(status)

    def updateLogs(self, log):
        # Atualiza o QTextEdit com as informações de log
        self.logTextEdit.append(log)

class SearchThread(QtCore.QThread):
    progressChanged = QtCore.pyqtSignal(int)
    statusChanged = QtCore.pyqtSignal(str)
    logChanged = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.values = loadDataFromSheets()

    def run(self):
        total_rows = len(self.values)
        for row_num, row_data in enumerate(self.values):
            item_info = row_data[2:5]
            query = row_data[1]

            if all(item_info) and query:
                self.logChanged.emit(
                    f"Pesquisando '{query}' com informações adicionais: {item_info}")
                title, description = searchAndGenerate(*item_info)  # Unpack item_info into separate arguments


                if title.strip() and description.strip():
                    self.values[row_num][3] = title
                    self.values[row_num][4] = description
                    writeData([title, description], row_num)

            # Atualiza a barra de progresso e o status da janela de pesquisa
            self.progressChanged.emit(row_num + 1)
            self.statusChanged.emit(
                f"Pesquisando... ({row_num+1}/{total_rows})")
            self.logChanged.emit("Pesquisa e registro concluídos.")

class Interface(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        # adicionando um título à janela
        self.setWindowTitle("Pesquisar Dados")

        # adicionando um ícone à janela
        self.setWindowIcon(QtGui.QIcon('icon.png'))

        # Definindo o tamanho mínimo da janela
        self.setMinimumSize(800, 600)

        # centralizando a janela na tela
        self.centerOnScreen()

        self.setupUi()
        self.loadData()

    def centerOnScreen(self):
        # Centralizando a janela na tela
        resolution = QtWidgets.QDesktopWidget().screenGeometry()
        self.setGeometry(
            int((resolution.width() / 2) - (self.frameSize().width() / 2)),
            int((resolution.height() / 2) - (self.frameSize().height() / 2)),
            self.frameSize().width(),
            self.frameSize().height())

    def setupUi(self):
            self.centralwidget = QtWidgets.QWidget(self)
            self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
            self.gridLayout.setContentsMargins(10, 10, 10, 10)
            self.gridLayout.setSpacing(10)

            # Adicionando um label para cada coluna
            self.colLabels = []
            for i in range(5):
                label = QLabel(self.centralwidget)
                label.setText(f"Col{i+1}")
                self.gridLayout.addWidget(label, 0, i)

            # Adicionando uma tabela para exibir os dados da planilha
            self.tableWidget = QtWidgets.QTableWidget(self.centralwidget)
            self.tableWidget.setRowCount(0)
            self.tableWidget.setColumnCount(5)
            self.gridLayout.addWidget(self.tableWidget, 1, 0, 1, 5)

            # Adicionando um campo de texto para futuros exemplos
            self.textEdit = QtWidgets.QTextEdit(self.centralwidget)
            self.textEdit.setText("Estribo Scania Serie 4")
            self.gridLayout.addWidget(self.textEdit, 1, 5, 3, 1)
            self.textEdit.setMaximumWidth(int(self.width() * 0.40))

            # Adicionando um campo de pesquisa para permitir a busca rápida dos dados, e um botão "Pesquisar" para executar
            self.searchBox = QLineEdit(self.centralwidget)
            self.searchBox.setPlaceholderText("Consulta de pesquisa")
            self.gridLayout.addWidget(self.searchBox, 2, 0, 1, 4)
            self.searchButton = QtWidgets.QPushButton(self.centralwidget)
            self.searchButton.setToolTip('Pesquisar')
            self.searchButton.setIcon(QtGui.QIcon('search.png'))
            self.searchButton.setText("Pesquisar")
            self.gridLayout.addWidget(self.searchButton, 2, 4)

            # Conectando os botões a suas respectivas funções
            self.searchButton.clicked.connect(self.searchData)

            # Adicionando um botão para atualizar os dados da planilha
            self.refreshButton = QtWidgets.QPushButton(self.centralwidget)
            self.refreshButton.setToolTip('Atualizar')
            self.refreshButton.setIcon(QtGui.QIcon('refresh.png'))
            self.refreshButton.setText("Atualizar")
            self.gridLayout.addWidget(self.refreshButton, 3, 0, 1, 5)

            self.centralwidget.setLayout(self.gridLayout)
            self.setCentralWidget(self.centralwidget)

            self.refreshButton.clicked.connect(self.loadData)
            self.tableWidget.horizontalHeader().setSectionResizeMode(
                QtWidgets.QHeaderView.Stretch)

    def loadData(self):
        values = loadDataFromSheets()
        if values is not None:
            self.tableWidget.setRowCount(len(values))
        for row_num, row_data in enumerate(values):
            self.tableWidget.setRowCount(row_num + 1)
            for col_num, col_data in enumerate(row_data):
                self.tableWidget.setItem(
                    row_num, col_num, QTableWidgetItem(col_data))
        self.statusBar().showMessage(
            f"{len(values)} linhas carregadas.", 2000)

    def searchData(self):
        query = self.searchBox.text().strip()
        total_rows = self.tableWidget.rowCount()

        if not query:
            query = ""  # Define a consulta vazia para pesquisar apenas com base nos dados da tabela

        self.searchDialog = SearchDialog(self)
        self.searchDialog.progressLabel.setText("Carregando...")
        self.searchDialog.progressBar.setRange(0, total_rows)
        self.searchDialog.show()
        QtWidgets.QApplication.processEvents()

        search_thread = SearchThread()
        search_thread.start()

        while search_thread.isRunning():
            QtWidgets.QApplication.processEvents()

        self.searchDialog.hide()
        self.loadData()

        num_results = self.searchDialog.resultList.count()
        if num_results > 0:
            self.searchDialog.resultList.setHidden(False)
            self.statusBar().showMessage(
                f"A consulta '{query}' retornou {num_results} resultados.", 2000)
        else:
            QMessageBox.information(
                self, 'Pesquisa Concluída', 'Nenhum resultado encontrado.'
            )

        self.searchDialog.exec_()


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = Interface()
    window.show()
    sys.exit(app.exec_())


#backend.py

import os
import gspread
import pickle
import json
import logging
from typing import List, Tuple
from googlesearch import search
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from transformers import TFGPT2LMHeadModel, GPT2Tokenizer, AutoModelForCausalLM, AutoTokenizer
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Configuração do logger
logging.basicConfig(filename='log.txt', level=logging.INFO)

# Spreadsheet constants
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SAMPLE_SPREADSHEET_ID = '1nSQih5Dbb4IRKUca1hnGeC_tD5m5_yhCFQFK80tXMuw'

# Initialize GPT-2 model and tokenizer
MODEL_NAME = 'gpt2'
model = TFGPT2LMHeadModel.from_pretrained(MODEL_NAME)
tokenizer = GPT2Tokenizer.from_pretrained(MODEL_NAME)

def authenticate():
    creds = None
    token_path = "token.pickle"  # Caminho para o arquivo de token

    # Verifica se o arquivo de token já existe
    if os.path.exists(token_path):
        with open(token_path, "rb") as token:
            creds = pickle.load(token)

    # Se não houver credenciais válidas, gera uma nova
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentialsOAuth.json", SCOPES)
            creds = flow.run_local_server(port=0)

        # Salva as credenciais no arquivo de token para uso posterior
        with open(token_path, "wb") as token:
            pickle.dump(creds, token)

    return creds

def loadKeys():
    with open("Keys.json", "r") as keys_file:
        keys_data = json.load(keys_file)
    return keys_data

def loadDataFromSheets():
    creds = authenticate()
    gc = gspread.authorize(creds)
    sheet = gc.open_by_key(SAMPLE_SPREADSHEET_ID).worksheet("Data")
    values = sheet.get_all_values()

    # Excluir o cabeçalho da lista de valores
    values = values[1:]

    return values

def search_google(service, query, cse_id, **kwargs):
    res = service.cse().list(q=query, cx=cse_id, num=10, **kwargs).execute()
    return res['items'] if 'items' in res else None

def generate_text(model, prompt, max_length=100, temperature=0.7, top_p=0.9):
    input_ids = tokenizer.encode(prompt, return_tensors='pt')
    output = model.generate(input_ids, max_length=max_length, temperature=temperature, top_p=top_p)
    text = tokenizer.decode(output[0], skip_special_tokens=True)
    return text

def searchAndGenerate(item_name: str, item_category: str, item_third_info: str) -> Tuple[str, str]:
    model = TFGPT2LMHeadModel.from_pretrained("gpt2")
    tokenizer = GPT2Tokenizer.from_pretrained("gpt2")

    # use item_info to generate a query
    query = item_name + " " + item_category  # Modify this line as needed

    # search for information about the item and generate text
    snippets = search(query)
    text = generate_text(model, tokenizer, snippets)

    # generate a title and a description
    title = generate_title(text)
    description = generate_description(text)

    return title, description

def generate_from_template(item_info):
    if len(item_info) >= 2:
        title = f"{item_info[0]} {item_info[1]}"
        description = f"This is a {item_info[0]} {item_info[1]}."
        return title, description
    else:
        return "", ""

def writeData(data, row_num):
    creds = authenticate()
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SAMPLE_SPREADSHEET_ID)
    worksheet = sh.worksheet('Data')

    cell_list = worksheet.range(f"D{row_num+2}:E{row_num+2}")
    cell_list[0].value = data[0]  # Título
    cell_list[1].value = data[1]  # Descrição
    worksheet.update_cells(cell_list)
