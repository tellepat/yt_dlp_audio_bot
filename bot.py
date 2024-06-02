import telebot
import yt_dlp
import os
import subprocess

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


def split_audio(filename, max_file_size):
    output_files = []
    file_size = os.path.getsize(filename)

    if file_size <= max_file_size:
        return [filename]

    audio_duration = float(subprocess.check_output(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1',
         filename]
    ).strip())

    part_duration = audio_duration / (file_size // max_file_size + 1)

    base, ext = os.path.splitext(filename)
    index = 0
    start_time = 0

    while start_time < audio_duration:
        part_filename = f"{base}_part{index + 1}{ext}"
        command = [
            'ffmpeg', '-i', filename, '-ss', str(start_time), '-t', str(part_duration), part_filename
        ]
        subprocess.run(command)
        output_files.append(part_filename)
        start_time += part_duration
        index += 1

    return output_files


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

        audio_files = split_audio(filename, MAX_FILE_SIZE)

        for audio_file in audio_files:
            with open(audio_file, 'rb') as audio:
                bot.send_audio(message.chat.id, audio)
            os.remove(audio_file)

        bot.reply_to(message, "Аудио успешно загружено и отправлено!")

    except Exception as e:
        bot.reply_to(message, f"Произошла ошибка: {str(e)}")


# Запускаем бота
bot.polling()
