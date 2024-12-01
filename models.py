from typing import Callable

from sqlalchemy import create_engine, Integer, Text, Select, BigInteger, Delete
from sqlalchemy.dialects.postgresql import Insert
from sqlalchemy.orm import DeclarativeBase, declared_attr
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import roles

engine = create_engine("postgresql+psycopg2://postgres:secret@db:5432/niyat", echo=True, pool_pre_ping=True)


class AbstractClass:
    @classmethod
    async def select(cls, **kwargs):
        with engine.connect() as conn:
            res = conn.execute(Select(cls))
            conn.commit()
            return res

    @classmethod
    async def filter(cls, *criteria):
        with engine.connect() as conn:
            res = conn.execute(Select(cls).filter(*criteria))
            conn.commit()
            return res

    @classmethod
    async def create(cls, **kwargs):
        with engine.connect() as conn:
            conn.execute(Insert(cls).values(**kwargs))
            conn.commit()

    @classmethod
    async def delete(cls, id):
        with engine.connect() as conn:
            conn.execute(Delete(cls).where(cls.id==id))
            conn.commit()


class Base(DeclarativeBase, AbstractClass):
    @declared_attr
    def __tablename__(self):
        result = self.__name__[0].lower()
        for i in self.__name__[1:]:
            if i.isupper():
                result += f'_{i.lower()}'
                continue
            result += i
        return result


class Answer(Base):
    id: Mapped[str] = mapped_column(Integer, primary_key=True)
    modul: Mapped[str] = mapped_column(Text)
    lesson: Mapped[str] = mapped_column(Text)
    question: Mapped[str] = mapped_column(Text)
    question_number: Mapped[int] = mapped_column(Integer)
    answer: Mapped[str] = mapped_column(Text)


class Question(Base):
    id: Mapped[str] = mapped_column(Integer, primary_key=True)
    question: Mapped[int] = mapped_column(Text, unique=True)
    user_id: Mapped[str] = mapped_column(BigInteger)


def create_table():
    Base.metadata.create_all(engine)
