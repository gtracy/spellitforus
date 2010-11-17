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
import testing


class RecordWord(webapp.RequestHandler):
    def post(self):
        user = userhandlers.getUser(users.get_current_user().user_id())
        if not user:
            logging.error("no user is logged in!")
            self.error(404)
            return
        
        if self.request.get('caller'):
            caller = '+1'+self.request.get('caller')
        elif user.phoneNumber:
            caller = '+1'+user.phoneNumber
        else:
            logging.error("impossible! the user doesn't have a number configured yet")
            self.error(403)
            return
        account = twilio.Account(testing.ACCOUNT_SID, testing.ACCOUNT_TOKEN)

        tra = {'From' : testing.CALLER_ID,
               'To' : caller,
               'Url' : 'http://spellitforus.appspot.com/record/recordtwiml?code=%s&index=%s'
                       % (self.request.get('code'),self.request.get('index')),
              }
        try:
            logging.debug("placing call to %s" % caller)
            account.request('/%s/Accounts/%s/Calls/' % (testing.API_VERSION, testing.ACCOUNT_SID),
                            'POST', tra)
        except Exception, e:
            logging.error("Twilio REST error: %s" % e)

        self.response.headers['Content-Type'] = 'text/xml'
        self.response.out.write('<goodness/>')
        
## end RecordWord
        
class RecordWordTwiml(webapp.RequestHandler):
    def post(self):
      # setup the response to get the recording from the caller
      r = twilio.Response()
      r.append(twilio.Say("Say your word after the beep", 
                          voice=twilio.Say.MAN,
                          language=twilio.Say.ENGLISH, 
                          loop=1))
      r.append(twilio.Record("http://spellitforus.appspot.com/record/recording?code=%s&index=%s" 
                               % (self.request.get('code'),self.request.get('index')), 
                             twilio.Record.POST, 
                             maxLength=10))
      logging.info("now asking the caller to record their message...")
      self.response.out.write(r)
        
## end RecordWordTwiml

class SaveWordRecording(webapp.RequestHandler):
    def post(self):
        logging.debug('got the recording...')
        url = self.request.get('RecordingUrl')
        code = self.request.get('code')
        index = int(self.request.get('index'))
        logging.debug('saving the word recording for %s (%s)' % (code,url))
        
        # check to see if we've already created this test model
        test = db.GqlQuery("SELECT * FROM Test WHERE randHandle = :1", code).get()
        if test is None:
            test = Test()
            test.randHandle = code
            test.wordRecordings = ['no']*5
            test.wordRecordings[index] = url
        else:
            test.wordRecordings[index] = url
        
        logging.debug("placing recording for code %s at index %s (%s)"
                      % (code,self.request.get('index'),url))
        test.put()
        
        r = twilio.Response()
        r.append(twilio.Say("Got it. Thanks.", 
                          voice=twilio.Say.WOMAN,
                          language=twilio.Say.ENGLISH, 
                          loop=1))
        self.response.out.write(r)
              
## end SaveWordRecording

def main():
    logging.getLogger().setLevel(logging.DEBUG)
    application = webapp.WSGIApplication([('/record/recordword', RecordWord),
                                          ('/record/recordtwiml', RecordWordTwiml),
                                          ('/record/recording', SaveWordRecording),
                                         ],
                                         debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
