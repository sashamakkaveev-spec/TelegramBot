import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

with patch('telebot.TeleBot'):
    from src.bot import WeatherBot


class TestWeatherBot(unittest.TestCase):

    def setUp(self):
        """Настройка перед каждым тестом"""
        self.mock_bot = Mock()

        self.telebot_patcher = patch('bot.telebot.TeleBot', return_value=self.mock_bot)
        self.mock_telebot = self.telebot_patcher.start()

        self.weather_bot = WeatherBot('fake_token:12345', 'test_api_key')

        self.mock_message = Mock()
        self.mock_message.chat.id = 12345
        self.mock_message.text = "Test City"

    def tearDown(self):
        """Очистка после каждого теста"""
        self.telebot_patcher.stop()

    def test_bot_initialization(self):
        """Тест инициализации бота"""
        self.mock_telebot.assert_called_once_with('fake_token:12345')
        self.assertEqual(self.weather_bot.API_KEY, 'test_api_key')

    def test_handle_start(self):
        """Тест обработки команды /start"""
        self.weather_bot.handle_start(self.mock_message)

        # Проверяем, что бот отправил правильное сообщение
        self.mock_bot.send_message.assert_called_once_with(
            12345,
            'Привет! Напиши город, погода в котором, тебя интересует.'
        )

    @patch('bot.requests.get')
    def test_handle_weather_message_success(self, mock_get):
        """Тест успешного запроса погоды"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"weather":[{"main":"Clear"}],"main":{"temp":15.5},"wind":{"speed":3.5}}'
        mock_get.return_value = mock_response

        self.mock_message.text = "London"

        self.weather_bot.handle_weather_message(self.mock_message)

        # Проверяем вызов API
        expected_url = 'https://api.openweathermap.org/data/2.5/weather?q=london&appid=test_api_key&units=metric'
        mock_get.assert_called_once_with(expected_url)

        self.assertEqual(self.mock_bot.send_message.call_count, 2)

        weather_call = self.mock_bot.send_message.call_args_list[0]
        self.assertIn("15.5°C", weather_call[0][1])
        self.assertIn("3.5м/с", weather_call[0][1])

        reminder_call = self.mock_bot.send_message.call_args_list[1]
        self.assertIn("напиши город", reminder_call[0][1])

    @patch('bot.requests.get')
    def test_handle_weather_message_cloudy(self, mock_get):
        """Тест погоды с облаками"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"weather":[{"main":"Clouds"}],"main":{"temp":10},"wind":{"speed":2}}'
        mock_get.return_value = mock_response

        self.mock_message.text = "Moscow"

        self.weather_bot.handle_weather_message(self.mock_message)

        # Проверяем, что API был вызван с правильным городом
        mock_get.assert_called_once_with(
            'https://api.openweathermap.org/data/2.5/weather?q=moscow&appid=test_api_key&units=metric'
        )

    @patch('bot.requests.get')
    def test_handle_weather_message_city_not_found(self, mock_get):
        """Тест запроса с неверным городом"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        self.mock_message.text = "InvalidCityName"

        self.weather_bot.handle_weather_message(self.mock_message)

        # Проверяем сообщение об ошибке
        self.mock_bot.send_message.assert_called_once_with(
            12345,
            'Город указан неверно, попробуй еще раз.'
        )

    @patch('bot.requests.get')
    def test_city_name_normalization(self, mock_get):
        """Тест нормализации названия города"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"weather":[{"main":"Clear"}],"main":{"temp":20},"wind":{"speed":1}}'
        mock_get.return_value = mock_response

        # Город с пробелами и разным регистром
        self.mock_message.text = "  New York  "

        self.weather_bot.handle_weather_message(self.mock_message)

        # Проверяем, что город нормализован (приведен к нижнему регистру и убраны пробелы)
        mock_get.assert_called_once_with(
            'https://api.openweathermap.org/data/2.5/weather?q=new york&appid=test_api_key&units=metric'
        )

    @patch('bot.requests.get')
    @patch('builtins.open')
    def test_photo_sending_for_clear_weather(self, mock_open, mock_get):
        """Тест отправки фото для ясной погоды"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"weather":[{"main":"Clear"}],"main":{"temp":25},"wind":{"speed":1}}'
        mock_get.return_value = mock_response

        mock_file = MagicMock()
        mock_file.__enter__ = Mock(return_value=mock_file)
        mock_file.__exit__ = Mock(return_value=None)
        mock_open.return_value = mock_file

        self.mock_message.text = "Paris"

        self.weather_bot.handle_weather_message(self.mock_message)

        # Проверяем, что открыт файл с солнцем
        mock_open.assert_called_with('./image/sun.png', 'rb')
        # Проверяем отправку фото
        self.mock_bot.send_photo.assert_called_once_with(12345, mock_file)

    @patch('bot.requests.get')
    @patch('builtins.open')
    def test_photo_sending_for_cloudy_weather(self, mock_open, mock_get):
        """Тест отправки фото для облачной погоды"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"weather":[{"main":"Rain"}],"main":{"temp":15},"wind":{"speed":5}}'
        mock_get.return_value = mock_response

        mock_file = MagicMock()
        mock_file.__enter__ = Mock(return_value=mock_file)
        mock_file.__exit__ = Mock(return_value=None)
        mock_open.return_value = mock_file

        self.mock_message.text = "Berlin"

        self.weather_bot.handle_weather_message(self.mock_message)

        # Проверяем, что открыт файл с облаком
        mock_open.assert_called_with('./image/cloud.png', 'rb')
        # Проверяем отправку фото
        self.mock_bot.send_photo.assert_called_once_with(12345, mock_file)


if __name__ == '__main__':
    unittest.main()