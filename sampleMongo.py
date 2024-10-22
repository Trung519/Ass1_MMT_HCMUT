import pymongo
import datetime

# connect to your Atlas cluster
uri = "mongodb+srv://trungphamquang519:jYlt9UNRTIjRuAPS@mmt.zy5ep.mongodb.net/?retryWrites=true&w=majority&appName=MMT"

# Create a new client and connect to the server
client = pymongo.MongoClient(uri)
# get the database and collection on which to run the operation
collection = client['gettingStarted']['people']

# create new documents
peopleDocuments = [
    {
      "name": { "first": "Alan", "last": "Turing" },
      "birth": datetime.datetime(1912, 6, 23),
      "death": datetime.datetime(1954, 6, 7),
      "contribs": [ "Turing machine", "Turing test", "Turingery" ],
      "views": 1250000
    }, 
    {
      "name": { "first": "Grace", "last": "Hopper" },
      "birth": datetime.datetime(1906, 12, 9),
      "death": datetime.datetime(1992, 1, 1),
      "contribs": [ "Mark I", "UNIVAC", "COBOL" ],
      "views": 3860000
    }
]

# insert documents
collection.insert_many(peopleDocuments)

# find documents 
result = collection.find_one({ "name.last": "Turing" })

# print results
print("Document found:\n", result)
