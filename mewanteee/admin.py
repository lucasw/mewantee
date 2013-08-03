
import cgi
import wsgiref.handlers
import os
import mewantee

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template


class ActivateUsersPage(webapp.RequestHandler):
	def get(self, nickname):

		account = mewantee.Account.gql("WHERE nickname=:1 ORDER BY date DESC", nickname).get();
		account.active = not account.active
		account.put()

	#	if account.active:
	#		self.response.out.write("activated")
	#	else:
	#		self.response.out.write("deactivated")

	#	self.response.out.write("<a href=\"/admin/users/\">return</a>")

		self.redirect('/admin/users')

class AdminUsersPage(webapp.RequestHandler):
	def get(self):

		user = users.get_current_user()

		accountlist = mewantee.Account.gql("ORDER BY date DESC")

		(account, url_linktext, url) = mewantee.FlimUtility().loginoutUrls(self,user)

		# index
		template_values = {
			'user': user,
			'accountlist': accountlist,
			#           'message': message,
			'account': account,
			#           'requests': requests,
			'url': url,
			'url_linktext': url_linktext,
		}

		path = os.path.join(os.path.dirname(__file__), 'adminusers.html')
		self.response.out.write(template.render(path, template_values))


def admin():
	application = webapp.WSGIApplication([
	('/admin/users', AdminUsersPage),
	('/admin/users/activate/(.*)', ActivateUsersPage),
	],
	debug=True)
	wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
	admin()

