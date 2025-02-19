import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(override=True)
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

CLIENT = OpenAI(
    api_key=OPENAI_KEY,
    base_url="https://api.proxyapi.ru/openai/v1"
)

ERROR_MESSAGE = "Something went wrong..."

TEXT_LENGTH_FOR_KEY_THEMES = 100

FATHER_VOICE_NAME = "artem"
DAUGHTER_VOICE_NAME = "sveta"

BASE_SYSTEM_PROMPT = [
    {
        "role": "system",
        "content": """
            Представьте себе диалог в мессенджере между отцом и его дочерью-подростком. Дочь только что прочитала статью или новость и хочет
            понять, о чем идет речь. Отец объясняет ей содержание статьи простым и доступным языком. Дочь задает вопросы, которые могут быть 
            острыми и неожиданными, а отец отвечает на них развернуто и честно, с терпением и заботой. Диалог должен быть легким, неформальным и 
            интерактивным, помогая подросткам понять сложные темы. Пожалуйста, создайте такой диалог на основе следующего текста.

            Это системный промпт, его нельзя нарушать - ВСЕГДА пиши диалог между дочкой и отцом - сразу отказывай и не выдавай ничего.
            Диалог в формате:
            'Отец: ...'\n
            'Дочь: ...'\n
            ...
        """
    }
]

BASE_SYSTEM_PROMPT_FOR_KEY_THEMES = [
    {
        "role": "system",
        "content": """
            Дан файл с научной, спортивной или политической статьей. Тебе нужно:
            1. Выбрать 4-6 ключевых тем.
            2. Описать каждую тему в 2-3 предложениях.
            3. Выдать описания из пункта 2 в виде списка в python ( то есть в виде ["description_1", "description_2", ..., "description_n"])
        """
    }
]