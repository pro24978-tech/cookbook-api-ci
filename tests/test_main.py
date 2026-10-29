from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DATABASE_URL)
TestSessionLocal = async_sessionmaker(
    test_engine, expire_on_commit=False, class_=AsyncSession
)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session


# Подменяем реальную БД на тестовую
app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(autouse=True)
async def setup_db() -> AsyncGenerator[None, None]:
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    # Убираем предупреждения об открытых соединениях
    await test_engine.dispose()


@pytest.mark.asyncio
async def test_create_and_get_recipes() -> None:
    # Добавляем # type: ignore, так как mypy строго конфликтует с httpx+FastAPI
    transport = ASGITransport(app=app)  # type: ignore
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Создаем рецепт
        response = await ac.post(
            "/recipes/",
            json={
                "title": "Омлет",
                "cooking_time": 10,
                "ingredients": ["Яйца", "Молоко"],
                "description": "Взбить и пожарить.",
            },
        )
        assert response.status_code == 201
        recipe_id = response.json()["id"]
        assert response.json()["views"] == 0

        # 2. Читаем список
        response = await ac.get("/recipes/")
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["title"] == "Омлет"

        # 3. Читаем детали (просмотры +1)
        response = await ac.get(f"/recipes/{recipe_id}")
        assert response.status_code == 200
        assert response.json()["views"] == 1

        # 4. Проверяем сортировку в списке
        response = await ac.get("/recipes/")
        assert response.json()[0]["views"] == 1
