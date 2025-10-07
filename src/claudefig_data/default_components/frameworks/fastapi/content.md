## FastAPI Best Practices

### Project Structure

```
project/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app initialization
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py          # Shared dependencies
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── endpoints/
│   │       │   ├── users.py
│   │       │   └── items.py
│   │       └── router.py    # API router
│   ├── core/
│   │   ├── config.py        # Settings management
│   │   └── security.py      # Auth utilities
│   ├── models/              # Database models
│   ├── schemas/             # Pydantic models
│   └── services/            # Business logic
├── tests/
└── pyproject.toml
```

### API Design

**Endpoint Naming:**
- Use plural nouns: `/users`, `/items`
- RESTful conventions: GET, POST, PUT/PATCH, DELETE
- Versioning in path: `/api/v1/users`

**Example Router:**
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.schemas.user import User, UserCreate
from app.services.user import user_service

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=User, status_code=201)
{% if use_async %}async {% endif %}def create_user(
    user_in: UserCreate,
    db: Session = Depends(deps.get_db),
) -> User:
    """Create a new user."""
    existing = {% if use_async %}await {% endif %}user_service.get_by_email(db, user_in.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    return {% if use_async %}await {% endif %}user_service.create(db, user_in)
```

### Pydantic Models

{% if use_pydantic_v2 %}
**Using Pydantic V2:**

```python
from pydantic import BaseModel, EmailStr, Field, ConfigDict

class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=100)
    is_active: bool = True

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class User(UserBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
```

**Key Changes from V1:**
- Use `model_config` instead of `class Config`
- Use `ConfigDict(from_attributes=True)` instead of `orm_mode=True`
- Use `model_dump()` instead of `dict()`
- Use `model_validate()` instead of `parse_obj()`
{% else %}
**Using Pydantic V1:**

```python
from pydantic import BaseModel, EmailStr, Field

class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=100)
    is_active: bool = True

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class User(UserBase):
    id: int

    class Config:
        orm_mode = True
```
{% endif %}

### Dependency Injection

**Common Dependencies:**

```python
# app/api/deps.py
from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import decode_token
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_db() -> Generator:
    """Database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

{% if use_async %}async {% endif %}def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> User:
    """Get currently authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    user = {% if use_async %}await {% endif %}user_service.get(db, id=payload["sub"])
    if user is None:
        raise credentials_exception
    return user
```

{% if use_async %}
### Async/Await Patterns

**Database Operations:**
```python
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

async_engine = create_async_engine("postgresql+asyncpg://...")
AsyncSessionLocal = sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
```

**Async Endpoints:**
```python
@router.get("/users/{user_id}")
async def read_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
) -> User:
    user = await user_service.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
```
{% endif %}

{% if use_sqlalchemy %}
### Database Integration (SQLAlchemy)

**Models:**
```python
from sqlalchemy import Boolean, Column, Integer, String
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
```

**Service Layer:**
```python
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate

class UserService:
    {% if use_async %}async {% endif %}def get(self, db: Session, id: int) -> User | None:
        return {% if use_async %}await {% endif %}db.query(User).filter(User.id == id).first()

    {% if use_async %}async {% endif %}def create(self, db: Session, user_in: UserCreate) -> User:
        user = User(
            email=user_in.email,
            hashed_password=hash_password(user_in.password),
            full_name=user_in.full_name,
        )
        db.add(user)
        {% if use_async %}await {% endif %}db.commit()
        {% if use_async %}await {% endif %}db.refresh(user)
        return user

user_service = UserService()
```
{% endif %}

### Error Handling

**Custom Exceptions:**
```python
from fastapi import HTTPException, status

class UserNotFoundError(HTTPException):
    def __init__(self, user_id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )

class ValidationError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail
        )
```

### Configuration Management

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "My API"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    {% if use_pydantic_v2 %}
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True
    )
    {% else %}
    class Config:
        env_file = ".env"
        case_sensitive = True
    {% endif %}

settings = Settings()
```

### Testing

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_user():
    response = client.post(
        "/api/v1/users/",
        json={
            "email": "test@example.com",
            "full_name": "Test User",
            "password": "securepassword"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data
```

### Best Practices Checklist

- [ ] Use dependency injection for database sessions and auth
- [ ] Separate Pydantic schemas from SQLAlchemy models
- [ ] Implement service layer for business logic
- [ ] Use proper HTTP status codes
- [ ] Document all endpoints with docstrings
- [ ] Add request/response examples to OpenAPI docs
- [ ] Implement proper error handling with custom exceptions
- [ ] Use async/await for I/O-bound operations
- [ ] Add input validation with Pydantic
- [ ] Include API versioning in routes
- [ ] Set up CORS properly for frontend integration
- [ ] Use environment variables for configuration
