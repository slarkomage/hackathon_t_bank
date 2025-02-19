import requests
import json
import PyPDF2
from pydantic import BaseModel
from bs4 import BeautifulSoup
import re
import logging
import shutil
import uuid
import os

SHARED_DIR = "/app/shared"
ERROR_FILE_NOT_FOUND = "File not found"

# Настройка логгирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')



def send_querry_to_model(querry: str):
    try:
        logging.info(f"Sending query to model: {querry[:50]}...")
        response = requests.post(
            "http://model:8000/generate",
            json={"querry": querry}
        )
        response.raise_for_status()
        
        model_data = response.json()
        logging.info(f"Received response from model: {model_data}")
        return model_data
    except requests.RequestException as e:
        logging.error(f"Error occurred while sending query to model: {e}")
        raise Exception(f"Error communicating with model service: {e}")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise


def extract_dialogue(text):
    """
    Extract dialogue from text in the new format
    """
    try:
        logging.info("Extracting dialogue from text")
        # Разделяем текст на строки
        lines = text.split('\n')
        
        responses = []
        current_speaker = None
        current_text = []

        for line in lines:
            logging.info(f"Processing line: {line}")
            line = line.strip("'")
            line = line.strip()
            
            if not line:
                continue
            
            if line.startswith(r'Отец:') or line.startswith('Дочь:'):
                # Если у нас есть предыдущий говорящий, добавляем его реплику
                if current_speaker and current_text:
                    response_text = ' '.join(current_text).strip()
                    if current_speaker == "Отец":
                        responses.append({"type": "father", "text": response_text})
                    else:
                        responses.append({"type": "daughter", "text": response_text})
                    current_text = []
                
                current_speaker = line.split(':')[0]
                current_text.append(':'.join(line.split(':')[1:]).strip())
            elif line.startswith('Key themes:'):
                # Игнорируем блок с описаниями
                break
            else:
                # Продолжение реплики текущего говорящего
                current_text.append(line)
        
        # Добавляем последнюю реплику, если она есть
        if current_speaker and current_text:
            response_text = ' '.join(current_text).strip()
            if current_speaker == "Отец":
                responses.append({"type": "father", "text": f"Отец говорит: {response_text}"})
            else:
                responses.append({"type": "daughter", "text": f"Дочь спрашивает: {response_text}"})
        
        logging.info(f"Extracted {len(responses)} dialogue responses")
        return responses
    except Exception as e:
        logging.error(f"Error occurred while extracting dialogue: {e}")
        return []


def get_audio_file(querry: str):
    """
    Get the audio file name and responses from the model
    """
    try:
        logging.info("Getting audio file and responses from model")
        model_data_response = send_querry_to_model(querry)
        response, audio_filename = model_data_response["generated_text"], model_data_response["audio_filename"]
        logging.info(f"Received response from model: {response}")
        responses = extract_dialogue(response)

        # generating random filename for frontend
        new_file_name = f"{uuid.uuid4()}.wav"
        shutil.copy(os.path.join(SHARED_DIR, audio_filename), os.path.join(SHARED_DIR, new_file_name))
        logging.info(f"Audio file copied to {os.path.join(SHARED_DIR, new_file_name)}")
        return {"responses": responses, "audioSrc": f"/shared/{new_file_name}"}
    except Exception as e:
        logging.error(f"Error occurred while getting audio file: {e}")
        return {"responses": "error", "audioSrc": ""}
    

def pdf_to_text(pdf_path):
    """
    Makes text from pdf file
    """
    text = ""
    try:
        logging.info(f"Converting PDF to text: {pdf_path}")
        with open(pdf_path, 'rb') as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                for encoding in ['utf-8', 'windows-1251', 'cp1251', 'koi8-r', 'iso-8859-5']:
                    try:
                        text += page_text.encode(encoding).decode('utf-8')
                        break
                    except UnicodeEncodeError:
                        continue
        logging.info("PDF successfully converted to text")
        return text
    except FileNotFoundError:
        logging.error(f"PDF file not found: {pdf_path}")
        return ERROR_FILE_NOT_FOUND


