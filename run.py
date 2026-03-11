#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Запуск музейного бота
"""

import os
import sys
import logging
from datetime import datetime


def setup_logging():
    """Настройка логирования"""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    if not os.path.exists('logs'):
        os.makedirs('logs')

    log_filename = f"logs/bot_{datetime.now().strftime('%Y%m%d')}.log"

    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )


def check_token():
    token = os.environ.get('BOT_TOKEN')
    if token:
        return token

    print("Введите токен бота (получить у @BotFather):")
    token = input().strip()

    if token:
        os.environ['BOT_TOKEN'] = token
        return token
    else:
        print("Ошибка: токен не может быть пустым!")
        sys.exit(1)


def main():
    print("=" * 50)
    print("Запуск музейного Telegram бота")
    print("=" * 50)

    setup_logging()
    logger = logging.getLogger(__name__)

    token = check_token()

    try:
        with open('museum_bot_simple.py', 'r', encoding='utf-8') as f:
            content = f.read()

        if '8156140134:AAGouWNzQs-QKBRNmB8De3-rK0H_OcmrpqI' in content:
            content = content.replace('8156140134:AAGouWNzQs-QKBRNmB8De3-rK0H_OcmrpqI', token)

            with open('museum_bot_simple.py', 'w', encoding='utf-8') as f:
                f.write(content)

            logger.info("Токен успешно установлен")
    except Exception as e:
        logger.error(f"Ошибка при установке токена: {e}")

    try:
        import museum_bot_simple
    except ImportError as e:
        logger.error(f"Ошибка импорта бота: {e}")
        print("\nУбедитесь, что все файлы находятся в одной папке:")
        print("- museum_bot_simple.py")
        print("- database_sqlite.py")
        print("- models_sqlite.py")
        sys.exit(1)


if __name__ == '__main__':
    main()