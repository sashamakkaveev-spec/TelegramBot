import json
import telebot
import requests


class WeatherBot:
    def __init__(self, token, api_key):
        self.bot = telebot.TeleBot(token)
        self.API_KEY = api_key
        self.setup_handlers()

    def setup_handlers(self):
        @self.bot.message_handler(commands=['start'])
        def start(message):
            self.handle_start(message)

        @self.bot.message_handler(content_types=['text'])
        def get_weather(message):
            self.handle_weather_message(message)

    def handle_start(self, message):
        self.bot.send_message(message.chat.id, 'Привет! Напиши город, погода в котором, тебя интересует.')

    def handle_weather_message(self, message):
        city = message.text.strip().lower()
        res = requests.get(
            f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={self.API_KEY}&units=metric')

        if res.status_code == 200:
            data = json.loads(res.text)

            weather = data["weather"][0]["main"]
            image = 'sun.png' if weather == 'Clear' else 'cloud.png'

            # Используем менеджер контекста для файла
            try:
                with open('./image/' + image, 'rb') as file:
                    self.bot.send_photo(message.chat.id, file)
            except FileNotFoundError:
                # Если файлы изображений недоступны (например, в тестах), просто пропускаем
                pass

            self.bot.send_message(message.chat.id, f'Температура на улице: {data["main"]["temp"]}°C\n'
                                                   f'Скорость ветра: {data["wind"]["speed"]}м/с')

            self.bot.send_message(message.chat.id, f'Если вновь захочешь узнать погоду, просто напиши город:)')
        else:
            self.bot.send_message(message.chat.id, f'Город указан неверно, попробуй еще раз.')

    def run(self):
        self.bot.polling(non_stop=True)


if __name__ == '__main__':
    token = '8073792544:AAHCD3Pre4XEUVXjvmE2MrP3GkfK3tScHK0'
    api_key = '8f71316ad4b0fcac82a281caf9619f97'

    weather_bot = WeatherBot(token, api_key)
    weather_bot.run()