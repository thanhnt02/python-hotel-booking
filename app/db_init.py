"""
Database initialization and management utilities.
"""
import asyncio
from typing import Optional
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import structlog

from app.core.config import get_settings
from app.models.base import Base
from app.models.user import User, UserRole
from app.models.hotel import Hotel, HotelStatus
from app.models.room import Room, RoomType, RoomStatus
from app.core.security import get_password_hash

logger = structlog.get_logger(__name__)
settings = get_settings()


def create_database():
    """Create the database if it doesn't exist."""
    # Parse database URL to get database name
    db_url_parts = settings.DATABASE_URL.split('/')
    database_name = db_url_parts[-1]
    base_url = '/'.join(db_url_parts[:-1])
    
    # Create engine without database name to create the database
    engine = create_engine(
        base_url + '/postgres',  # Connect to default postgres database
        isolation_level='AUTOCOMMIT'
    )
    
    try:
        with engine.connect() as conn:
            # Check if database exists
            result = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :db_name"),
                {"db_name": database_name}
            )
            
            if not result.fetchone():
                # Create database
                conn.execute(text(f"CREATE DATABASE {database_name}"))
                logger.info(f"Database '{database_name}' created successfully")
            else:
                logger.info(f"Database '{database_name}' already exists")
                
    except Exception as e:
        logger.error(f"Error creating database: {e}")
        raise
    finally:
        engine.dispose()


def create_tables():
    """Create all database tables."""
    engine = create_engine(settings.DATABASE_URL)
    
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        raise
    finally:
        engine.dispose()


def drop_tables():
    """Drop all database tables."""
    engine = create_engine(settings.DATABASE_URL)
    
    try:
        # Drop all tables
        Base.metadata.drop_all(bind=engine)
        logger.info("Database tables dropped successfully")
    except Exception as e:
        logger.error(f"Error dropping tables: {e}")
        raise
    finally:
        engine.dispose()


def init_db():
    """Initialize the database with tables and initial data."""
    logger.info("Initializing database...")
    
    # Create database if it doesn't exist
    create_database()
    
    # Create all tables
    create_tables()
    
    # Create initial data
    create_initial_data()
    
    logger.info("Database initialization completed")


def create_initial_data():
    """Create initial data for the application."""
    from app.database import SessionLocal
    
    db = SessionLocal()
    
    try:
        # Check if admin user exists
        admin_user = db.query(User).filter(User.email == "admin@hotel.com").first()
        
        if not admin_user:
            # Create admin user
            admin_user = User(
                email="admin@hotel.com",
                first_name="Admin",
                last_name="User",
                hashed_password=get_password_hash("admin123"),
                role=UserRole.ADMIN,
                is_active=True,
                is_verified=True
            )
            db.add(admin_user)
            logger.info("Admin user created")
        
        # Check if demo hotel manager exists
        manager_user = db.query(User).filter(User.email == "manager@hotel.com").first()
        
        if not manager_user:
            # Create hotel manager user
            manager_user = User(
                email="manager@hotel.com",
                first_name="Hotel",
                last_name="Manager",
                hashed_password=get_password_hash("manager123"),
                role=UserRole.HOTEL_MANAGER,
                is_active=True,
                is_verified=True
            )
            db.add(manager_user)
            logger.info("Hotel manager user created")
        
        # Check if demo customer exists
        customer_user = db.query(User).filter(User.email == "customer@example.com").first()
        
        if not customer_user:
            # Create customer user
            customer_user = User(
                email="customer@example.com",
                first_name="John",
                last_name="Doe",
                hashed_password=get_password_hash("customer123"),
                role=UserRole.CUSTOMER,
                is_active=True,
                is_verified=True
            )
            db.add(customer_user)
            logger.info("Demo customer user created")
        
        db.commit()
        
        # Create demo hotel if manager exists
        if manager_user:
            demo_hotel = db.query(Hotel).filter(Hotel.name == "Grand Hotel Demo").first()
            
            if not demo_hotel:
                # Create demo hotel
                demo_hotel = Hotel(
                    name="Grand Hotel Demo",
                    description="A luxurious demo hotel for testing",
                    address="123 Hotel Street, Demo City, DC 12345",
                    city="Demo City",
                    country="Demo Country",
                    phone="+1-555-0123",
                    email="info@grandhoteldemo.com",
                    website="https://grandhoteldemo.com",
                    star_rating=5,
                    status=HotelStatus.ACTIVE,
                    manager_id=manager_user.id
                )
                db.add(demo_hotel)
                db.commit()
                logger.info("Demo hotel created")
                
                # Create demo rooms
                room_types = [
                    (RoomType.STANDARD, 99.99, "Comfortable standard room"),
                    (RoomType.DELUXE, 149.99, "Spacious deluxe room with city view"),
                    (RoomType.SUITE, 299.99, "Luxury suite with premium amenities"),
                    (RoomType.PRESIDENTIAL, 599.99, "Presidential suite with exclusive services")
                ]
                
                for room_type, price, description in room_types:
                    for room_num in range(1, 6):  # Create 5 rooms of each type
                        room_number = f"{room_type.value.upper()}-{room_num:03d}"
                        
                        room = Room(
                            room_number=room_number,
                            room_type=room_type,
                            description=description,
                            price_per_night=price,
                            max_occupancy=2 if room_type == RoomType.STANDARD else 4,
                            status=RoomStatus.AVAILABLE,
                            hotel_id=demo_hotel.id
                        )
                        db.add(room)
                
                db.commit()
                logger.info("Demo rooms created")
        
        logger.info("Initial data creation completed")
        
    except Exception as e:
        logger.error(f"Error creating initial data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def reset_database():
    """Reset the database by dropping and recreating all tables."""
    logger.warning("Resetting database - all data will be lost!")
    
    # Drop all tables
    drop_tables()
    
    # Initialize fresh database
    init_db()
    
    logger.info("Database reset completed")


async def check_database_connection():
    """Check if database connection is working."""
    from app.database import async_engine
    
    try:
        async with async_engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            await result.fetchone()
        
        logger.info("Database connection successful")
        return True
        
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


def migrate_database():
    """Run database migrations (placeholder for Alembic)."""
    logger.info("Running database migrations...")
    
    # This would typically use Alembic commands
    # For now, we'll just ensure tables exist
    create_tables()
    
    logger.info("Database migrations completed")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Database management commands")
    parser.add_argument(
        "command",
        choices=["init", "create-tables", "drop-tables", "reset", "migrate", "create-initial-data"],
        help="Database command to run"
    )
    
    args = parser.parse_args()
    
    if args.command == "init":
        init_db()
    elif args.command == "create-tables":
        create_tables()
    elif args.command == "drop-tables":
        drop_tables()
    elif args.command == "reset":
        reset_database()
    elif args.command == "migrate":
        migrate_database()
    elif args.command == "create-initial-data":
        create_initial_data()
