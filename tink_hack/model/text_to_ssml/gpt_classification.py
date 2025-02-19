import asyncio
import logging
from config import CLIENT, ERROR_MESSAGE


async def check_text_coherence(text: str) -> bool:
    """
    Функция для проверки связности и адекватности текста.
    
    Args:
        text (str): Текст для проверки
        api_key (str): API ключ OpenAI
        
    Returns:
        bool: True если текст связный и адекватный, False в противном случае
    """

    prompt = f"""
    Проанализируйте статью на связность и адекватность.
    Ответьте только True или False, где:
    True - статья связная, предложения логически связаны между собой
    False - статья несвязная, нелогичная или бессмысленная/вообще не похожа на статью

    Текст для анализа:
    {text}
    
    Ответ (только True или False):
    """

    try:
        response = await asyncio.to_thread(
            CLIENT.chat.completions.create,
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Вы - эксперт по анализу текстов. Отвечайте только True или False"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )
    
        
        result = response.choices[0].message.content.strip().lower()
        print(result)
        return True if 'true' in result else False

    except Exception as e:
        logging.error(f"Error occurred while getting final result: {e}")
        return ERROR_MESSAGE
