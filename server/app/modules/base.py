from typing import Generic, TypeVar, Type, Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import Base

ModelT =  TypeVar("ModelT" , bound= Base)
CreateSchemaT = TypeVar("CreateSchemaT" ,  bound =  BaseModel)
UpdateSchemaT = TypeVar("updateSchemaT" ,  bound =  BaseModel)
class CRUDBase(Generic[ModelT ,  CreateSchemaT ,  UpdateSchemaT]):
    def __init__(self , model : Type[ModelT]):
        self.model =  model 

    async def get( self , db : AsyncSession , id :  str ) -> ModelT | None :
        return await db.get(self.model , id)

    async def get_multi(self ,  db : AsyncSession , skip : int = 0 , limit : int = 100) -> Sequence[ModelT] :
        result = await db.execute(select(self.model).offset(skip).limit(limit))
        return result.scalars().all()

    async def create(self, db: AsyncSession, *, obj_in: CreateSchemaT) -> ModelT:
        db_obj = self.model(**obj_in.model_dump())
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self, db: AsyncSession, *, db_obj: ModelT, obj_in: UpdateSchemaT
    ) -> ModelT:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def remove(self, db: AsyncSession, *, id: int) -> ModelT | None:
        obj = await self.get(db, id)
        if obj:
            await db.delete(obj)
            await db.commit()
        return obj