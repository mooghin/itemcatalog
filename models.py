import random
import string
import datetime

from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

from itsdangerous import (TimedJSONWebSignatureSerializer as
                          Serializer, BadSignature, SignatureExpired)

Base = declarative_base()
secret_key = ''.join(random.choice(string.ascii_uppercase + string.digits)
                     for x in range(32))


class User(Base):
    ''' Represents a user of the item catalog. '''
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False)
    email = Column(String, nullable=False)
    picture = Column(String)

    def generate_auth_token(self, expiration=600):
        s = Serializer(secret_key, expires_in=expiration)
        return s.dumps({'id': self.id})

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(secret_key)
        try:
            data = s.loads(token)
        except SignatureExpired:
            # Valid Token, but expired
            return None
        except BadSignature:
            # Invalid Token
            return None
        user_id = data['id']
        return user_id


class Category(Base):
    ''' Represents a category of items that can be accessed in the catalog. '''
    __tablename__ = 'category'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

    @property
    def serialize(self):
        """Return Category data in easily serializeable format"""
        return {
            'type': 'Category',
            'name': self.name,
            'id': self.id,
        }


class Item(Base):
    ''' Represents one item that can be accessed in the catalog.
        Must belong to one category. '''
    __tablename__ = 'item'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, default="no description available")
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(Category)
    date_added = Column(DateTime, default=datetime.datetime.now)

    @property
    def serialize(self):
        """Return Item data in easily serializeable format"""
        return {
            'type': 'Item',
            'name': self.name,
            'id': self.id,
            'description': self.description,
            'category': self.category.name,
            'date_added': self.date_added,
        }

# Set up database
engine = create_engine('sqlite:///itemcatalog.db')
Base.metadata.create_all(engine)
