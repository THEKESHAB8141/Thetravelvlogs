from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Define Models
class Destination(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    region: str
    description: str
    image_url: str
    highlights: List[str]
    best_season: str

class DestinationCreate(BaseModel):
    name: str
    region: str
    description: str
    image_url: str
    highlights: List[str]
    best_season: str

class TripPackage(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    destination_id: str
    destination_name: str
    title: str
    duration: str
    price_veg: float
    price_non_veg: float
    pickup_time: str
    itinerary: List[str]
    inclusions: List[str]
    exclusions: List[str]
    image_url: str

class TripPackageCreate(BaseModel):
    destination_id: str
    destination_name: str
    title: str
    duration: str
    price_veg: float
    price_non_veg: float
    pickup_time: str
    itinerary: List[str]
    inclusions: List[str]
    exclusions: List[str]
    image_url: str

class Booking(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    trip_id: str
    trip_title: str
    customer_name: str
    customer_email: str
    customer_phone: str
    travel_date: str
    guests: int
    meal_preference: str
    total_amount: float
    booking_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "confirmed"

class BookingCreate(BaseModel):
    trip_id: str
    trip_title: str
    customer_name: str
    customer_email: str
    customer_phone: str
    travel_date: str
    guests: int
    meal_preference: str
    total_amount: float

# Routes
@api_router.get("/")
async def root():
    return {"message": "Northeast India & Sikkim Travel API"}

# Destinations
@api_router.get("/destinations", response_model=List[Destination])
async def get_destinations():
    destinations = await db.destinations.find({}, {"_id": 0}).to_list(1000)
    return destinations

@api_router.post("/destinations", response_model=Destination)
async def create_destination(input: DestinationCreate):
    dest_dict = input.model_dump()
    dest_obj = Destination(**dest_dict)
    doc = dest_obj.model_dump()
    await db.destinations.insert_one(doc)
    return dest_obj

# Trip Packages
@api_router.get("/trips", response_model=List[TripPackage])
async def get_trips(destination_id: Optional[str] = None):
    query = {"destination_id": destination_id} if destination_id else {}
    trips = await db.trips.find(query, {"_id": 0}).to_list(1000)
    return trips

@api_router.get("/trips/{trip_id}", response_model=TripPackage)
async def get_trip(trip_id: str):
    trip = await db.trips.find_one({"id": trip_id}, {"_id": 0})
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip

@api_router.post("/trips", response_model=TripPackage)
async def create_trip(input: TripPackageCreate):
    trip_dict = input.model_dump()
    trip_obj = TripPackage(**trip_dict)
    doc = trip_obj.model_dump()
    await db.trips.insert_one(doc)
    return trip_obj

# Bookings
@api_router.get("/bookings", response_model=List[Booking])
async def get_bookings():
    bookings = await db.bookings.find({}, {"_id": 0}).to_list(1000)
    for booking in bookings:
        if isinstance(booking.get('booking_date'), str):
            booking['booking_date'] = datetime.fromisoformat(booking['booking_date'])
    return bookings

@api_router.post("/bookings", response_model=Booking)
async def create_booking(input: BookingCreate):
    booking_dict = input.model_dump()
    booking_obj = Booking(**booking_dict)
    doc = booking_obj.model_dump()
    doc['booking_date'] = doc['booking_date'].isoformat()
    await db.bookings.insert_one(doc)
    return booking_obj

# Seed data endpoint
@api_router.post("/seed")
async def seed_data():
    # Clear existing data
    await db.destinations.delete_many({})
    await db.trips.delete_many({})
    
    # Seed destinations
    destinations_data = [
        {
            "id": "dest-1",
            "name": "Gangtok",
            "region": "Sikkim",
            "description": "The capital of Sikkim, nestled in the Himalayas with stunning mountain views and rich Buddhist culture.",
            "image_url": "https://images.unsplash.com/photo-1761820228515-b79043c31856?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDQ2NDN8MHwxfHNlYXJjaHwxfHxIaW1hbGF5YW4lMjBtb3VudGFpbiUyMHZpc3RhfGVufDB8fHx8MTc2MjEwNDgwNXww&ixlib=rb-4.1.0&q=85",
            "highlights": ["Tsomgo Lake", "Nathula Pass", "Rumtek Monastery", "MG Marg"],
            "best_season": "March to June, September to December"
        },
        {
            "id": "dest-2",
            "name": "Darjeeling",
            "region": "West Bengal",
            "description": "Famous for its tea gardens, toy train, and breathtaking views of Kanchenjunga.",
            "image_url": "https://images.unsplash.com/photo-1742286087572-937f08b947b8?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDQ2Mzl8MHwxfHNlYXJjaHwxfHx0ZWElMjBnYXJkZW4lMjBsYW5kc2NhcGV8ZW58MHx8fHwxNzYyMTA0ODA1fDA&ixlib=rb-4.1.0&q=85",
            "highlights": ["Tiger Hill", "Darjeeling Himalayan Railway", "Tea Gardens", "Batasia Loop"],
            "best_season": "April to June, September to November"
        },
        {
            "id": "dest-3",
            "name": "Tawang",
            "region": "Arunachal Pradesh",
            "description": "Home to India's largest monastery and spectacular mountain landscapes.",
            "image_url": "https://images.unsplash.com/photo-1633538028057-838fd4e027a4?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NjZ8MHwxfHNlYXJjaHwxfHxCdWRkaGlzdCUyMG1vbmFzdGVyeXxlbnwwfHx8fDE3NjIxMDQ4MDZ8MA&ixlib=rb-4.1.0&q=85",
            "highlights": ["Tawang Monastery", "Sela Pass", "Madhuri Lake", "Bumla Pass"],
            "best_season": "March to October"
        },
        {
            "id": "dest-4",
            "name": "Shillong",
            "region": "Meghalaya",
            "description": "The 'Scotland of the East' with rolling hills, waterfalls, and pleasant weather.",
            "image_url": "https://images.unsplash.com/photo-1752063497357-4a9e0b765771?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDQ2NDN8MHwxfHNlYXJjaHwyfHxIaW1hbGF5YW4lMjBtb3VudGFpbiUyMHZpc3RhfGVufDB8fHx8MTc2MjEwNDgwNXww&ixlib=rb-4.1.0&q=85",
            "highlights": ["Elephant Falls", "Shillong Peak", "Ward's Lake", "Don Bosco Museum"],
            "best_season": "October to May"
        }
    ]
    
    await db.destinations.insert_many(destinations_data)
    
    # Seed trip packages
    trips_data = [
        {
            "id": "trip-1",
            "destination_id": "dest-1",
            "destination_name": "Gangtok",
            "title": "Gangtok Paradise - 5 Days",
            "duration": "5 Days / 4 Nights",
            "price_veg": 18500,
            "price_non_veg": 21000,
            "pickup_time": "8:00 AM from Bagdogra Airport/NJP Station",
            "itinerary": [
                "Day 1: Arrival in Gangtok, check-in, MG Marg evening walk",
                "Day 2: Tsomgo Lake & Baba Mandir excursion",
                "Day 3: Nathula Pass visit (subject to permit)",
                "Day 4: Rumtek Monastery, Hanuman Tok, Tashi View Point",
                "Day 5: Departure to Bagdogra/NJP"
            ],
            "inclusions": ["Accommodation", "Daily breakfast, lunch & dinner", "All transfers", "Sightseeing as per itinerary", "Permit fees"],
            "exclusions": ["Personal expenses", "Travel insurance", "Any meals not mentioned"],
            "image_url": "https://images.unsplash.com/photo-1761820228515-b79043c31856?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDQ2NDN8MHwxfHNlYXJjaHwxfHxIaW1hbGF5YW4lMjBtb3VudGFpbiUyMHZpc3RhfGVufDB8fHx8MTc2MjEwNDgwNXww&ixlib=rb-4.1.0&q=85"
        },
        {
            "id": "trip-2",
            "destination_id": "dest-2",
            "destination_name": "Darjeeling",
            "title": "Darjeeling Delight - 4 Days",
            "duration": "4 Days / 3 Nights",
            "price_veg": 14500,
            "price_non_veg": 16500,
            "pickup_time": "7:00 AM from Bagdogra Airport/NJP Station",
            "itinerary": [
                "Day 1: Arrival in Darjeeling, check-in, Mall Road exploration",
                "Day 2: Tiger Hill sunrise, Ghoom Monastery, Batasia Loop, toy train ride",
                "Day 3: Tea garden visit, Happy Valley, Himalayan Mountaineering Institute",
                "Day 4: Departure to Bagdogra/NJP"
            ],
            "inclusions": ["Accommodation", "Daily breakfast, lunch & dinner", "All transfers", "Sightseeing", "Toy train tickets"],
            "exclusions": ["Personal expenses", "Camera fees", "Tips"],
            "image_url": "https://images.unsplash.com/photo-1742286087572-937f08b947b8?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDQ2Mzl8MHwxfHNlYXJjaHwxfHx0ZWElMjBnYXJkZW4lMjBsYW5kc2NhcGV8ZW58MHx8fHwxNzYyMTA0ODA1fDA&ixlib=rb-4.1.0&q=85"
        },
        {
            "id": "trip-3",
            "destination_id": "dest-3",
            "destination_name": "Tawang",
            "title": "Tawang Tranquility - 6 Days",
            "duration": "6 Days / 5 Nights",
            "price_veg": 25500,
            "price_non_veg": 28500,
            "pickup_time": "6:00 AM from Guwahati Airport/Station",
            "itinerary": [
                "Day 1: Guwahati to Bomdila (overnight journey)",
                "Day 2: Bomdila to Tawang via Sela Pass",
                "Day 3: Tawang Monastery, War Memorial, local market",
                "Day 4: Bumla Pass & Madhuri Lake excursion",
                "Day 5: Tawang to Bomdila",
                "Day 6: Bomdila to Guwahati, departure"
            ],
            "inclusions": ["Accommodation", "All meals", "Permits & entry fees", "Transfers", "Guide services"],
            "exclusions": ["Personal expenses", "Travel insurance", "Medical expenses", "Laundry"],
            "image_url": "https://images.unsplash.com/photo-1633538028057-838fd4e027a4?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NjZ8MHwxfHNlYXJjaHwxfHxCdWRkaGlzdCUyMG1vbmFzdGVyeXxlbnwwfHx8fDE3NjIxMDQ4MDZ8MA&ixlib=rb-4.1.0&q=85"
        },
        {
            "id": "trip-4",
            "destination_id": "dest-4",
            "destination_name": "Shillong",
            "title": "Shillong Explorer - 4 Days",
            "duration": "4 Days / 3 Nights",
            "price_veg": 15400,
            "price_non_veg": 17400,
            "pickup_time": "9:00 AM from Guwahati Airport/Station",
            "itinerary": [
                "Day 1: Guwahati to Shillong, Umiam Lake visit",
                "Day 2: Cherrapunji day trip - Nohkalikai Falls, Seven Sisters Falls, Mawsmai Cave",
                "Day 3: Elephant Falls, Shillong Peak, Ward's Lake, Police Bazaar",
                "Day 4: Departure to Guwahati"
            ],
            "inclusions": ["Accommodation", "Breakfast, lunch & dinner", "Transfers", "Sightseeing", "Entry tickets"],
            "exclusions": ["Personal expenses", "Camera fees", "Adventure activities"],
            "image_url": "https://images.unsplash.com/photo-1752063497357-4a9e0b765771?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDQ2NDN8MHwxfHNlYXJjaHwyfHxIaW1hbGF5YW4lMjBtb3VudGFpbiUyMHZpc3RhfGVufDB8fHx8MTc2MjEwNDgwNXww&ixlib=rb-4.1.0&q=85"
        }
    ]
    
    await db.trips.insert_many(trips_data)
    
    return {"message": "Database seeded successfully", "destinations": len(destinations_data), "trips": len(trips_data)}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()