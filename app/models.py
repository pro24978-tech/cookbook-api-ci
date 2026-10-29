from sqlalchemy import JSON, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Recipe(Base):
    __tablename__ = "recipes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(100), index=True)
    views: Mapped[int] = mapped_column(Integer, default=0)
    cooking_time: Mapped[int] = mapped_column(Integer)  # в минутах
    ingredients: Mapped[list[str]] = mapped_column(JSON)  # список строк
    description: Mapped[str] = mapped_column(Text)
