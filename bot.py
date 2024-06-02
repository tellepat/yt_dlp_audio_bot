import telebot
import yt_dlp
import os
from pydub import AudioSegment
import logging

# Настраиваем логирование
logging.basicConfig(level=logging.INFO)

# Получаем токен из переменной окружения
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    raise ValueError("Необходимо установить переменную окружения TELEGRAM_BOT_TOKEN")

bot = telebot.TeleBot(TOKEN)

# Указываем директорию для сохранения загруженных файлов
DOWNLOAD_DIR = 'downloads'
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Отправь мне ссылку на YouTube видео, и я скачаю для тебя аудио.")

@bot.message_handler(func=lambda message: True)
def download_audio(message):
    url = message.text
    bot.reply_to(message, "Начинаю загрузку аудио...")

    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            title = info_dict.get('title', None)
            filename = ydl.prepare_filename(info_dict).replace('.webm', '.mp3').replace('.m4a', '.mp3')

        # Полный путь к файлу
        filename = os.path.join(DOWNLOAD_DIR, os.path.basename(filename))
        file_size = os.path.getsize(filename)
        logging.info(f"Downloaded file size: {file_size}")

        if file_size > MAX_FILE_SIZE:
            audio = AudioSegment.from_mp3(filename)
            duration = len(audio)
            logging.info(f"Audio duration: {duration} ms")
            part_duration = int((MAX_FILE_SIZE / file_size) * duration)
            logging.info(f"Part duration: {part_duration} ms")
            parts = [audio[i:i + part_duration] for i in range(0, len(audio), part_duration)]

            for i, part in enumerate(parts):
                part_filename = f"{filename[:-4]}_part{i + 1}.mp3"
                logging.info(f"Exporting part {i + 1} to {part_filename}")
                part.export(part_filename, format="mp3")
                with open(part_filename, 'rb') as audio_part:
                    logging.info(f"Sending part {i + 1}")
                    bot.send_audio(message.chat.id, audio_part)
                os.remove(part_filename)
        else:
            with open(filename, 'rb') as audio:
                logging.info("Sending full audio")
                bot.send_audio(message.chat.id, audio)

        os.remove(filename)
        bot.reply_to(message, "Аудио успешно загружено и отправлено!")

    except Exception as e:
        logging.error(f"Error: {str(e)}")
        bot.reply_to(message, f"Произошла ошибка: {str(e)}")

# Запускаем бота
bot.polling()
