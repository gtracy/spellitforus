from google.appengine.ext import db

   
class User(db.Model):
    user              = db.UserProperty()
    phoneNumber       = db.StringProperty()
    userID            = db.StringProperty()
    email             = db.StringProperty()
    nickname          = db.StringProperty()
    status            = db.StringProperty()
    first             = db.StringProperty()
    last              = db.StringProperty()
    createDate        = db.DateTimeProperty(auto_now_add=True)
    
class Test(db.Model):
    name           = db.StringProperty()
    words          = db.StringListProperty()
    wordRecordings = db.StringListProperty()
    wordAnswers    = db.StringListProperty()
    grade          = db.StringProperty()
    dateAdded      = db.DateTimeProperty(auto_now_add=True)
    testsTaken     = db.IntegerProperty()
    randHandle     = db.StringProperty()
    
class UserTest(db.Model):
    test   = db.ReferenceProperty(Test)
    user   = db.ReferenceProperty(User)
    score  = db.IntegerProperty()
    date   = db.DateTimeProperty(auto_now_add=True)
    