import cgi
import wsgiref.handlers
import os
#import admin
import mewantee

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template


class MainPage(webapp.RequestHandler):
	def get(self):


		user = users.get_current_user()
		
		(account, url_linktext, url) = mewantee.FlimUtility().loginoutUrls(self,user)
		
		# index
		template_values = {
			'user': user,
#			'message': message,
			'account': account,
#			'requests': requests,
			'url': url,
			'url_linktext': url_linktext,
		}

		path = os.path.join(os.path.dirname(__file__), 'index.html')
		self.response.out.write(template.render(path, template_values))

def main():



	application = webapp.WSGIApplication([ 
			('/', 			MainPage),	
			#('/admin/users', admin.AdminUsersPage),
			('/request/(.*)', 		mewantee.FullRequest),
			('/addrequest', 		mewantee.AddRequest),
			('/addbounty/(.*)', 	mewantee.AddBounty),
			('/bounties', 			mewantee.AddBounty),
			('/payment/(.*)/(.*)', 	mewantee.AddPayment),
			('/payments', 			mewantee.AddPayment),
			('/account', 			mewantee.ManageAccount),
			('/comments', 			mewantee.AddComment),
			('/comment/(.*)',		mewantee.AddComment),
			],
		debug=True)
	wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
	main()
