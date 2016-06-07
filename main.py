#!/usr/bin/env python
# coding=UTF-8
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import webapp2
import cgi
import re
import os
import jinja2
import hashlib
import hmac
import random
import string
import time
import json
import logging
from datetime import datetime
import mimetypes

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape=True, trim_blocks=True) 

from google.appengine.ext import ndb
from google.appengine.api import images
from google.appengine.api import memcache

############################################################################################################
# utils #

class Handler(webapp2.RequestHandler):
	#produces the actual html
	def write(self, *a, **kw):
		self.response.out.write(*a, **kw)

	#load the template, and produces a string with the data in params    
	def render_str(self, template, **params):
		t = jinja_env.get_template(template)
		return t.render(params)

	#combines previous two.     
	def render(self, template, **kw):
		self.write(self.render_str(template, **kw))

class Validate():
	secret = "kdebfzhkfblzuhcjsdhbcjskbfkjufuehfzuijkpmm"

	def validUser(self,username):
		USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
		return USER_RE.match(username)

	def validPass(self,password):
		USER_PASS = re.compile(r"^.{3,20}$")
		return USER_PASS.match(password)

	def validEmail(self,email):
		USER_MAIL = re.compile(r"^[\S]+@[\S]+\.[\S]+$")
		return USER_MAIL.match(email)

	def makeSecureString(self,s):
		return str("%s|%s" %(s,hmac.new(self.secret, s, hashlib.sha256).hexdigest()))

	def checkValue(self,value,secureString):
		if self.makeSecureString(value)==secureString:
			return value
	
	def make_salt(self):
		return ''.join(random.choice(string.letters) for x in xrange(5))

	def makePwHash(self, name, pw, salt=None):
		salt = self.make_salt() if not salt else salt
		hsh = hashlib.sha256(name+pw+salt).hexdigest()
		return (hsh,salt)

	def existingUser(self, name, pw, hsh, salt):
		tmp = self.makePwHash(name, pw, salt)[0] 
		return (hsh == tmp)

class UsrEntry(ndb.Model):
	name = ndb.StringProperty(required = True)
	password = ndb.StringProperty(required = True)
	salt = ndb.StringProperty(required = True)
	email = ndb.StringProperty(required = False)
	created = ndb.DateTimeProperty(auto_now_add = True)
	# language = db.StringProperty(required = False)


class Images(ndb.Model):
	file_name = ndb.StringProperty()
	blob = ndb.BlobProperty()

class UsrAccHandler(Handler,Validate):

	licenceNbr = "licence"
	
	def get(self, pageAdr = None):
		self.render("usrAccount.html", signingUp=True)

	def post(self,pageAdr = None):
		usr = self.request.get('username')
		passwd = self.request.get('password')
		verif = self.request.get('verify')
		mail = self.request.get('email')
		licNbr = self.request.get('licence')

		wrgUsr = "wrong username" if (not self.validUser(usr)) else ""
		wrgPswd = "wrong password" if (not self.validPass(passwd)) else ""
		wrgMatch = "passwords don't match" if (passwd != verif) else ""
		wrgMail = "wrong email" if (mail and (not self.validEmail(mail))) else ""
		wrgLicNbr = "wrong licence" if (not str(licNbr) == self.licenceNbr) else ""

		if not (wrgUsr or wrgPswd or wrgMatch or wrgMail or wrgLicNbr):
			
			usrData = (ndb.gql("SELECT * FROM UsrEntry WHERE name = :usrname", usrname=usr)).get()
			if not usrData:
				(hsh,salt) = self.makePwHash(usr,passwd)
				newUsr = UsrEntry(name=usr, password=hsh, salt=salt, email=mail)
				newUsr.put()
				self.response.headers.add_header('Set-Cookie', 'name=%s; Path=/' %self.makeSecureString(usr))
				self.redirect("/")
			else:
				self.render("usrAccount.html", error="user already registered", signingUp=True)
				
		else:
			logging.error(licNbr)
			logging.error(self.licenceNbr)

			self.render("usrAccount.html",
						 usr = cgi.escape(usr),
						 mail = cgi.escape(mail),
						 wrgUsr = wrgUsr,
						 wrgPswd = wrgPswd,
						 wrgMatch = wrgMatch,
						 wrgMail = wrgMail,
						 wrgLicNbr = wrgLicNbr,
						 signingUp=True)

