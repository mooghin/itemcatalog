from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Base, User, Category, Item

engine = create_engine('sqlite:///itemcatalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# Create dummy user
User1 = User(username="Megan", email="mooghin@gmail.com")
session.add(User1)
session.commit()

# Create new categories for items
Camping = Category(name="Camping")
session.add(Camping)
session.commit()

Hiking = Category(name="Hiking")
session.add(Hiking)
session.commit()

Spinning = Category(name="Spinning")
session.add(Spinning)
session.commit()

Health = Category(name="Health+Safety")
session.add(Health)
session.commit()

# Create items in each category
# First category: Camping
tent = Item(name="tent", category=Camping)
sleeping_bag = Item(name="sleeping bag", category=Camping)
sleeping_pad = Item(name="sleeping pad", category=Camping)
plate = Item(name="plate", category=Camping)
mug = Item(name="mug", category=Camping)
spork = Item(name="spork", category=Camping)
headlamp = Item(name="headlamp", category=Camping)

session.add(tent)
session.add(sleeping_bag)
session.add(sleeping_pad)
session.add(plate)
session.add(mug)
session.add(spork)
session.add(headlamp)
session.commit()

# Second category: Hiking
boots = Item(name="hiking boots", category=Hiking)
socks = Item(name="wool socks", category=Hiking)
pack = Item(name="daypack", category=Hiking)
hat = Item(name="sun hat", category=Hiking)

session.add(boots)
session.add(socks)
session.add(pack)
session.add(hat)
session.commit()

# Third category: Spinning
top = Item(name="workout top", category=Spinning)
tights = Item(name="spin tights", category=Spinning)
socks = Item(name="cotton socks", category=Spinning)
shoes = Item(name="spinning shoes", category=Spinning)

session.add(top)
session.add(tights)
session.add(socks)
session.add(shoes)
session.commit()

# Fourth category: Health
bottle = Item(name="water bottle", category=Health)
uv = Item(name="sunscreen", category=Health)
chapstick = Item(name="Chap-Stick", category=Health)
bandaids = Item(name="Band-Aids", category=Health)

session.add(bottle)
session.add(uv)
session.add(chapstick)
session.add(bandaids)
session.commit()
