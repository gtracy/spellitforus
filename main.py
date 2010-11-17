#!/usr/bin/env python

import os
import logging
import random
import string

from django.utils import simplejson

from google.appengine.api import users
from google.appengine.api import images
from google.appengine.ext import db
from google.appengine.ext.db import Key
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp import util

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

from dataModel import *

import userhandlers
import twilio

GOOGLE_ANALYTICS_CODE = 'UA-configure-me'


class MainHandler(webapp.RequestHandler):
    def get(self):
      user = users.get_current_user()
      if user:
          greeting = ("%s (<a href=\"%s\">sign out</a>)" %
                      (user.nickname(), users.create_logout_url("/")))

      else:
          greeting = ("<a href=\"%s\">Sign in or register</a>" %
                        users.create_login_url("/"))
          # add the counter to the template values
          template_values = {'greeting':greeting,
                             'addButton':'<span> </span>',
                             'specialNote':('<span style="padding-top:25px;font-size:18px;color:#dd0000;">You need to be <a href=\"%s\">logged in</a> to access tests.</span>' % users.create_login_url("/")),
                            }
      
          # generate the html
          path = os.path.join(os.path.dirname(__file__), 'index.html')
          self.response.out.write(template.render(path, template_values))
          return
      
      # make sure we already have this user registered so we
      # can keep track of the ID
      userID = user.user_id()
      user = db.GqlQuery("SELECT * FROM User WHERE userID = :1", userID).get()
      if user is None:
          # re-direct to account creation page
          self.redirect("/user")
          return
      else:
          if user.phoneNumber is None:
              phoneNumber = 'x'
          else:
              phoneNumber = user.phoneNumber

      # use a random string to connect words for a test that hasn't been created
      randomString = ''.join(random.choice(string.letters) for i in xrange(8))
      # get a list of ALL existing tests
      results = []
      testQuery = db.GqlQuery("SELECT * FROM Test ORDER BY dateAdded DESC")
      tests = testQuery.fetch(100)
      for s in tests:
        logging.debug('found a test!')			
        results.append({'grade':s.grade,
                        'name':s.name,
                        'words':s.words,
                        'testid':s.key(),
                        'counter':s.testsTaken,                        
                        })      
      
      # add the counter to the template values
      template_values = {'greeting':greeting,
                         'phoneNumber':phoneNumber,
                         'randomString':randomString,
                         'addButton':'<span class="add-btn">+ create a test</span>',
                         'tests':results,
                         'googleAnalyticsCode':GOOGLE_ANALYTICS_CODE,
                        }
      
      # generate the html
      path = os.path.join(os.path.dirname(__file__), 'index.html')
      self.response.out.write(template.render(path, template_values))

# handler for ajax call to add a new test via the web
class AddTestHandler(webapp.RequestHandler):
    
    def post(self):
      activeUser = userhandlers.getUser(users.get_current_user().user_id())
      if not activeUser:
          self.error(404)
          return
      
      # check to see if the test already exists. we may have created it
      # if the user recorded their own words
      code = self.request.get('code')
      test = db.GqlQuery("SELECT * FROM Test WHERE randHandle = :1",code).get()
      if test is None:
          logging.debug("hmm. we had to create a new test model for %s" % code)
          test = Test()
      else:
          logging.debug('adding words to existing test %s' % code)
          
      test.owner = activeUser
      if self.request.get('name'):
          test.name = self.request.get('name');
      else:
          test.name = 'no name';
          
      if self.request.get('grade'):
          test.grade = self.request.get('grade')
      else:
          test.grade = 'unknown'
          
      words = []
      wordAnswers = []
      if self.request.get('one'): 
          words.append(self.request.get('one'))
          wordAnswers.append(computeKeypadAnswer(self.request.get('one')))
      if self.request.get('two'): 
          words.append(self.request.get('two'))
          wordAnswers.append(computeKeypadAnswer(self.request.get('two')))
      if self.request.get('three'): 
          words.append(self.request.get('three'))
          wordAnswers.append(computeKeypadAnswer(self.request.get('three')))
      if self.request.get('four'): 
          words.append(self.request.get('four'))
          wordAnswers.append(computeKeypadAnswer(self.request.get('four')))
      if self.request.get('five'): 
          words.append(self.request.get('five'))
          wordAnswers.append(computeKeypadAnswer(self.request.get('five')))

      if not words or len(words) == 0:
          self.error(403)
          return
      
      test.words = words
      test.wordAnswers = wordAnswers
      test.testsTaken = 0
      test.put()
      
      # encapsulate in json
      response_dict = {}
      if activeUser.first:
          owner = activeUser.first + ' ' + activeUser.last
      else:
          owner = activeUser.nickname
      response_dict.update({'name':test.name,
                            'grade':test.grade,
                            'words':test.words,
                           })
      logging.debug('json response %s' % response_dict);
            
      self.response.headers['Content-Type'] = 'application/javascript'
      self.response.out.write(simplejson.dumps(response_dict))

## end AddTestHandler

# converts a character to the equivalent keypad number
def getkeypad(x):
    return {'a':'2',
          'b':'2',
          'c':'2',
          'd':'3',
          'e':'3',
          'f':'3',
          'g':'4',
          'h':'4',
          'i':'4',
          'j':'5',
          'k':'5',
          'l':'5',
          'm':'6',
          'n':'6',
          'o':'6',
          'p':'7',
          'q':'7',
          'r':'7',
          's':'7',
          't':'8',
          'u':'8',
          'v':'8',
          'w':'9',
          'x':'9',
          'y':'9',
          'z':'9',
         }.get(x,'1')
## end getkeypad()

def computeKeypadAnswer(word):
    answer = ' '
    for c in word:
        answer += getkeypad(c)
    logging.debug('computed answer %s for the word %s' % (answer,word))
    return answer.strip(' ')
## end computeKeypadAnswer

def main():
    logging.getLogger().setLevel(logging.DEBUG)
    application = webapp.WSGIApplication([('/', MainHandler),
                                          ('/addtest', AddTestHandler),
                                         ],
                                         debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
