from sqlalchemy import create_engine, Column, Integer, String, Text, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import os

Base = declarative_base()


class MuseumInfo(Base):
    __tablename__ = 'museum_info'

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    address = Column(String(300), nullable=False)
    work_hours = Column(String(200), nullable=False)
    phone = Column(String(50), nullable=False)
    website = Column(String(100))
    price_info = Column(Text)
    description = Column(Text)
    latitude = Column(Float)
    longitude = Column(Float)
    main_image = Column(String(500))  #
    gallery_images = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Exhibition(Base):
    """Выставки"""
    __tablename__ = 'exhibitions'

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    type = Column(String(50))
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    curator = Column(String(100))
    is_active = Column(Boolean, default=True)
    poster_image = Column(String(500))  # Постер выставки
    gallery_images = Column(Text)  # Дополнительные изображения
    created_at = Column(DateTime, default=datetime.utcnow)

    # Связь с залами
    halls = relationship("Hall", back_populates="exhibition", cascade="all, delete-orphan")


class Hall(Base):
    """Залы музея"""
    __tablename__ = 'halls'

    id = Column(Integer, primary_key=True)
    exhibition_id = Column(Integer, ForeignKey('exhibitions.id'))
    name = Column(String(200), nullable=False)
    description = Column(Text)
    floor = Column(Integer)
    hall_image = Column(String(500))  # Изображение зала
    created_at = Column(DateTime, default=datetime.utcnow)

    # Связи
    exhibition = relationship("Exhibition", back_populates="halls")
    exhibits = relationship("Exhibit", back_populates="hall", cascade="all, delete-orphan")


class Exhibit(Base):
    """Экспонаты"""
    __tablename__ = 'exhibits'

    id = Column(Integer, primary_key=True)
    hall_id = Column(Integer, ForeignKey('halls.id'))
    name = Column(String(300), nullable=False)
    description = Column(Text)
    author = Column(String(200))
    year = Column(String(50))
    material = Column(String(200))
    image_url = Column(String(500))
    audio_guide_url = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)

    hall = relationship("Hall", back_populates="exhibits")


class Event(Base):
    """Мероприятия"""
    __tablename__ = 'events'

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    event_type = Column(String(50))
    start_datetime = Column(DateTime)
    end_datetime = Column(DateTime, nullable=True)
    recurrence = Column(String(50))
    price = Column(String(100))
    max_participants = Column(Integer)
    current_participants = Column(Integer, default=0)
    location = Column(String(200))
    organizer = Column(String(100))
    contact_phone = Column(String(50))
    is_active = Column(Boolean, default=True)
    poster_image = Column(String(500))
    gallery_images = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, nullable=True)


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))
    is_admin = Column(Boolean, default=False)
    language = Column(String(10), default='ru')
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)

class Booking(Base):
    __tablename__ = 'bookings'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    event_id = Column(Integer, ForeignKey('events.id'))
    booking_date = Column(DateTime, default=datetime.utcnow)
    event_date = Column(DateTime)
    tickets_count = Column(Integer, default=1)
    status = Column(String(50), default='pending')
    total_price = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)