from sqlalchemy import Column, Integer, String, Date
from app.src.databases.base import Base
class Contact(Base): 
    __tablename__ = 'contacts' 

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(55), nullable=False)  
    last_name = Column(String(55), nullable=False)
    email = Column(String(100), unique=True, nullable=False) 
    phone_number = Column(String(20), nullable=False) 
    birthday = Column(Date, nullable=False)   
    additional_info = Column(String(250), nullable=True)
