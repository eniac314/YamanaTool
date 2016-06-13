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
import pickle
from datetime import datetime
import mimetypes
import copy

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
	imgData = ndb.BlobProperty()
	# thumbnail = ndb.BlobProperty()

class Plant(ndb.Model):
	plantName = ndb.StringProperty()
	plantNameChinese = ndb.StringProperty()
	remarks = ndb.TextProperty()
	usage = ndb.TextProperty()
	availability = ndb.TextProperty()
	mainPic = ndb.StringProperty()
	pics = ndb.StringProperty()
	created = ndb.DateTimeProperty(auto_now_add = True)


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
						 extraCss = "plantUpdate.css",
						 extraJs = "plantUpdate.js"
						)
		else:
			self.redirect("/login")

	def post(self):

		plantName = self.request.get("plantName")
		plantNameChinese = self.request.get("plantNameChinese")
		remarks = self.request.get("remarks")
		usage = self.request.get("usage")
		nbrLoc = int(self.request.get("nbrLoc"))
		nbrPic = int(self.request.get("nbrPic"))

		locs = [(self.request.get('loc' + str(l)), self.request.get('date' + str(l))) for l in range (1,nbrLoc+1)]
		
		mainPic = self.request.POST.get("mainPicture", None)
		
		pics = [(self.request.POST.get('file' + str(p), None)) for p in range (1,nbrPic + 1)]

		newPlant = Plant( plantName = plantName
						, plantNameChinese = plantNameChinese
						, remarks = remarks
						, usage = usage
						, availability = pickle.dumps(locs)
						, mainPic = mainPic.filename
						, pics = pickle.dumps([p.filename for p in pics])
						)
		
		self.newImage(mainPic)
		[self.newImage(p) for p in pics]

		newPlant.put()

		self.write(str(newPlant))

		# data = images.Image(mainPic.file.read())
		# data.resize(width = 800, height = 600)
		# data.im_feeling_lucky()
		# self.response.write(data.execute_transforms(output_encoding=images.JPEG))
	
	def imgProcess(self,file,w,h):
		data = images.Image(file.file.read())
		data.resize(width = w, height = h)
		data.im_feeling_lucky()

		return (data.execute_transforms(output_encoding=images.JPEG))

	def newImage(self,file):
		
		pic = Images( id = file.filename
					  , file_name = file.filename
					  , imgData = self.imgProcess(file,800,600)
					  # , thumbnail = None #self.imgProcess(file,250,200)
					  )
		pic.put()
		return pic 


		# file_upload = self.request.POST.get("file", None)
		# file_name = file_upload.filename
		
		# img = images.Image(file_upload.file.read())
		# img.resize(width=80, height=100)
		# img.im_feeling_lucky()
		# thumbnail = img.execute_transforms(output_encoding=images.JPEG)


		# image = Images(id=file_name, file_name=file_name, blob=thumbnail)

		# image.put()

		# self.response.headers[b'Content-Type'] = mimetypes.guess_type(image.file_name)[0]
		# self.response.write(image.blob)

class LocationJsonHandler(Handler,Validate):
	def get(self):
		value = self.request.cookies.get('name')
		usr = value.split('|')[0] if value else None

		if usr and self.checkValue(usr,value):
			
			locs = [ '食物森林(鑰匙孔花園)'
				   , '螺旋花園'
				   , '麵包窯'
				   , '蚯蚓公寓'
				   , '生態濕地'
				   , '堆肥廁所'
				   , '蔓陀蘿花園'
				   , '香蕉圈堆肥'
				   , '生態池'
				   , '香蕉圈浴室'
				   , '柴薪堆放區'
				   , '自然建築(主屋，風雨教室)'
				   , '集水渠(標示線條的地方)'
				   , '香蕉圈'
				   , '天然堆肥'
				   , '桑椹'
				   , '防風林，緩衝帶，生物棲息地'
				   ]
			
			self.response.headers['Content-Type'] = 'application/json; charset=UTF-8'
			self.write(str(json.dumps(locs)))

		else:
			self.redirect("/login")

class PlantsJsonHandler(Handler,Validate):
	def get(self):
		value = self.request.cookies.get('name')
		usr = value.split('|')[0] if value else None

		if usr and self.checkValue(usr,value):
			
			# test = {'name':('rose','玫瑰花')
			# 	   ,'availability':[('greenhouse','05/12/')]
			# 	   ,'usage':('w','w')
			# 	   ,'remarks':('w','w')
			# 	   ,'pics':[]
			# 	   }
			

			plants = Plant.query()
			
			resp = [{'name':(p.plantName,p.plantNameChinese)
					,'availability':pickle.loads(p.availability)
					,'usage':(p.usage,"")
					,'remarks':(p.remarks,"")
					,'mainPic':p.mainPic 
					,'pics':pickle.loads(p.pics)
					} for p in plants]


			self.response.headers['Content-Type'] = 'application/json; charset=UTF-8'
			self.write(str(json.dumps(resp)))

		else:
			self.redirect("/login")

class ImgHandler(Handler,Validate):
	def get(self, picname):
		value = self.request.cookies.get('name')
		usr = value.split('|')[0] if value else None

		if usr and self.checkValue(usr,value):
			pic = Images.query(Images.file_name == picname).get()
			self.response.headers[b'Content-Type'] = mimetypes.guess_type(pic.file_name)[0]
			self.response.write(pic.imgData)
			# self.write(picname)
		else:
			self.redirect("/login")

class ThumbsHandler(Handler,Validate):
	def get(self, picname):
		value = self.request.cookies.get('name')
		usr = value.split('|')[0] if value else None

		if usr and self.checkValue(usr,value):
			pic = Images.query(Images.file_name == picname).get()
			
			data = images.Image(pic.imgData)
			data.resize(width = 250, height = 200)
			data.im_feeling_lucky()
			res = data.execute_transforms(output_encoding=images.JPEG)

			self.response.headers[b'Content-Type'] = mimetypes.guess_type(pic.file_name)[0]
			self.response.write(res)
			# self.write(picname)
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
	('/locations', LocationJsonHandler),
	('/thumbs/(\w*.\w*)', ThumbsHandler),
	('/img/(\w*.\w*)', ImgHandler),
	('/logout',LogoutHandler)

], debug=True)
