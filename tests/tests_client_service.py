import pytest
import pytest_asyncio
from sqlalchemy import create_engine
from app.models.user import User
from app.models.client import Client
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool
from fastapi import HTTPException
import sys
from unittest.mock import MagicMock
from app.schemas.clients import ClientCreate, ClientRead
from app.schemas.common import PaginationResponse, PaginationInfo
import asyncio
from app.services.clients import create_client, get_clients

Base = declarative_base()

app_models = MagicMock()
app_models.Client = Client
app_models.Base = Base

app_schemas = MagicMock()
app_schemas.ClientCreate = ClientCreate

app_schemas_clients = MagicMock()
app_schemas_clients.ClientRead = ClientRead

app_schemas_common = MagicMock()
app_schemas_common.PaginationResponse = PaginationResponse
app_schemas_common.PaginationInfo = PaginationInfo

sys.modules['app.models'] = app_models
sys.modules['app.schemas'] = app_schemas
sys.modules['app.schemas.clients'] = app_schemas_clients
sys.modules['app.schemas.common'] = app_schemas_common

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def async_engine():
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False}
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture
async def sample_user(db_session):
    user = User(
        id=1,
        email="testuser@example.com",
        name="Test User",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def client_create_data():
    return ClientCreate(
        name="Juan Pérez",
        email="juan@example.com",
        phone="+1234567890",
        address="123 Main St, Anytown, USA"
    )


@pytest.fixture
def another_client_create_data():
    return ClientCreate(
        name="Maria López",
        email="maria@example.com",
        phone="987654321",
        address="456 Elm St, Othertown, USA"
    )


class TestCreateClient:

    @pytest.mark.asyncio
    async def test_create_client_success(self, db_session, client_create_data, sample_user):
        result = await create_client(db_session, client_create_data, sample_user.user.id)

        assert result is not None
        assert result.id is not None
        assert result.name == client_create_data.name
        assert result.email == client_create_data.email
        assert result.phone == client_create_data.phone
        assert result.address == client_create_data.address
        assert result.user_id == sample_user.user.id

        assert result.id > 0

    @pytest.mark.asyncio
    async def test_create_client_duplicate_email(self, db_session, client_create_data, sample_uuser):
        await create_client(db_session, client_create_data, sample_user.user.id)

        duplicate_client = ClientCreate(
            name="Otro Cliente",
            email=client_create_data.email,
            phone="123456789",
            address="789 Oak St, Sometown, USA"
        )

        with pytest.raises(HTTPException) as exc_info:
            await create_client(db_session, duplicate_client, sample_user.user.id)
        assert exc_info.value.status_code == 400
        assert "Client with this email already exists" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_create_multiiple_clients_differeent_emails(
        self,
        db_session,
        client_create_data,
        another_client_create_data,
        sample_user
    ):
        client1 = await create_client(db_session, client_create_data, sample_user.user.id)
        client2 = await create_client(db_session, another_client_create_data, sample_user.user.id)

        assert client1.id is not client2.id
        assert client1.email != client2.email
        assert client1.user_id == client2.user_id == sample_user.user.id

    @pytest.mark.asyncio
    async def test_create_client_with_minimal_data(self, db_session, sample_user):
        minimal_client = ClientCreate(
            name="Minimal Client",
            email="minimal@example.com"
        )

        result = await create_client(db_session, minimal_client, sample_user.user.id)

        assert result is not None
        assert result.name == minimal_client.name
        assert result.email == minimal_client.email
        assert result.phone is None
        assert result.address is None

    @pytest.mark.asyncio
    async def test_create_client_different_users_same_email(self, db_session):
        user1 = User(id=1, email="user1@example.com", name="User 1")
        user2 = User(id=2, email="user2@example.com", name="User 2")

        db_session.add(user1)
        db_session.add(user2)
        await db_session.commit()

        client_data = ClientCreate(
            name="Test Client",
            email="shared@example.com",
            phone="123456789"
        )

        await create_client(db_session, client_data, user1.id)

        with pytest.raises(HTTPException) as exc_info:
            await create_client(db_session, client_data, user2.id)

        assert exc_info.value.status_code == 400


class TestGetClients:
    @pytest_asyncio.fixture
    async def setup_test_clients(self, db_session, sample_user):
        clients_data = [
            ClientCreate(
                name="Cliente Alpha",
                email="alpha@example.com",
                phone="111111111",
                address="Dirección Alpha"
            ),
            ClientCreate(
                name="Cliente Beta",
                email="beta@example.com",
                phone="222222222",
                address="Dirección Beta"
            ),
            ClientCreate(
                name="Cliente Gamma",
                email="gamma@example.com",
                phone="333333333",
                address="Dirección Gamma"
            ),
            ClientCreate(
                name="Test Search",
                email="search@test.com",
                phone="444444444",
                address="Dirección Search"
            ),
            ClientCreate(
                name="Another Test",
                email="another@test.com",
                phone="555555555",
                address="Dirección Another"
            ),
        ]

        created_clients = []
        for client_data in clients_data:
            client = await create_client(db_session, client_data, sample_user.id)
            created_clients.append(client)

        return created_clients

    @pytest.mark.asyncio
    async def test_get_clients_default_pagination(self, db_session, setup_test_clients):
        result = await get_clients(db_session)

        assert isinstance(result, PaginationResponse)
        assert result.info.page == 1
        assert result.info.per_page == 20
        assert result.info.total == 5
        assert result.info.total_pages == 1
        assert len(result.data) == 5

        for client in result.data:
            assert isinstance(client, ClientRead)
            assert client.id is not None
            assert client.name is not None
            assert client.email is not None

    @pytest.mark.asyncio
    async def test_get_clients_with_pagination(self, db_session, setup_test_clients):
        result = await get_clients(db_session, skip=2, limit=2)

        assert result.info.page == 2
        assert result.info.per_page == 2
        assert result.info.total == 5
        assert result.info.total_pages == 3
        assert len(result.data) == 2

    @pytest.mark.asyncio
    async def test_get_clients_with_search(self, db_session, setup_test_clients):
        result = await get_clients(db_session, search="test")

        assert result.info.total == 2
        assert len(result.data) == 2

        for client in result.data:
            assert "test" in client.email.lower()

    @pytest.mark.asyncio
    async def test_get_clients_search_case_insensitive(self, db_session, setup_test_clients):
        result_lower = await get_clients(db_session, search="alpha")
        result_upper = await get_clients(db_session, search="ALPHA")
        result_mixed = await get_clients(db_session, search="Alpha")

        assert result_lower.info.total == 1
        assert result_upper.info.total == 1
        assert result_mixed.info.total == 1

    @pytest.mark.asyncio
    async def test_get_clients_no_results(self, db_session, setup_test_clients):
        result = await get_clients(db_session, search="nonexistent")

        assert result.info.total == 0
        assert result.info.total_pages == 1
        assert len(result.data) == 0

    @pytest.mark.asyncio
    async def test_get_clients_empty_database(self, db_session):
        result = await get_clients(db_session)

        assert result.info.total == 0
        assert result.info.total_pages == 1
        assert len(result.data) == 0

    @pytest.mark.asyncio
    async def test_get_clients_pagination_boundary_conditions(self, db_session, setup_test_clients):
        result = await get_clients(db_session, skip=0, limit=3)
        assert result.info.page == 1
        assert len(result.data) == 3

        result = await get_clients(db_session, skip=3, limit=3)
        assert result.info.page == 2
        assert len(result.data) == 2

        result = await get_clients(db_session, skip=10, limit=3)
        assert len(result.data) == 0
        assert result.info.total == 5

    @pytest.mark.asyncio
    async def test_get_clients_search_partial_match(self, db_session, setup_test_clients):
        result = await get_clients(db_session, search="@example")

        assert result.info.total == 3
        assert len(result.data) == 3

        for client in result.data:
            assert "@example.com" in client.email


class TestIntegrationScenarios:
    @pytest.mark.asyncio
    async def test_complete_client_management_workflow(self, db_session, sample_user):
        empty_result = await get_clients(db_session)
        assert empty_result.info.total == 0

        clients_to_create = [
            ClientCreate(name="Cliente A", email="a@test.com", phone="111"),
            ClientCreate(name="Cliente B", email="b@test.com", phone="222"),
            ClientCreate(name="Cliente C", email="c@test.com", phone="333"),
        ]

        created_clients = []
        for client_data in clients_to_create:
            client = await create_client(db_session, client_data, sample_user.id)
            created_clients.append(client)

        all_clients = await get_clients(db_session)
        assert all_clients.info.total == 3

        search_result = await get_clients(db_session, search="a@test")
        assert search_result.info.total == 1
        assert search_result.data[0].name == "Cliente A"

        paginated_result = await get_clients(db_session, skip=1, limit=1)
        assert paginated_result.info.page == 2
        assert len(paginated_result.data) == 1

    @pytest.mark.asyncio
    async def test_duplicate_email_prevention(self, db_session, sample_user):
        client1_data = ClientCreate(
            name="First Client",
            email="unique@test.com",
            phone="111"
        )

        client1 = await create_client(db_session, client1_data, sample_user.id)
        assert client1.id is not None

        client2_data = ClientCreate(
            name="Second Client",
            email="unique@test.com",
            phone="222"
        )

        with pytest.raises(HTTPException) as exc_info:
            await create_client(db_session, client2_data, sample_user.id)

        assert exc_info.value.status_code == 400

        all_clients = await get_clients(db_session)
        assert all_clients.info.total == 1

    @pytest.mark.asyncio
    async def test_large_dataset_pagination(self, db_session, sample_user):
        for i in range(25):
            client_data = ClientCreate(
                name=f"Cliente {i:02d}",
                email=f"client{i:02d}@test.com",
                phone=f"{i:03d}000000"
            )
            await create_client(db_session, client_data, sample_user.id)

        page1 = await get_clients(db_session, skip=0, limit=10)
        assert len(page1.data) == 10
        assert page1.info.total_pages == 3

        page2 = await get_clients(db_session, skip=10, limit=10)
        assert len(page2.data) == 10
        assert page2.info.page == 2

        page3 = await get_clients(db_session, skip=20, limit=10)
        assert len(page3.data) == 5
        assert page3.info.page == 3


class TestErrorHandling:
    @pytest.mark.asyncio
    async def test_create_client_invalid_user_id(self, db_session):
        client_data = ClientCreate(
            name="Test Client",
            email="test@example.com"
        )
        result = await create_client(db_session, client_data, 999)
        assert result.user_id == 999

    @pytest.mark.asyncio
    async def test_get_clients_extreme_pagination_values(self, db_session, sample_user):
        client_data = ClientCreate(name="Test", email="test@example.com")
        await create_client(db_session, client_data, sample_user.id)

        result = await get_clients(db_session, skip=1000000, limit=10)
        assert len(result.data) == 0
        assert result.info.total == 1

        result = await get_clients(db_session, skip=0, limit=0)
        assert result.info.per_page == 0
        assert result.info.total_pages == 1