def txt_to_text(text_path):
    """
    Makes text from txt file
    """
    encodings = ['utf-8', 'windows-1251', 'cp1251', 'koi8-r', 'iso-8859-5']
    for encoding in encodings:
        try:
            logging.info(f"Attempting to read text file with encoding: {encoding}")
            with open(text_path, 'r', encoding=encoding) as txt_file:
                text = txt_file.read()
                logging.info("Text file successfully read")
                return text
        except UnicodeDecodeError:
            logging.warning(f"Failed to decode with encoding: {encoding}")
            continue
    logging.error(f"Failed to read text file with all attempted encodings: {text_path}")
    return ERROR_FILE_NOT_FOUND


def parse_file(file_name):
    """
    Parses file
    """
    try:
        file_path = os.path.join(SHARED_DIR, file_name)
        logging.info(f"Parsing file: {file_path}")
    
        if file_path.endswith('.pdf'):
            return pdf_to_text(file_path)
        elif file_path.endswith('.txt'):
            return txt_to_text(file_path)
        else:
            logging.error(f"Unsupported file format: {file_path}")
            return ERROR_FILE_NOT_FOUND
    except FileNotFoundError:
        logging.error(f"File not found: {file_path}")
        return ERROR_FILE_NOT_FOUND
    

def parse_rbc_link(link):
    """
    Парсит ссылку RBC для получения текста статьи
    """
    try:
        logging.info(f"Parsing RBC link: {link}")
        # Get page content
        response = requests.get(link)
        response.raise_for_status()
        
        # Create BeautifulSoup object to parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract article title
        title = soup.find('h1', class_='article__header__title-in').text.strip()
        
        # Extract article text
        article_body = soup.find('div', class_='article__text article__text_free')
        
        # Extract all paragraphs
        paragraphs = article_body.find_all('p')
        
        # Join text of all paragraphs
        article_text = ' '.join([p.get_text(strip=True) for p in paragraphs])
        
        # Form full article text
        full_text = f"{title}\n\n{article_text}"
        
        logging.info("Successfully parsed RBC article")
        return full_text
    except Exception as e:
        logging.error(f"Error occurred while parsing RBC link: {e}")
        return ERROR_FILE_NOT_FOUND


def parse_tinkoff_journal_link(link):
    """
    Parses Tinkoff Journal link to get article text
    """
    try:
        logging.info(f"Parsing Tinkoff Journal link: {link}")
        # Get page content
        response = requests.get(link)
        response.raise_for_status()
        
        # Create BeautifulSoup object to parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract article title from twitter:title meta tag
        title = soup.find('meta', attrs={'name': 'twitter:title'})['content']
        
        # Extract article text
        paragraphs = soup.find_all('p', class_='_paragraph_1nuxh_4')
        article_text = ' '.join([p.get_text(separator=' ', strip=True) for p in paragraphs])
        
        # Form full article text
        full_text = f"{title}\n\n{article_text}"
        
        logging.info("Successfully parsed Tinkoff Journal article")
        return full_text
    except Exception as e:
        logging.error(f"Error occurred while parsing Tinkoff Journal link: {e}")
        return ERROR_FILE_NOT_FOUND
    
    

def parse_habr_link(link):
    """
    Parses Habr link to get article text
    """
    try:
        logging.info(f"Parsing Habr link: {link}")
        # Get page content
        response = requests.get(link)
        response.raise_for_status()
        
        # Create BeautifulSoup object to parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract article title from twitter:title meta tag
        title = soup.find('title').text
        
        # Extract article text
        paragraphs = soup.find_all('div', class_='article-formatted-body')
        article_text = ' '.join([p.get_text(separator=' ', strip=True) for p in paragraphs])

        # Form full article text
        full_text = f"{title}\n\n{article_text}"
        
        logging.info("Successfully parsed Habr article")
        return full_text
    except Exception as e:
        logging.error(f"Error occurred while parsing Habr link: {e}")
        return ERROR_FILE_NOT_FOUND


