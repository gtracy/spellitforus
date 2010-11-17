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

ACCOUNT_SID = "your-account-sid"
ACCOUNT_TOKEN = "your-auth-token"
API_VERSION = '2010-04-01'
CALLER_ID = '+1yournumber'

class StartTestHandler(webapp.RequestHandler):
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
            self.error(403)
            return
            
        logging.debug('Starting a test with %s' % caller)
        
        testID = self.request.get('id')
        logging.debug('Looking up test with key %s' % testID)
        userTest = UserTest()
        userTest.test = db.get(testID)
        userTest.user = userhandlers.getUser(users.get_current_user().user_id())

        userTest.score = 0
        userTest.put()
        
        index = 0
        nextWord = userTest.test.words[index]
        id = userTest.key()

        account = twilio.Account(ACCOUNT_SID, ACCOUNT_TOKEN)
        tra = {'From' : CALLER_ID,
               'To' : caller,
               'Url' : 'http://spellitforus.appspot.com/test/quiz?word=%s&index=%s&id=%s'
                       % (nextWord,str(index),id),
              }
        try:
            logging.debug("placing call to %s" % caller)
            account.request('/%s/Accounts/%s/Calls/' % (API_VERSION, ACCOUNT_SID),
                            'POST', tra)
        except Exception, e:
            logging.error("Twilio REST error: %s" % e)

        self.response.headers['Content-Type'] = 'text/xml'
        self.response.out.write('<goodness/>')
## end StartTestHandler

## http://spellitforus.appspot.com/test/quiz
class GenerateQuizTwiml(webapp.RequestHandler):
    def post(self):
        userTest = db.get(self.request.get('id'))
        word = self.request.get('word')
        userAnswer = self.request.get('Digits')
        wordIndex = self.request.get('index')
        index = int(wordIndex)
        
        # if there was an answer, check for accuracy
        if userAnswer:
            if userAnswer == userTest.test.wordAnswers[index]:
                logging.debug('%s answered %s is correct!' % (word,userAnswer))
                # correct answer - update the score
                userTest.score += 1
                userTest.put()
            else:
                logging.debug('%s answered %s is INcorrect!' % (word,userAnswer))
            index += 1        
        
        # (else) note that the first word starts the test so there
        # doesn't have to be an answer each time
                    
        r = twilio.Response()
        if index == len(userTest.test.words) :
            userTest.test.testsTaken += 1
            userTest.test.put()
            
            # they've completed the test - report their score
            if userTest.score == len(userTest.test.words):
                prompt = 'Awesome.  That is a perfect score!'
            elif userTest.score < (userTest.score / len(userTest.test.words)):
                prompt = 'You had %s out of %s correct answers. Better luck next time!' % (userTest.score,len(userTest.test.words))
            else:
                prompt = 'You had %s out of %s correct answers. Great job!' % (userTest.score,len(userTest.test.words))
            
            r.append(twilio.Say(prompt,
                                voice=twilio.Say.WOMAN,
                                language=twilio.Say.ENGLISH,
                                loop=1))
        else:
            # special case the first run through
            if index == 0:
                newWord = word
            else:
                newWord = userTest.test.words[index]
                
            logging.debug('setting up gather request for word %s at index %s' 
                          % (word,str(index)))
            gather = twilio.Gather('http://spellitforus.appspot.com/test/quiz?word=%s&id=%s&index=%s' 
                                   % (newWord,self.request.get('id'),str(index)),
                                   method='POST')
            if not userTest.test.wordRecordings:
                 gather.append(twilio.Say(newWord,
                                         voice=twilio.Say.MAN,
                                         language=twilio.Say.ENGLISH,
                                         loop=1))
            elif len(userTest.test.wordRecordings[index]) < 5:
                 gather.append(twilio.Say(newWord,
                                         voice=twilio.Say.MAN,
                                         language=twilio.Say.ENGLISH,
                                         loop=1))
            else:
                gather.append(twilio.Play(userTest.test.wordRecordings[index],
                                          loop=1))
            r.append(gather)

        self.response.out.write(r)

## end GenerateQuizTwiml

def main():
    logging.getLogger().setLevel(logging.DEBUG)
    application = webapp.WSGIApplication([('/test/start', StartTestHandler),
                                          ('/test/quiz', GenerateQuizTwiml),
                                         ],
                                         debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
