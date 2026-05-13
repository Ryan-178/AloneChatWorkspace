import asyncio
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app
from auth import get_password_hash, create_access_token
from models import User, Conversation, ConversationParticipant, Group, GroupMember, Message, Workspace, WorkspaceMember, AgentSession, AgentMessage

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(scope="session")
async def db_engine():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session(db_engine):
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.fixture
def override_get_db(db_session):
    async def _get_db():
        yield db_session
    return _get_db


@pytest.fixture
def client(override_get_db):
    from httpx import AsyncClient, ASGITransport
    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest_asyncio.fixture
async def test_user(db_session):
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("password123"),
        display_name="Test User",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_user2(db_session):
    user = User(
        email="test2@example.com",
        hashed_password=get_password_hash("password123"),
        display_name="Test User 2",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user):
    token = create_access_token(data={"sub": test_user.id})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers2(test_user2):
    token = create_access_token(data={"sub": test_user2.id})
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def test_conversation(db_session, test_user, test_user2):
    conv = Conversation(type="direct", name="Test Conversation")
    db_session.add(conv)
    await db_session.flush()

    cp1 = ConversationParticipant(conversation_id=conv.id, user_id=test_user.id)
    cp2 = ConversationParticipant(conversation_id=conv.id, user_id=test_user2.id)
    db_session.add_all([cp1, cp2])
    await db_session.commit()
    await db_session.refresh(conv)
    return conv


@pytest_asyncio.fixture
async def test_group(db_session, test_user, test_user2):
    group = Group(name="Test Group", description="A test group", owner_id=test_user.id)
    db_session.add(group)
    await db_session.flush()

    gm1 = GroupMember(group_id=group.id, user_id=test_user.id, role="owner")
    gm2 = GroupMember(group_id=group.id, user_id=test_user2.id, role="member")
    db_session.add_all([gm1, gm2])
    await db_session.commit()
    await db_session.refresh(group)
    return group


@pytest_asyncio.fixture
async def test_workspace(db_session, test_user):
    ws = Workspace(name="Test Workspace", description="A test workspace", owner_id=test_user.id)
    db_session.add(ws)
    await db_session.flush()

    member = WorkspaceMember(workspace_id=ws.id, user_id=test_user.id, role="owner")
    db_session.add(member)
    await db_session.commit()
    await db_session.refresh(ws)
    return ws


@pytest_asyncio.fixture
async def test_agent_session(db_session, test_user):
    session = AgentSession(
        user_id=test_user.id,
        title="Test Agent Session",
        status="active",
    )
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)
    return session