class LoginHandler(Handler, Validate):

	def get(self):
		self.render("login.html", loggedout=True)

	def post(self):
		usr = self.request.get('username')
		passwd = self.request.get('password')

		wrgUsr = "wrong username" if (not self.validUser(usr)) else ""
		wrgPswd = "wrong password" if (not self.validPass(passwd)) else ""

		usrData = (ndb.gql("SELECT * FROM UsrEntry WHERE name = :usrname", usrname=usr)).get()


		if (not (wrgUsr or wrgPswd)):
			if  usrData and self.existingUser(usr, passwd, usrData.password, usrData.salt):
				self.response.headers.add_header('Set-Cookie', 'name=%s; Path=/' %self.makeSecureString(usr))
				self.redirect('/')
			else:
				self.render("login.html",error="wrong username and/or password!", loggedout=True)
		else:
			self.render("login.html",
						 usr = cgi.escape(usr),
						 wrgUsr = wrgUsr,
						 wrgPswd = wrgPswd,
						 loggedout=True)

class LogoutHandler(Handler):
	def get(self):
		self.response.headers.add_header('Set-Cookie', 'name=; Path=/')
		self.redirect("/")

###############################################################################

class MainHandler(Handler,Validate):
	def get(self):
		value = self.request.cookies.get('name')
		usr = value.split('|')[0] if value else None

		if usr and self.checkValue(usr,value):
			self.render("index.html",
						 usr=usr,
						 extraCss = "home.css",
						 extraJs  = "home.js" 
						)
			
		else:
			self.redirect("/login")

class MapHandler(Handler,Validate):
	def get(self):
		value = self.request.cookies.get('name')
		usr = value.split('|')[0] if value else None

		if usr and self.checkValue(usr,value):
			self.render("map.html",
						 usr=usr,
						 extraCss = "stylemap.css",
						 extraJs = "yamana.js"
						)
			
		else:
			self.redirect("/login")

class PlantsHandler(Handler,Validate):
	def get(self):
		value = self.request.cookies.get('name')
		usr = value.split('|')[0] if value else None

		if usr and self.checkValue(usr,value):
			self.render("plants.html",
						 usr=usr,
						 extraCss = "plants.css",
						 extraJs = "plants.js"
						)
		else:
			self.redirect("/login")

class PlantUpdateHandler(Handler,Validate):
	def get(self):
		value = self.request.cookies.get('name')
		usr = value.split('|')[0] if value else None

		if usr and self.checkValue(usr,value):
			self.render("plantUpdate.html",
						 usr=usr,
						 extraCss = "plants.css",
						 extraJs = "plantUpdate.js"
						)
		else:
			self.redirect("/login")

	def post(self):

		file_upload = self.request.POST.get("file", None)
		file_name = file_upload.filename
		
		img = images.Image(file_upload.file.read())
		img.resize(width=80, height=100)
		img.im_feeling_lucky()
		thumbnail = img.execute_transforms(output_encoding=images.JPEG)


		image = Images(id=file_name, file_name=file_name, blob=thumbnail)

		image.put()

		self.response.headers[b'Content-Type'] = mimetypes.guess_type(image.file_name)[0]
		self.response.write(image.blob)

class PlantsJsonHandler(Handler,Validate):
	def get(self):
		value = self.request.cookies.get('name')
		usr = value.split('|')[0] if value else None

		if usr and self.checkValue(usr,value):
			
			test = {'name':('rose','玫瑰花')
				   ,'availability':[('greenhouse','05/12/')]
				   ,'usage':('w','w')
				   ,'remarks':('w','w')
				   ,'pics':[]
				   }
			
			self.response.headers['Content-Type'] = 'application/json; charset=UTF-8'
			self.write(str(json.dumps([test])))

		else:
			self.redirect("/login")

app = webapp2.WSGIApplication([
	('/', MainHandler),
	('/map',MapHandler),
	('/plants',PlantsHandler),
	('/plants_json',PlantsJsonHandler),
	('/signup',UsrAccHandler),
	('/login',LoginHandler),
	('/plant_update',PlantUpdateHandler),
	('/logout',LogoutHandler)
], debug=True)
