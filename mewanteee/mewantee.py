import cgi
import wsgiref.handlers

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext import db

import os
from google.appengine.ext.webapp import template

# this global isn't working right, store it in the database?
# or is there a good temporary per-user storage place?
#message = 'test'


##############################################################

class Request(db.Model):
	author = db.UserProperty()
	author_nickname = db.StringProperty(multiline=False)
	id = db.IntegerProperty()
	title = db.StringProperty(multiline=False)
	content = db.StringProperty(multiline=True)
	date = db.DateTimeProperty(auto_now_add=True)
	# use bounty Key instead?
	bounty_id = db.IntegerProperty()
	# TBD temp value for printing, always updated
	bounty = db.IntegerProperty()

##############################################################

class Bounty(db.Model):
	user = db.UserProperty()
	author_nickname = db.StringProperty(multiline=False)
	id = db.IntegerProperty()
	date = db.DateTimeProperty(auto_now_add=True)
  	points = db.IntegerProperty()
	request_id = db.IntegerProperty()

class AddBounty(webapp.RequestHandler):
	def add(this,self, request_id, bounty):
			
		user = users.get_current_user()

		if user:
			account = Account.gql("WHERE owner=:1 ORDER BY date DESC LIMIT 10", user).get()
			if not account:
				# no error page yet
				self.redirect('/error')
				return
		else :
			return

		# TBD check for negative bounties
		new_bounty = Bounty()
		new_bounty.user = user
		new_bounty.request_id = int(request_id)
		
		try: 
			new_bounty.points = bounty 
			#int(self.request.get('bounty'))
		except ValueError:
			message = 'invalid bounty %s' % bounty
			self.redirect('/')
			return

		if new_bounty.points > account.points:
			message = 'not enough points for that bounty'
			return
		else:
			account.points = account.points - new_bounty.points
			account.put()
	
		# TBD this probably fails when multiple users
		# are submitting comments at the same time 
		last_bounty = Bounty.gql("ORDER BY date DESC LIMIT 1").get()
		if last_bounty and last_bounty.id:
			new_bounty.id = last_bounty.id + 1
		else:
			new_bounty.id = 1
		
		new_bounty.put()

		return new_bounty.id

	def post(self,request_id):
	
		try: 
			bounty = int(self.request.get('bounty'))
		except ValueError:
			message = 'invalid bounty %s' % bounty
			self.redirect('/')
			return

		# the request won't point back to this new bounty
		# since it is a secondary one, but it can still be found and summed
		# up from the database
		AddBounty().add(self,request_id,bounty)
		
		self.redirect('/request/%s' % request_id)
		return

	# list all the recent bounties
	def get(self):

		user = users.get_current_user()
		bounties = Bounty.gql("ORDER BY date DESC LIMIT 50")

		message = ''

		(account, url_linktext, url) = FlimUtility().loginoutUrls(self,user)

		template_values = {
			'user': user,
			'message': message,
			'account': account,
			'bounties': bounties,
			'url': url,
			'url_linktext': url_linktext,
		}
		path = os.path.join(os.path.dirname(__file__), 'bounties.html')
		self.response.out.write(template.render(path, template_values))


##############################################################

class Payment(db.Model):
	user = db.UserProperty()
	author_nickname = db.StringProperty(multiline=False)
	receiver = db.UserProperty()
	receiver_nickname = db.StringProperty(multiline=False)
	id = db.IntegerProperty()
	points = db.IntegerProperty()
	date = db.DateTimeProperty(auto_now_add=True)
  	# the bounty this payment came out of, if any
	bounty_id = db.IntegerProperty()
	comment_id = db.IntegerProperty()
	request_id = db.IntegerProperty()

