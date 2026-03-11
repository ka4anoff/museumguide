from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from models_sqlite import Base, MuseumInfo, Exhibition, Event, User, Booking
from datetime import datetime, timedelta
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self, db_path='museum_bot.db'):
        self.db_path = db_path
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)

        self.engine = create_engine(
            f'sqlite:///{db_path}',
            connect_args={'check_same_thread': False},
            echo=False
        )

        self.Session = sessionmaker(bind=self.engine)

    @contextmanager
    def session_scope(self):
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Ошибка базы данных: {e}")
            raise
        finally:
            session.close()

    def init_db(self):
        """Создание всех таблиц"""
        Base.metadata.create_all(self.engine)
        logger.info(f"База данных создана: {self.db_path}")

    def populate_initial_data(self):
        with self.session_scope() as session:
            if session.query(MuseumInfo).first():
                logger.info("База данных уже содержит данные")
                return

            museum = MuseumInfo(
                name='Самарский областной художественный музей',
                address='ул. Куйбышева, 92, Самара',
                work_hours='10:00 - 20:00 (ежедневно)',
                phone='+7 (905) 37 238-65',
                website='artmus.ru/',
                price_info='Стоимость входного билета: дети до 16 лет - бесплатно, взрослые – 100 рублей, пенсионеры – 50 рублей.',
                description='Крупнейший музей искусства в Самаре, известен своими неповторимыми экспозициями и интересными лекциями для жителей города а так же гостей. Самарский областной художественный музей был основан в 1897 году. Инициатором его создания выступил местный художник и меценат Константин Павлович Головкин. Изначально он был организован как художественный отдел при Самарском Публичном музее на основе коллекции, переданной в дар местными художниками.',
                latitude=53.18950318640915,
                longitude=50.08982722328036,
                main_image='https://samara.travel/upload/iblock/eee/eeefeaaa4f5815045cbfcfcdb0d59685.jpg',
                gallery_images='https://samara.travel/upload/iblock/ea1/xfeh6boh84vhp633z14efijbedpc20ch.jpg'
            )
            session.add(museum)

            main_exhibition = Exhibition(
                name='Обзорная экскурсия',
                description='Включает знакомство с собранием музея, формированием  уникальной коллекции, а именно: русского религиозного искусства, русского светского искусства XVIII-XX вв., авангарда, западноевропейского искусства и коллекции Востока.',
                type='permanent',
                is_active=True,
                poster_image='https://gmgs.ru/wp-content/uploads/2021/09/IMG_20210823_132310_198-792x500.jpg'
            )
            session.add(main_exhibition)
            session.flush()

            temp_exhibitions = [
                Exhibition(
                    name='Современное искусство 2026',
                    description='Экспозиция представляет широкий срез актуального художественного процесса в России — от признанных мастеров до молодых авторов. Здесь живопись и графика соседствуют со скульптурой, арт-фотографией и экспериментальными формами. Выставка демонстрирует всё многообразие стилей и направлений: от преемственности классической школы и академического реализма до смелых поисков современных импрессионистов и концептуалистов. Это уникальная возможность увидеть, как художники осмысляют вечные ценности и вызовы сегодняшнего дня, создавая многоголосый портрет современной России.',
                    type='temporary',
                    start_date=datetime(2026, 3, 1),
                    end_date=datetime(2026, 5, 30),
                    curator='Анна Иванова',
                    poster_image='https://habrastorage.org/getpro/habr/upload_files/1d8/0c9/db0/1d80c9db0571f795726cc409933803b2.jpg'
                ),
                Exhibition(
                    name='Фотография 20 века',
                    description='Приглашаем вас в путешествие по драматичному и великому XX столетию, увиденному через объектив фотокамеры. Экспозиция охватывает путь фотографии от авангардных экспериментов 1920-х до философских наблюдений 1980-х. Вы увидите, как менялся визуальный язык: от пикториализма, подражающего живописи, к жесткому документальному репортажу и смелым опытам фотоавангарда Александра Родченко и Эль Лисицкого .',
                    type='temporary',
                    start_date=datetime(2026, 4, 15),
                    end_date=datetime(2026, 7, 15),
                    curator='Петр Сидоров',
                    poster_image='https://fotoblick.ru/upload/images/pervie_fotoapparati.jpg'
                ),
                Exhibition(
                    name='Великие имена русского пейзажа',
                    description='Экскурсия предназначена для зрителей всех возрастов и познакомит с коллекцией пейзажного искусства XVIII-XX вв. Наш музей располагает большим количеством произведений замечательных русских художников:  родоначальников жанра - Сильвестра Щедрина и Михаила Лебедева, мастера морского пейзажа Ивана Айвазовского, тонкого знатока природы Алексея Саврасова, популярного пейзажиста Ивана Шишкина, знаменитого мастера среднерусского пейзажа Исаака Левитана, а также пейзажами А.И.Куинджи, К.Ф. Богаевского, Н.К. Рериха, Д.Д. Бурлюка и других. Посетители смогут познакомиться с разными типами пейзажа, научатся различать их оттенки, узнают о сложной и подчас трагической судьбе русских художников.',
                    type='temporary',
                    start_date=datetime(2026, 4, 1),
                    end_date=datetime(2026, 5, 30),
                    curator='Анна Сидорова',
                    poster_image='https://artmus.ru/content/upload/images/W9oM8FIJrqw(1).jpg'
                )
            ]
            session.add_all(temp_exhibitions)

            now = datetime.now()
            events = [
                Event(
                    name='Обзорная экскурсия по музею',
                    description='Знакомство с основными экспонатами и историей музея',
                    event_type='excursion',
                    start_datetime=now.replace(hour=15, minute=0) + timedelta(days=1),
                    price='300 руб.',
                    max_participants=20,
                    location='Главный холл',
                    organizer='Отдел экскурсий',
                    contact_phone='+7 (905) 37 238-65',
                    poster_image='https://dynamic-media-cdn.tripadvisor.com/media/photo-o/2b/9b/0a/f1/08032024.jpg?w=900&h=-1&s=1',
                    is_active=True
                ),
                Event(
                    name='Лекция "Искусство Возрождения"',
                    description='Лекция посвящена эволюции искусства в Италии в период кватроченто и чинквеченто (XV–XVI века). Мы проследим путь от первых робких шагов Джотто к уверенному реализму Мазаччо, от поисков идеала у Боттичелли к титанической мощи Микеланджело.',
                    event_type='lecture',
                    start_datetime=now.replace(hour=18, minute=0) + timedelta(days=2),
                    price='200 руб.',
                    max_participants=50,
                    location='Лекционный зал',
                    organizer='Лекторий музея',
                    contact_phone='+7 (905) 37 238-65',
                    poster_image='https://artmus.ru/content/upload/images/XxsugWKVK-Q.jpg',
                    is_active=True
                ),
                Event(
                    name='Мастер-класс для детей',
                    description='Краткий мастер-класс по живописи гуашью для детей. Знакомство с материалом, смешивание красок и создание яркого рисунка. Идеально для первого опыта в рисовании. Все материалы включены. Продолжительность: 120 минут.',
                    event_type='masterclass',
                    start_datetime=now.replace(hour=12, minute=0) + timedelta(days=3),
                    price='400 руб.',
                    max_participants=15,
                    location='Детская студия',
                    organizer='Детский центр',
                    contact_phone='+7 (905) 37 238-65',
                    poster_image='https://pic.rtbcdn.ru/video/49/75/4975b97be5bf3a63af17a4e4a86afb01.jpg',
                    is_active=True
                ),
                Event(
                    name='Экскурсия Женские образы в изобразительном искусстве XVIII – XIX вв"',
                    description='Тематическая экскурсия посвящена образу женщины в русском изобразительном искусстве XVIII-XX вв, её роли в обществе на определенных исторических этапах. Прослеживается эволюция моды, идеала красоты, национальные традиции. Предметной основой данной экскурсии являются произведения художников: Ф.С. Рокотова, В.Л. Боровиковского, Б.М. Кустодиева, Г. Сердюкова, В.А. Тропинина, Н.Крамского, В.Е. Маковского, В.И. Сурикова и др.',
                    event_type='excursion',
                    start_datetime=now.replace(hour=18, minute=0) + timedelta(days=2),
                    price='200 руб.',
                    max_participants=50,
                    location='Главный холл',
                    organizer='Лекторий музея',
                    contact_phone='+7 (905) 37 238-65',
                    poster_image='https://artmus.ru/content/upload/images/h3ZoFT7jEjY.jpg',
                    is_active=True
                ),
                Event(
                    name='Лики, излучающие свет"',
                    description='Экскурсовод расскажет гостям, что такое икона, чем отличается икона от портрета, об особенностях русской иконописи и ее  основных сюжетах на примере коллекции СОХМ. Посетители смогут познакомиться с традиционными техниками религиозного декоративно – прикладного искусства.',
                    event_type='excursion',
                    start_datetime=now.replace(hour=18, minute=0) + timedelta(days=2),
                    price='200 руб.',
                    max_participants=50,
                    location='Главный холл',
                    organizer='Лекторий музея',
                    contact_phone='+7 (905) 37 238-65',
                    poster_image='https://artmus.ru/content/upload/images/001%20(19).jpg',
                    is_active=True
                ),
                Event(
                    name='Русское искусство рубежа XIX – XX веков ',
                    description='Рубеж эпох выделяется в особый период, когда начинают формироваться новые принципы в искусстве. Это время в нашей коллекции представлено такими именами как: Б.М. Кустодиев, Н.К. Рерих, К.Ф. Богаевский, М.В. Нестеров, В.А. Серов, К.А. Коровин, А.Е. Архипов и др.',
                    event_type='excursion',
                    start_datetime=now.replace(hour=11, minute=0) + timedelta(days=5),
                    price='300 руб.',
                    max_participants=20,
                    location='Главный холл',
                    organizer='Отдел экскурсий',
                    contact_phone='+7 (905) 37 238-65',
                    poster_image='https://artmus.ru/content/upload/images/AJGYEaRX6eU(1).jpg',
                    is_active=True
                )
            ]
            session.add_all(events)

            logger.info("Начальные данные успешно загружены")

    def get_stats(self):
        with self.session_scope() as session:
            stats = {
                'users': session.query(User).count(),
                'exhibitions': session.query(Exhibition).count(),
                'events': session.query(Event).count(),
                'bookings': session.query(Booking).count(),
                'active_events': session.query(Event).filter(
                    Event.start_datetime >= datetime.now(),
                    Event.is_active == True
                ).count()
            }
            return stats