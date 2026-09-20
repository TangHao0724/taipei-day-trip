from datetime import date
from pydantic import BaseModel
from enum import Enum
class Time_slot(str, Enum):
	MORNING = "morning"
	AFTERNOON = "afternoon"

class User_data(BaseModel):
	id:int | None = None
	name:str | None = None
	email:str	
	password:str

class Signin_data(BaseModel):
	email:str
	password:str

class Booking_data(BaseModel):
	attractionId:int
	date:date
	time: Time_slot
	price:int

class Attraction(BaseModel):
	id:int
	name:str
	address:str
	image:str

class Order(BaseModel):
	price:int
	trip:Trip

class Trip(BaseModel):
    attraction: Attraction
    date: date
    time: str

class Contact(BaseModel):
	name:str
	email:str
	phone:str
class Full_order(BaseModel):
	prime:str
	order:Order
	contact:Contact


# mcp_data
class Mcp_data(BaseModel):
	id:int
	token:str | None