class AddPayment(webapp.RequestHandler):
	def post(self,request_id, comment_id):
		
		user = users.get_current_user()

		if user:
			account = Account.gql("WHERE owner=:1 ORDER BY date DESC", user).get()
			if not account:
				self.redirect('/error')
				return
		else :
			self.redirect('/error')
			return
		
		payment = Payment()
		payment.user = user 
		payment.author_nickname = account.nickname
		try:
			payment.points = int(self.request.get('paybounty'))
		except ValueError:
			self.redirect('/error')
			return

		payment.request_id = int(request_id)
		payment.comment_id = int(comment_id)
		
		comment = Commentz.gql("WHERE id=:1 ORDER BY date DESC", int(comment_id)).get()

		if not comment:
			self.redirect('/error')
			return

		if comment.author == user:
			self.redirect('/cantpayself')
			return

		receiver_account = Account.gql("WHERE owner=:1 ORDER BY date DESC", comment.author ).get()
		if not receiver_account:
			self.redirect('/error')
			return

		payment.receiver_nickname = receiver_account.nickname

		# get the most recent bounty made by this user if any
		# TBD - sum up all bounties from the same user on a request rather than posting individual ones
		bounty = Bounty.gql("WHERE user=:1 AND request_id=:2 ORDER BY date DESC", user, int(request_id)).get()
		if bounty and (payment.points <= bounty.points):
			payment.bounty_id = bounty.id

			bounty.points  = bounty.points - payment.points
			receiver_account.points = receiver_account.points + payment.points
			receiver_account.put()
			bounty.put()
		else:
			if (payment.points > account.points):
				self.redirect('/error')
				return
			account.points  = account.points - payment.points
			receiver_account.points = receiver_account.points + payment.points
			receiver_account.put()
			account.put()

		
		payment.put()
		self.redirect('/request/%s' % request_id)	

##############################################################

class FlimUtility():

	def loginoutUrls(this,self,user):
		account = None
	
		if user:
			account = Account.gql("WHERE owner=:1 ORDER BY date DESC LIMIT 10", user).get()
		
			url = users.create_logout_url(self.request.uri)
			url_linktext = 'logout'
					
		else:
			url = users.create_login_url(self.request.uri)
			url_linktext = 'login'

		return (account, url_linktext, url) 

	def getBounty(this, request_id):	
		bounties = Bounty.gql("WHERE request_id=:1 ORDER BY date DESC LIMIT 10", request_id)

		# this is probably not very efficient db access-wise, could do it better
		bounty = 0
		for thebounty in bounties:
			bounty = bounty + thebounty.points

		return bounty



##############################################################

class Commentz(db.Model):
	author = db.UserProperty()
	author_nickname = db.StringProperty(multiline=False)
	content = db.StringProperty(multiline=True)
	id = db.IntegerProperty()
	request_id = db.IntegerProperty()
	date = db.DateTimeProperty(auto_now_add=True)

class AddComment(webapp.RequestHandler):
	def post(self, id):
			
		user = users.get_current_user()

		if user:
			account = Account.gql("WHERE owner=:1 ORDER BY date DESC", user).get()
			if not account:
				self.redirect('/error')
				return
		else :
			self.redirect('/error')
			return

		commentz = Commentz()
		commentz.author = user 
		commentz.author_nickname = account.nickname
		commentz.content = self.request.get('comment')
		commentz.request_id = int(id)
		
		# TBD this probably fails when multiple users
		# are submitting comments at the same time 
		last_comment = Commentz.gql("ORDER BY date DESC LIMIT 1").get()
		if last_comment and last_comment.id:
			commentz.id = last_comment.id + 1
		else:
			commentz.id = 1

		k = commentz.put()
		self.redirect('/request/%s' % id)

	def get(self):

		user = users.get_current_user()
		comments = Commentz.gql("ORDER BY date DESC").fetch(50)

		message = '%s' % len(comments)

		(account, url_linktext, url) = FlimUtility().loginoutUrls(self,user)

		template_values = {
			'user': user,
			'message': message,
			'account': account,
			'comments': comments,
			'url': url,
			'url_linktext': url_linktext,
		}
		path = os.path.join(os.path.dirname(__file__), 'comments.html')
		self.response.out.write(template.render(path, template_values))


