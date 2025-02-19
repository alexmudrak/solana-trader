from sqlalchemy import Column, Float, Integer, Sequence, String

from models import Base


class Price(Base):
    __tablename__ = "prices"

    id = Column(Integer, Sequence("price_id_seq"), primary_key=True)
    token_name = Column(String(50), nullable=False)
    price = Column(Float)
    timestamp = Column(String(50))
