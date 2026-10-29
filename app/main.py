from collections.abc import Sequence
from contextlib import asynccontextmanager
from typing import AsyncIterator, List

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import RedirectResponse

# ДОБАВЛЯЕМ ИМПОРТ update
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas
from app.database import engine, get_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="Cookbook API",
    description="API для кулинарной книги",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    return RedirectResponse(url="/docs")


@app.post(
    "/recipes/",
    response_model=schemas.RecipeDetailOut,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новый рецепт",
    tags=["Рецепты"],
)
async def create_recipe(
    recipe: schemas.RecipeCreate, db: AsyncSession = Depends(get_db)
) -> models.Recipe:

    new_recipe = models.Recipe(**recipe.model_dump())
    db.add(new_recipe)
    await db.commit()
    await db.refresh(new_recipe)
    return new_recipe


@app.get(
    "/recipes/",
    response_model=List[schemas.RecipeListOut],
    summary="Получить список всех рецептов (Первый экран)",
    tags=["Рецепты"],
)
async def get_recipes(
    db: AsyncSession = Depends(get_db),
) -> Sequence[models.Recipe]:

    query = select(models.Recipe).order_by(
        models.Recipe.views.desc(), models.Recipe.cooking_time.asc()
    )

    result = await db.execute(query)
    return result.scalars().all()


# ОБНОВЛЕННЫЙ ЭНДПОИНТ
@app.get(
    "/recipes/{recipe_id}",
    response_model=schemas.RecipeDetailOut,
    summary="Получить детальную информацию о рецепте (Второй экран)",
    tags=["Рецепты"],
)
async def get_recipe(
    recipe_id: int, db: AsyncSession = Depends(get_db)
) -> models.Recipe:

    # 1. Сначала проверяем, существует ли рецепт (чтобы вернуть 404, если нет)
    recipe = await db.get(models.Recipe, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Рецепт не найден")

    # 2. Атомарно увеличиваем счетчик просмотров в базе данных
    stmt = (
        update(models.Recipe)
        .where(models.Recipe.id == recipe_id)
        .values(views=models.Recipe.views + 1)
    )
    await db.execute(stmt)
    await db.commit()

    # 3. Так как мы обновили данные в БД в обход ORM-объекта,
    # объект в памяти (recipe) устарел. Нам нужно его обновить,
    # чтобы вернуть клиенту актуальное значение views.
    await db.refresh(recipe)

    return recipe
