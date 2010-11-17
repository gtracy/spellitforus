#!/usr/bin/env python

import os
import logging

from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.db import Key
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp import util

from google.appengine.api import users
from google.appengine.api import mail
from google.appengine.api import memcache
from google.appengine.api.labs import taskqueue
from google.appengine.api.labs.taskqueue import Task

from google.appengine.runtime import apiproxy_errors

from dataModel import *


class UserHandler(webapp.RequestHandler):
    
    def get(self):
      activeUser = users.get_current_user()
      if activeUser:
          greeting = ("%s (<a href=\"%s\">sign out</a>)" %
                      (activeUser.nickname(), users.create_logout_url("/")))
      else:
          self.redirect("/")
          return

      # identify the user profile being displayed
      userKey = self.request.get("user")
      if len(userKey) == 0:
          logging.debug("seeking profile page without a key...")
          userQuery = db.GqlQuery("SELECT __key__ FROM User WHERE userID = :1", activeUser.user_id())
          userKey = userQuery.get()
          if userKey is None:
              logging.info("this is a brand new user... ask them to init their profile")
              createUser(activeUser)
              userKey = userQuery.get()
              self.redirect('/user/edit?user='+str(userKey)+'&init=yes')
              return
              
      logging.info("user key is %s" % userKey)
      user = db.get(userKey)
      if user is None:
          logging.info("Can't find this user!?! userKey sent from the client is %s" % userKey)
          # this should never be the case so bail back to the front page if it does
          self.redirect("/")
          return

      if user.userID == activeUser.user_id():
          edit = '<div id="edit"><a href=/user/edit?user='+str(userKey)+'>edit</a></div>'
      else:
          edit = ' '

      # add the counter to the template values
      template_values = {'nickname':user.nickname,
                         'userEmail':user.email,
                         'userIDKey':str(user.key()),
                         'greeting':greeting,
                         'edit':edit,
                        }
      
      # generate the html
      path = os.path.join(os.path.dirname(__file__), 'user.html')
      self.response.out.write(template.render(path, template_values))


##  end UserHandler

class UserEditHandler(webapp.RequestHandler):
    
    def get(self):
        activeUser = users.get_current_user()
        if activeUser:
            greeting = ("%s (<a href=\"%s\">sign out</a>)" %
                        (activeUser.nickname(), users.create_logout_url("/")))
        else:
            self.redirect("/")
            return
        
        # grab the user's current profile data to populate the form
        user = db.get(self.request.get("user"))
        if user is None:
            logging.error("User edit attempt with no logged in user. This should never happen, %s" % self.request.get("user"))
            return
        
        if self.request.get('init') == 'yes':
            welcome = "<h3>Welcome! Please take a moment to fill out your profile.</h3>"
        else:
            welcome = ' '
            
        logging.info("User: %s", user.nickname)
        first = ' ' if user.first is None else user.first
        last = ' ' if user.last is None else user.last
        nickname = first + ' ' + last if user.nickname is None else user.nickname
        email = user.email
              
        template_values = {'nickname':nickname,
                           'preferredEmail':email,
                           'greeting':greeting,
                           'first':first,
                           'last':last,
                           'userKey':self.request.get('user'),
                           'welcome':welcome,
                          }
        path = os.path.join(os.path.dirname(__file__), 'profile.html')
        self.response.out.write(template.render(path, template_values))
        
## end UserEditHandler

class ProfileAjaxUpdateHandler(webapp.RequestHandler):

    def post(self):
        activeUser = users.get_current_user()
        if activeUser:
            greeting = ("%s (<a href=\"%s\">sign out</a>)" %
                        (activeUser.nickname(), users.create_logout_url("/")))
        else:
            self.redirect("/")
            return

        first = self.request.get('first')
        last = self.request.get('last')
        nickname = self.request.get('nickname')
        phone = self.request.get('phone')
        userKey = self.request.get('userKey')
        
        user = db.get(userKey)
        if user is None:
            logging.error("Profile update attempt with no logged in user. This should never happen, %s" % userKey)
            return
        
        #logging.info("Updating profile for %s with %s, %s, %s, %s" % (userKey,first,last,nickname,email))
        user.first = first
        user.last = last
        user.nickname = nickname
        user.phoneNumber = phone
        user.put()
        
        self.redirect('/')

## end ProfileAjaxUpdateHandler

def createUser(activeUser):
        newUser = User()
        newUser.user = activeUser
        newUser.userID = activeUser.user_id()
        newUser.email = activeUser.email()
        newUser.nickname = activeUser.nickname()
        newUser.status = ""
        logging.info("Creating profile for %s" % newUser.email)
        newUser.put()
        return

## end createUser()          


def getUser(userID):
    
    user = memcache.get(userID)
    if user is None:
      userQuery = db.GqlQuery("SELECT * FROM User WHERE userID = :1", userID)
      users = userQuery.fetch(1)
      if len(users) == 0:
          logging.info("We can't find this user in the User table... userID: %s" % userID)
          return None
      else:
          memcache.set(userID, user)
          return users[0]
    else:
      return user
    
## end getUser()

def main():
  logging.getLogger().setLevel(logging.DEBUG)
  application = webapp.WSGIApplication([('/user', UserHandler),
                                        ('/user/edit', UserEditHandler),
                                        ('/user/update', ProfileAjaxUpdateHandler),
                                        ],
                                       debug=True)
  util.run_wsgi_app(application)


if __name__ == '__main__':
  main()
