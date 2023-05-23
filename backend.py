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
