import openai
import aiogram
import asyncio
from config import *

import traceback
import logging

import asyncio
import logging
import sys
from aiogram import *

from aiogram import Bot, Dispatcher, Router, types
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.utils.markdown import hbold

# Bot token can be obtained via https://t.me/BotFather
TOKEN = TELEGRAM_BOT_TOKEN
openai.api_key = OPENAI_API_KEY
admin_key = ADMIN_KEY
system_message = SYSTEM_MESSAGE

openai.Model.list()

# All handlers should be attached to the Router (or Dispatcher)
router = Router()

dialogues = {}
dialogue = []
role_system = {"role": "system", "content": system_message}

# The function checks whether the message is an administrative one.
def check_admin_messages(input_string):
    
    global system_message
    global dialogues
    target_phrase = admin_key
    
    if target_phrase in input_string:
        index = input_string.index(target_phrase)
        remaining_text = input_string[index + len(target_phrase):]
        
        # add rool
        # if "add:" in remaining_text:
        #     comand = remaining_text.split("add:", 1)[1].strip()
        #     system_message = comand + system_message
        #     for dialogue_key, messages in dialogues.items():
        #         for message in messages:
        #             if message["role"] == "system":
        #                 message["content"] = system_message
                
        #     # print("system_message = ", dialogues)
        #     return True
        # else:
        #     return False
        
        if "get_sys:" in remaining_text:
            return system_message
        elif "put_sys:" in remaining_text:
            comand = remaining_text.split("put_sys:", 1)[1].strip()
            system_message = comand
            for dialogue_key, messages in dialogues.items():
                for message in messages:
                    if message["role"] == "system":
                        message["content"] = system_message
            return "Системный промт успешно изменен"
        else:
            return False
        
        
    else:
        return False
    

# The function of sending requests to openai
async def ai(prompt):    
    global dialogue
    dialogue.append({"role": "user", "content": prompt})
    try:        
        response = openai.ChatCompletion.create(
            model = "gpt-3.5-turbo",
            messages = dialogue,
            max_tokens=256,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )   
        dialogue.append({"role": "assistant", "content": response.choices[0].message.content})
         
        return response.choices[0].message.content
        
    except Exception:
        logging.error(traceback.format_exc())
        return None              
    

# This handler receives messages with `/start` command
@router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer("Здравствуйте! Это рекрутинговый бот компании Latoken. \n\nЯ могу рассказат Вам о нашей компании, предоставить список текущих вакансий, объяснить порядок трудоустройства кандидатов. Вы можете задать мне любые вопросы, связанные с трудоустройством в компанию Latoken. \n\nПожалуйста познакомтесь сначала с нашей компание и пройдите тесты, перейдя по ссылкам https://deliver.latoken.com/about  и  https://deliver.latoken.com/hackathon  \n\nПосле того, как Вы познакомитесь с предложенной информацией, я буду готов ответить на Ваши вопросы.")


# Handler will forward receive a message back to the sender
@router.message()
async def echo_handler(message: types.Message) -> None:
    rezult = check_admin_messages(message.text)
    if rezult:
        await message.reply(rezult)
    
    else:
        global dialogues
        global  dialogue
        user_id = message.from_user.id
        
        if user_id in dialogues:
            dialogue = dialogues[user_id]
        else:
            dialogue = [
                {"role": "system", "content": system_message}
            ]
        
        try:
            await message.reply("Пожалуйста ожидайте. Ваш запрос обрабатывается...")
            answer = await ai(message.text)
            
            if answer != None:
                await message.reply(answer)
            dialogues[user_id] = dialogue
        except Exception:
            logging.error(traceback.format_exc())
            await message.answer("Неизвестная ошибка. Попробуйте еще раз!")


async def main() -> None:
    dp = Dispatcher()
    dp.include_router(router)

    bot = Bot(TOKEN, parse_mode=ParseMode.HTML)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped!")
