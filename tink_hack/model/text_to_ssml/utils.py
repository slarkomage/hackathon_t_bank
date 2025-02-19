import asyncio
import logging
import re
from typing import List, Dict

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import BASE_SYSTEM_PROMPT, BASE_SYSTEM_PROMPT_FOR_KEY_THEMES, CLIENT, FATHER_VOICE_NAME,\
      DAUGHTER_VOICE_NAME, ERROR_MESSAGE, TEXT_LENGTH_FOR_KEY_THEMES
from gpt_classification import check_text_coherence
from sslm_upgrading import upgrade_sslm

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def get_key_themes_from_text(text: str) -> List[str]:
    """
    Extract key themes from text to add them to the prompt in main query
    """
    try:
        logging.info("Extracting key themes from text")
        themes = await ask_gpt(text, BASE_SYSTEM_PROMPT_FOR_KEY_THEMES)
        logging.info(f"Extracted key themes: {themes}")
        return themes
    except Exception as e:
        logging.error(f"Error occurred while getting key themes: {e}")
        return ERROR_MESSAGE


async def ask_gpt(user_message: str, base_system_prompt: List[Dict]) -> str:
    """
    Send request to GPT
    """
    try:
        logging.info("Sending request to GPT")
        all_messages = base_system_prompt.copy()
        all_messages.append({"role": "user", "content": user_message})
    
        response = await asyncio.to_thread(
            CLIENT.chat.completions.create,
            model="gpt-4o-mini",
            messages=all_messages,
            max_tokens=1500,
            temperature=0.7
        )

        gpt_answer = response.choices[0].message.content
        logging.info("Received response from GPT")
        return gpt_answer
    except Exception as e:
        logging.error(f"Error occurred while asking GPT: {e}")
        return ERROR_MESSAGE


async def gpt_dialog_from_string(text: str) -> str:
    """
    Get final dialog from GPT (str with dialog)
    """
    try:
        logging.info("Generating dialog from string")
        if len(text) >= TEXT_LENGTH_FOR_KEY_THEMES:
            logging.info("Text is long enough, getting key themes")
            key_themes = await get_key_themes_from_text(text)
            text += f"\n\nKey themes, add them to the dialog: {key_themes}"
        result = await ask_gpt(text, BASE_SYSTEM_PROMPT)
        final_result = result + f"\n\nKey themes: {key_themes}" if 'key_themes' in locals() else result
        logging.info("Dialog generated successfully")
        return final_result
    except Exception as e:
        logging.error(f"Error occurred while getting final result: {e}")
        return ERROR_MESSAGE


async def extract_dialogue(text):
    """
    Extract dialogue from text [{'father': 'line'}, {'daughter': 'line'}]
    """
    try:
        logging.info("Extracting dialogue from text")
        pattern = r"(Дочь|Отец):\s*(.+?)(?=(?:Дочь|Отец):|$)"
        matches = re.findall(pattern, text, re.DOTALL)

        dialogue = []
        for speaker, line in matches:
            if speaker == "Отец":
                dialogue.append({'father': line.strip()})
            elif speaker == "Дочь":
                dialogue.append({'daughter': line.strip()})
        
        logging.info(f"Extracted {len(dialogue)} lines of dialogue")
        return dialogue
    except Exception as e:
        logging.error(f"Error occurred while extracting dialogue: {e}")
        return []


async def generate_ssml(dialogue: List[Dict]) -> str:
    """
    Generate SSML from dialogue
    """
    try:
        logging.info("Generating SSML from dialogue")
        ssml = "<speak>\n"
        for line in dialogue:
            if 'father' in line:
                ssml += f'  <voice name="{FATHER_VOICE_NAME}">\n'
                ssml += f'    <p>\n      <s>{line["father"]}</s>\n    </p>\n'
                ssml += f'  </voice>\n'
            elif 'daughter' in line:
                ssml += f'  <voice name="{DAUGHTER_VOICE_NAME}">\n'
                ssml += f'    <p>\n      <s>{line["daughter"]}</s>\n    </p>\n'
                ssml += f'  </voice>\n'
        ssml += "</speak>"
        logging.info("SSML generated successfully")
        return ssml
    except Exception as e:
        logging.error(f"Error occurred while generating SSML: {e}")
        return ERROR_MESSAGE


async def get_text_from_string(text: str) -> str:
    """
    Get text from file
    """
    try:
        logging.info("Processing text from string")
        is_normal_text = await check_text_coherence(text)
        if not is_normal_text:
            logging.warning("Text coherence check failed")
            return ERROR_MESSAGE
        
        dialog_in_one_string = await gpt_dialog_from_string(text)
        if dialog_in_one_string == ERROR_MESSAGE:
            logging.error("Failed to generate dialog from string")
            return ERROR_MESSAGE
        
        dialogue = await extract_dialogue(dialog_in_one_string)
        if len(dialogue) == 0:
            logging.warning("No dialogue extracted from text")
            return ERROR_MESSAGE
        
        ssml = await generate_ssml(dialogue)
        if ssml == ERROR_MESSAGE:
            logging.error("Failed to generate SSML")
            return ERROR_MESSAGE
        
        # upgraded_ssml = await upgrade_sslm(ssml)
        logging.info("Text processing completed successfully")
        # return upgraded_ssml
        return ssml, dialog_in_one_string
    except Exception as e:
        logging.error(f"Error occurred while getting text from string: {e}")
        return ERROR_MESSAGE
