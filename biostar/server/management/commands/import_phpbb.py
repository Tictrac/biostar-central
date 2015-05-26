from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
import sys, logging, os
from django.core.exceptions import ImproperlyConfigured
from datetime import date
from django.utils import timezone
from django.conf import settings

logger = logging.getLogger('simple-logger')

class Command(BaseCommand):
    help = 'Import from .sql backup'

    option_list = BaseCommand.option_list + (
        make_option("-f", '--file', dest='file', default=False, help='import file'),
    )

    def handle(self, *args, **options):
        fname = options['file']

        if fname:
        	if fname.endswith('.sql'):
        		import_bb_file(fname)
        	else:
        		logger.error('Wrong format! Please provide and sql file (.sql)')
        else:
        	if not fname:
        		logger.error('No file name supplied')
        	logger.info('try -h for more help')


#Removes unwanted lines from sql file
def sanitize(filename):
    f = open(filename,'r')
    sqltemp=[]
    for i in f.readlines():
        if i[0]!='-' and i[0]!='/' and i[0]!='\n':
            if i[-1:] == '\n':
                i=i[:-1]
            sqltemp.append(i)
    sql=[]
    temp=[]
    for i in sqltemp:
        if i[-1:]==';':
            temp.append(i)
            temp = ''.join(temp)
            sql.append(temp)
            temp=[]
        else:
            temp.append(i)
    return sql


#Returns the post title and body from the INSERT instance
def spliting(string):
    lt = []
    for i in range(len(string)-1):
        if string[i]=="," and string[i+1]=="'":
            start=i+2
            for j in range(i+1,len(string)-1):
                if string[j]=="'" and string[j+1]==",":
                    end=j
                    break
            temp=string[start:end]
            lt.append(temp)
            i=j+1

    tb=[lt[2],lt[3]]
    return tb


#Fetches the environment variable
def get_env(name, func=None):
    """Get the environment variable or return exception"""
    try:
        if func:
            return func(os.environ[name])
        else:
            return unicode(os.environ[name], encoding="utf-8")
    except KeyError:
        msg = "*** Required environment variable %s not set." % name
        raise ImproperlyConfigured(msg)


#Imports the posts into django models
def import_posts(allposts):
	from biostar.apps.users.models import User
	from biostar.apps.posts.models import Post

	emailhost=get_env('EMAIL_HOST')
	email = 'sqlimport@' + emailhost + '.com'
	try:
		u = User.objects.get(email=email)
	except:
		u = User(email=email, name='sqlimport')
		u.save()
		u.profile.date_joined = timezone.now()
		u.profile.last_login = timezone.now()
		u.profile.save()

	post_count=0
	for single in allposts:
		title = single[0]
		body = single[1]
		logger.info('Fetched post : %s' % title)
		if title.startswith('Re:'):
			ptitle = title[4:]
			try:
				parent = Post.objects.get(title=ptitle)
				post = Post(title=title, content=body, author=u, type= Post.ANSWER)
				post.parent=parent
				post.root=parent
				post.save()
				post_count+=1
			except:
				pass
		else:
			post = Post(title=title, content=body, author=u, type = Post.QUESTION)
			post.save()
			post_count+=1
	logger.info('%d posts created' % post_count)



#Governs the improt process
def import_bb_file(fname):
	logger.info('Sanitizing file')
	sql = sanitize(fname)

    #Retrieves index line with post table
	logger.info('Parsing file...')
	for i in range(0,len(sql)):
		if sql[i].startswith('INSERT INTO `phpbb_posts`'):
			index = i
			break

	sql = sql[index]
	#Retrieves all posts
	sql = sql[33:]

	#Split posts into different INSERT instances
	sql = sql.split('),(')

	#Gettings all post title and body as list
	logger.info('Retrieving posts...')
	posts=[]
	for i in sql:
		post=spliting(i)
		posts.append(post)

	import_posts(posts)
	logger.info('DONE!')


if __name__ == '__main__':
    pass