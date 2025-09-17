"""
Base repository class with common CRUD operations.
"""
from typing import Type, TypeVar, Generic, Optional, List, Any, Dict
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database import Base
from app.core.logging import database_logger

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Base repository with common CRUD operations."""
    
    def __init__(self, model: Type[ModelType]):
        """
        Initialize repository with model.
        
        Args:
            model: SQLAlchemy model class
        """
        self.model = model
    
    def create(self, db: Session, *, obj_in: Dict[str, Any]) -> ModelType:
        """
        Create a new record.
        
        Args:
            db: Database session
            obj_in: Dictionary of attributes for the new record
        
        Returns:
            Created model instance
        
        Raises:
            IntegrityError: If there's a database constraint violation
        """
        try:
            db_obj = self.model(**obj_in)
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            
            database_logger.log_transaction(
                operation="CREATE",
                table=self.model.__tablename__,
                record_id=getattr(db_obj, 'id', None)
            )
            
            return db_obj
        except IntegrityError as e:
            db.rollback()
            raise e
    
    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        """
        Get record by ID.
        
        Args:
            db: Database session
            id: Record ID
        
        Returns:
            Model instance or None if not found
        """
        return db.query(self.model).filter(self.model.id == id).first()
    
    def get_multi(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """
        Get multiple records with pagination.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
        
        Returns:
            List of model instances
        """
        return db.query(self.model).offset(skip).limit(limit).all()
    
    def update(self, db: Session, *, db_obj: ModelType, obj_in: Dict[str, Any]) -> ModelType:
        """
        Update an existing record.
        
        Args:
            db: Database session
            db_obj: Existing model instance
            obj_in: Dictionary of attributes to update
        
        Returns:
            Updated model instance
        """
        try:
            for field, value in obj_in.items():
                if hasattr(db_obj, field) and value is not None:
                    setattr(db_obj, field, value)
            
            db.commit()
            db.refresh(db_obj)
            
            database_logger.log_transaction(
                operation="UPDATE",
                table=self.model.__tablename__,
                record_id=getattr(db_obj, 'id', None)
            )
            
            return db_obj
        except IntegrityError as e:
            db.rollback()
            raise e
    
    def delete(self, db: Session, *, id: Any) -> Optional[ModelType]:
        """
        Delete a record by ID.
        
        Args:
            db: Database session
            id: Record ID
        
        Returns:
            Deleted model instance or None if not found
        """
        obj = db.query(self.model).get(id)
        if obj:
            db.delete(obj)
            db.commit()
            
            database_logger.log_transaction(
                operation="DELETE",
                table=self.model.__tablename__,
                record_id=id
            )
        
        return obj
    
    def exists(self, db: Session, id: Any) -> bool:
        """
        Check if a record exists.
        
        Args:
            db: Database session
            id: Record ID
        
        Returns:
            True if record exists, False otherwise
        """
        return db.query(self.model).filter(self.model.id == id).first() is not None
    
    def count(self, db: Session, **filters) -> int:
        """
        Count records with optional filters.
        
        Args:
            db: Database session
            **filters: Filter conditions
        
        Returns:
            Number of matching records
        """
        query = db.query(self.model)
        
        for field, value in filters.items():
            if hasattr(self.model, field) and value is not None:
                query = query.filter(getattr(self.model, field) == value)
        
        return query.count()
    
    def find_by(self, db: Session, **filters) -> List[ModelType]:
        """
        Find records by filters.
        
        Args:
            db: Database session
            **filters: Filter conditions
        
        Returns:
            List of matching model instances
        """
        query = db.query(self.model)
        
        for field, value in filters.items():
            if hasattr(self.model, field) and value is not None:
                query = query.filter(getattr(self.model, field) == value)
        
        return query.all()
    
    def find_one_by(self, db: Session, **filters) -> Optional[ModelType]:
        """
        Find one record by filters.
        
        Args:
            db: Database session
            **filters: Filter conditions
        
        Returns:
            First matching model instance or None
        """
        query = db.query(self.model)
        
        for field, value in filters.items():
            if hasattr(self.model, field) and value is not None:
                query = query.filter(getattr(self.model, field) == value)
        
        return query.first()
    
    def bulk_create(self, db: Session, *, objs_in: List[Dict[str, Any]]) -> List[ModelType]:
        """
        Create multiple records in bulk.
        
        Args:
            db: Database session
            objs_in: List of dictionaries with attributes for new records
        
        Returns:
            List of created model instances
        """
        try:
            db_objs = [self.model(**obj_in) for obj_in in objs_in]
            db.add_all(db_objs)
            db.commit()
            
            for db_obj in db_objs:
                db.refresh(db_obj)
            
            database_logger.log_transaction(
                operation="BULK_CREATE",
                table=self.model.__tablename__,
                record_id=f"{len(db_objs)} records"
            )
            
            return db_objs
        except IntegrityError as e:
            db.rollback()
            raise e
    
    def bulk_update(self, db: Session, *, updates: List[Dict[str, Any]]) -> int:
        """
        Update multiple records in bulk.
        
        Args:
            db: Database session
            updates: List of dictionaries with 'id' and update attributes
        
        Returns:
            Number of updated records
        """
        try:
            updated_count = 0
            
            for update_data in updates:
                record_id = update_data.pop('id')
                if record_id:
                    result = db.query(self.model).filter(
                        self.model.id == record_id
                    ).update(update_data)
                    updated_count += result
            
            db.commit()
            
            database_logger.log_transaction(
                operation="BULK_UPDATE",
                table=self.model.__tablename__,
                record_id=f"{updated_count} records"
            )
            
            return updated_count
        except IntegrityError as e:
            db.rollback()
            raise e
    
    def bulk_delete(self, db: Session, *, ids: List[Any]) -> int:
        """
        Delete multiple records in bulk.
        
        Args:
            db: Database session
            ids: List of record IDs to delete
        
        Returns:
            Number of deleted records
        """
        deleted_count = db.query(self.model).filter(
            self.model.id.in_(ids)
        ).delete(synchronize_session=False)
        
        db.commit()
        
        database_logger.log_transaction(
            operation="BULK_DELETE",
            table=self.model.__tablename__,
            record_id=f"{deleted_count} records"
        )
        
        return deleted_count