###############################################################

class Account(db.Model):
	owner = db.UserProperty()
	nickname = db.StringProperty(multiline=False)
	points = db.IntegerProperty()
	date = db.DateTimeProperty(auto_now_add=True)
	active = db.BooleanProperty()
	# TBD add account id?  or make the nickname be in the url?

class ManageAccount(webapp.RequestHandler):
	def post(self):
		
		user = users.get_current_user()

		if not user:
			self.redirect('/error')
			return

		# default starting account points
		account = Account()
		account.nickname = self.request.get('nickname')
		account.owner = user 
		account.points = 100
		# the admin must activate the account
		account.active = False
		account.put()

		self.redirect('/')

class AddRequest(webapp.RequestHandler):
	def post(self):
		request = Request()
	
		user = users.get_current_user()

		if user:
			request.author = user
			account = Account.gql("WHERE owner=:1 ORDER BY date DESC", user).get()
			if not account:
				self.redirect('/error')
				return
		else :
			return

		request.author_nickname = account.nickname

		request.title = self.request.get('title')
		request.content = self.request.get('content')
	
		# TBD this probably fails when multiple users
		# are submitting comments at the same time 
		last_request = Request.gql("ORDER BY date DESC").get()
		if last_request:
			request.id = last_request.id + 1
		else:
			request.id = 1

		try: 
			bounty = int(self.request.get('bounty'))
		except ValueError:
			message = 'invalid bounty %s' % self.request.get('bounty')
			self.redirect('/')
			return

		bounty_id = AddBounty().add(self, request.id, bounty)

		message = 'posted a new request'

		if bounty_id:
			request.bounty_id = bounty_id
			request.put()
	
		self.redirect('/')

############################################################################################

class FullRequest(webapp.RequestHandler):
	def get(self,request_id):

		user = users.get_current_user()

		request = Request.gql("WHERE id=:1", int(request_id)).get()
	
		request.bounty = FlimUtility().getBounty(request.id)

		comments = Commentz.gql("WHERE request_id=:1 ORDER BY date DESC LIMIT 50",request.id)

#		if not request:
#			self.redirect('/%s')	

		message = ''

		(account, url_linktext, url) = FlimUtility().loginoutUrls(self,user)
		
		template_values = {
			'user': user,
			'message': message,
			'account': account,
			'request': request,
			'comments': comments,
			'url': url,
			'url_linktext': url_linktext,
		}
		path = os.path.join(os.path.dirname(__file__), 'request.html')
		self.response.out.write(template.render(path, template_values))


#############################################################

class OldMainPage(webapp.RequestHandler):
	def get(self):
		
		message = ''

		# TBD fetch can be used for next/prev pages
		requests = Request.gql("ORDER BY date DESC").fetch(10)
		
		for i in range(0, len(requests)):
			requests[i].bounty = FlimUtility().getBounty(requests[i].id)
	
		#message = requests[0].author_nickname

		user = users.get_current_user()
		
		(account, url_linktext, url) = FlimUtility().loginoutUrls(self,user)
		
		# index
		template_values = {
			'user': user,
			'message': message,
			'account': account,
			'requests': requests,
			'url': url,
			'url_linktext': url_linktext,
		}
		path = os.path.join(os.path.dirname(__file__), 'index.html')
		self.response.out.write(template.render(path, template_values))



def oldmain():
	application = webapp.WSGIApplication(
					[('/', MainPage),
					('/request/(.*)',FullRequest), 
					('/addrequest', AddRequest),
					('/addbounty/(.*)', AddBounty),
					('/bounties', AddBounty),
					('/payment/(.*)/(.*)', AddPayment),
					('/payments', AddPayment),
					('/account', ManageAccount),
					('/comments', AddComment),
					('/comment/(.*)', AddComment)],
					debug=True)
	wsgiref.handlers.CGIHandler().run(application)