def parse_championat_link(link):
    """
    Парсит ссылку Championat.com для получения текста статьи
    """
    try:
        logging.info(f"Parsing Championat link: {link}")
        # Получаем содержимое страницы
        response = requests.get(link)
        response.raise_for_status()
        
        # Создаем объект BeautifulSoup для парсинга HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Извлекаем заголовок статьи из тега title
        title = soup.find('title').text.strip()
        
        # Извлекаем текст статьи
        article_content = soup.find('div', class_='match__live-text')
        if article_content:
            paragraphs = article_content.find_all('p')
            article_text = ' '.join([p.get_text(strip=True) for p in paragraphs])
        else:
            article_text = "Текст статьи не найден."
        
        # Формируем полный текст статьи
        full_text = f"{title}\n\n{article_text}"
        
        logging.info("Successfully parsed Championat article")
        return full_text
    except Exception as e:
        logging.error(f"Error occurred while parsing Championat link: {e}")
        return ERROR_FILE_NOT_FOUND


def parse_arxiv_link(link):
    """
    Парсит ссылку arXiv.org и скачивает PDF-файл статьи
    """
    try:
        logging.info(f"Parsing arXiv link: {link}")
        # Получаем содержимое страницы
        response = requests.get(link)
        response.raise_for_status()
        
        # Создаем объект BeautifulSoup для парсинга HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Извлекаем заголовок статьи
        title = soup.find('h1', class_='title mathjax').text.strip().replace('Title:', '').strip()
        
        # Находим ссылку на PDF-файл
        pdf_link = soup.find('a', {'href': lambda href: href and href.startswith('/pdf/')})
        
        if pdf_link:
            pdf_url = f"https://arxiv.org{pdf_link['href']}"
            
            # Скачиваем PDF-файл
            pdf_response = requests.get(pdf_url)
            pdf_response.raise_for_status()
            
            # Создаем имя файла из заголовка статьи
            file_name = f"{title.replace(' ', '_')[:50]}.pdf"
            file_path = os.path.join(SHARED_DIR, file_name)
            
            # Сохраняем PDF-файл
            with open(file_path, 'wb') as file:
                file.write(pdf_response.content)
            
            logging.info(f"Successfully downloaded PDF file: {file_name}")
            return f"PDF-файл '{file_name}' успешно скачан и сохранен в папке '{SHARED_DIR}'."
        else:
            logging.warning("PDF link not found in arXiv page")
            return "Ссылка на PDF-файл не найдена."
    except Exception as e:
        logging.error(f"Error occurred while parsing arXiv link: {e}")
        return f"Произошла ошибка при парсинге arXiv: {str(e)}"




def parse_url(url):
    """
    Общая функция для парсинга URL. Выбирает соответствующий парсер
    в зависимости от домена и возвращает текст статьи.
    """
    try:
        logging.info(f"Parsing URL: {url}")
        if 'rbc.ru' in url:
            return parse_rbc_link(url)
        elif 'journal.tinkoff.ru' in url:
            return parse_tinkoff_journal_link(url)
        elif 'habr.com' in url:
            return parse_habr_link(url)
        elif 'championat.com' in url:
            return parse_championat_link(url)
        elif 'arxiv.org' in url:
            # Для arXiv сначала скачиваем PDF, затем извлекаем текст
            pdf_result = parse_arxiv_link(url)
            if pdf_result.startswith("PDF-файл"):
                # Извлекаем имя файла из сообщения
                file_name = re.search(r"'(.+?)'", pdf_result).group(1)
                file_path = os.path.join(SHARED_DIR, file_name)
                # Извлекаем текст из PDF
                return pdf_to_text(file_path)
            else:
                return pdf_result  # Возвращаем сообщение об ошибке, если PDF не был скачан
        else:
            logging.warning(f"Unsupported URL: {url}")
            return "Unsupported URL. Cannot parse this website."
    except Exception as e:
        logging.error(f"An error occurred while parsing the URL: {e}")
        return f"An error occurred while parsing the URL: {str(e)}"

