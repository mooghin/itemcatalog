from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Base, User, Category, Item

engine = create_engine('sqlite:///itemcatalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# Create initial user
User1 = User(username="Megan Elmore", email="mooghin@gmail.com")
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
tent = Item(owner=User1, name="tent", category=Camping)
sleeping_bag = Item(owner=User1, name="sleeping bag", category=Camping)
sleeping_pad = Item(owner=User1, name="sleeping pad", category=Camping)
plate = Item(owner=User1, name="plate", category=Camping)
mug = Item(owner=User1, name="mug", category=Camping)
spork = Item(owner=User1, name="spork", category=Camping)
headlamp = Item(owner=User1, name="headlamp", category=Camping)

session.add(tent)
session.add(sleeping_bag)
session.add(sleeping_pad)
session.add(plate)
session.add(mug)
session.add(spork)
session.add(headlamp)
session.commit()

# Second category: Hiking
boots = Item(owner=User1, name="hiking boots", category=Hiking)
socks = Item(owner=User1, name="wool socks", category=Hiking)
pack = Item(owner=User1, name="daypack", category=Hiking)
hat = Item(owner=User1, name="sun hat", category=Hiking)

session.add(boots)
session.add(socks)
session.add(pack)
session.add(hat)
session.commit()

# Third category: Spinning
top = Item(owner=User1, name="workout top", category=Spinning)
tights = Item(owner=User1, name="spin tights", category=Spinning)
socks = Item(owner=User1, name="cotton socks", category=Spinning)
shoes = Item(owner=User1, name="spinning shoes", category=Spinning)

session.add(top)
session.add(tights)
session.add(socks)
session.add(shoes)
session.commit()

# Fourth category: Health
bottle = Item(owner=User1, name="water bottle", category=Health)
uv = Item(owner=User1, name="sunscreen", category=Health)
chapstick = Item(owner=User1, name="Chap-Stick", category=Health)
bandaids = Item(owner=User1, name="Band-Aids", category=Health)

session.add(bottle)
session.add(uv)
session.add(chapstick)
session.add(bandaids)
session.commit()
