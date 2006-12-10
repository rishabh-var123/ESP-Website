# Django settings for esp project.

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Adam Seering', 'aseering@mit.edu'),
    ('Mike Axiak', 'axiak@mit.edu')
)
MANAGERS = ADMINS

DATABASE_ENGINE = 'postgresql'           # 'postgresql', 'mysql', 'sqlite3' or 'ado_mssql'.
DATABASE_NAME = 'django'             # Or path to database file if using sqlite3.
DATABASE_USER = 'esp'             # Not used with sqlite3.
DATABASE_PASSWORD = 'password'         # Not used with sqlite3.
DATABASE_HOST = '192.168.1.1'             # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.

# Local time zone for this installation. All choices can be found here:
# http://www.postgresql.org/docs/current/static/datetime-keywords.html#DATETIME-TIMEZONE-SET-TABLE
TIME_ZONE = 'America/New_York'

# Language code for this installation. All choices can be found here:
# http://www.w3.org/TR/REC-html40/struct/dirlang.html#langcodes
# http://blogs.law.harvard.edu/tech/stories/storyReader$15
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = '/esp/esp/media/uploaded/'

# URL that handles the media served from MEDIA_ROOT.
# Example: "http://media.lawrence.com"
MEDIA_URL = '/media/uploaded/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/admin/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'm)^ea+0^rg5w73-h9d$t)#1@jsf+0km97_rbnpy2884b^%t&wo'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.doc.XViewMiddleware',
)

ROOT_URLCONF = 'esp.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates".
    # Always use forward slashes, even on Windows.
    '/esp/esp/templates'
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'esp.datatree',
    'esp.miniblog',
    'esp.users',
    'esp.workflow',
    'esp.dbmail',
    'esp.program',
    'esp.cal',
    'esp.lib',
    'esp.setup',
    'esp.unittest',
    'esp.web',
    'esp.qsd',
    'esp.qsdmedia',
    'esp.satprep',
    'esp.money',
    'esp.resources',
    'esp.poll',
    'esp.dblog',
)

EMAIL_HOST = 'outgoing.mit.edu'
APPEND_SLASH=False
