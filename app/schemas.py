from typing import List

from pydantic import BaseModel, Field


class RecipeBase(BaseModel):
    title: str = Field(
        ...,
        description="Название блюда",
        json_schema_extra={"example": "Паста Карбонара"},
    )
    cooking_time: int = Field(
        ...,
        description="Время приготовления в минутах",
        gt=0,
        json_schema_extra={"example": 30},
    )
    ingredients: List[str] = Field(
        ...,
        description="Список ингредиентов",
        json_schema_extra={"example": ["Спагетти", "Бекон", "Яйца"]},
    )
    description: str = Field(
        ...,
        description="Текстовое описание процесса приготовления",
        json_schema_extra={"example": "Сварите пасту..."},
    )


class RecipeCreate(RecipeBase):
    pass


class RecipeListOut(BaseModel):
    id: int
    title: str
    views: int
    cooking_time: int

    model_config = {"from_attributes": True}


class RecipeDetailOut(RecipeBase):
    id: int
    views: int

    model_config = {"from_attributes": True}
