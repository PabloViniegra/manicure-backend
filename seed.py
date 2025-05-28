import asyncio
from datetime import datetime, timedelta
from sqlalchemy import delete
from app.database import async_sessionmaker
from app.models.user import User
from app.models.client import Client
from app.models.service import Service
from app.models.appointment import Appointment

import bcrypt


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


async def seed():
    session = async_sessionmaker()
    async with session as db:
        await db.execute(delete(Appointment))
        await db.execute(delete(Service))
        await db.execute(delete(Client))
        await db.execute(delete(User))
        await db.commit()

        password = hash_password("admin123")
        admin = User(email="admin@example.com", full_name="Admin User",
                     hashed_password=password, is_active=True, role="admin")
        user1 = User(email="user1@example.com", full_name="User One",
                     hashed_password=hash_password("user1pass"), is_active=True, role="client")
        user2 = User(email="user2@example.com", full_name="User Two",
                     hashed_password=hash_password("user2pass"), is_active=True, role="staff")
        db.add_all([admin, user1, user2])
        await db.commit()
        await db.refresh(admin)
        await db.refresh(user1)
        await db.refresh(user2)

        client1 = Client(
            name="María Gómez",
            email="maria@example.com",
            phone="123456789",
            address="Calle Primavera 123",
            user_id=user1.id
        )
        client2 = Client(
            name="Lucía Pérez",
            email="lucia@example.com",
            phone="987654321",
            address="Avenida Verano 99",
            user_id=user2.id
        )
        db.add_all([client1, client2])
        await db.commit()
        await db.refresh(client1)
        await db.refresh(client2)

        service1 = Service(name="Manicura tradicional", duration=45,
                           price=20.0, description="Manicura básica con esmalte tradicional")
        service2 = Service(name="Manicura semipermanente", duration=60,
                           price=30.0, description="Esmalte semipermanente de larga duración")
        service3 = Service(name="Decoración de uñas", duration=30,
                           price=10.0, description="Decoración artística personalizada")
        db.add_all([service1, service2, service3])
        await db.commit()
        await db.refresh(service1)
        await db.refresh(service2)
        await db.refresh(service3)

        appointment1 = Appointment(
            client_id=client1.id,
            date=datetime.utcnow() + timedelta(days=1, hours=10),
            status="pending",
            created_at=datetime.utcnow(),
            notes="Prefiere colores neutros.",
            services=[service1, service3],
        )
        appointment2 = Appointment(
            client_id=client2.id,
            date=datetime.utcnow() + timedelta(days=2, hours=11),
            status="confirmed",
            created_at=datetime.utcnow(),
            notes="Traer catálogo de diseños.",
            services=[service2],
        )
        db.add_all([appointment1, appointment2])
        await db.commit()

        print("✅ Seed completado con datos de ejemplo.")

if __name__ == "__main__":
    asyncio.run(seed())
