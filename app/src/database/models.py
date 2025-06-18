# app/src/databases/models.py
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Date
from sqlalchemy.orm import relationship
from app.src.database.database import Base
class User(Base): 
    __tablename__ = "users"   
    id = Column(Integer, primary_key=True, index=True)  
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    confirmed = Column(Boolean, default=False)
    avatar = Column(String, nullable=True)  
    contacts = relationship("Contact", back_populates="owner")      
class Contact(Base):          
    __tablename__ = "contacts"   
    id = Column(Integer, primary_key=True, index=True) 
    first_name = Column(String, index=True)     
    last_name = Column(String, index=True)  
    email = Column(String, index=True) 
    phone_number = Column(String)       
    birthday = Column(Date)  
    additional_info = Column(String) 
    user_id = Column(Integer, ForeignKey("users.id"))  
    owner = relationship("User", back_populates="contacts")

