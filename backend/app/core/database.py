import enum
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def str_enum_values(enum_cls: type[enum.Enum]) -> list[str]:
    """SQLAlchemy Enum(..., values_callable=str_enum_values) 용 헬퍼.

    values_callable 없으면 SQLAlchemy가 멤버 .name(대문자)을 DB로 보내는데, 소문자 값을
    사용하는 Postgres enum 타입에 저장 시 DataError가 난다. 새 str Enum 컬럼을 추가할 때는
    이 헬퍼를 재사용해서 같은 문제를 다시 만들지 않도록 한다.
    """
    return [member.value for member in enum_cls]


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
