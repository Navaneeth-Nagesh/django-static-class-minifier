
# Django Static class minifier

  
[![Alt](https://camo.githubusercontent.com/2b5c48821f22738887c98a07f95852b610fb555b/68747470733a2f2f696d672e736869656c64732e696f2f61706d2f6c2f61746f6d69632d64657369676e2d75692e7376673f?raw=true  "MIT License")](https://github.com/Navaneeth-Nagesh/django-static-class-minifier/blob/master/LICENSE)  [![Alt](https://camo.githubusercontent.com/5536e335426d79f50ee2d88b57d6c108074992d7/68747470733a2f2f696d672e736869656c64732e696f2f707970692f707976657273696f6e732f7974326d70332e737667?raw=true  "Python 3")](https://pypi.org/project/django-static-class-minifier/) [![Alt](https://camo.githubusercontent.com/f12fbc1a9f48db714fa9e3fcc1e7a2c163d01bcd/68747470733a2f2f7472617669732d63692e6f72672f6d6f6363752f646a616e676f2d696e6c696e652d7374617469632e7376673f6272616e63683d6d6173746572?raw=true  "Build Passing")](https://pypi.org/project/django-static-class-minifier/) [![Alt](https://camo.githubusercontent.com/20eaa0afa205181685fcb1a6a396f5652f026b1a/68747470733a2f2f696d672e736869656c64732e696f2f62616467652f636f64652532306f662d636f6e647563742d6666363962342e7376673f7374796c653d666c6174?raw=true  "Code of Conduct")](https://github.com/Navaneeth-Nagesh/django-static-class-minifier/blob/master/docs/CODE_OF_CONDUCT.md) [![Alt](https://camo.githubusercontent.com/614c7585c82b25086d62bfe7745aa9f765291151/68747470733a2f2f72656164746865646f63732e6f72672f70726f6a656374732f7974326d70332f62616467652f3f76657273696f6e3d6c6174657374?raw=true  "Docs Passing")](https://github.com/Navaneeth-Nagesh/django-static-class-minifier) 

### Description

  

The class minify package shortens the class name in the DOM to gibberish characters with reducing the size of the actual class name and which helps to reduces the file size and which also makes web scrappers difficult to scrap the website.

  

End result : ![Alt](https://github.com/Navaneeth-Nagesh/django-static-class-minifier/blob/master/snaps/example.JPG?raw=true  "Example")

  
  

### Installation

  

`$ pip install django-static-class-minifier`

  

(you may want to write this in your requirements.txt)

  

In settings.py -

  

In Installed apps -

```

INSTALLED_APPS = [

'django.contrib.sessions',

'django.contrib.messages',

'django.contrib.staticfiles',

'static_compressor', #installed app

'.....'

]

```

In Middleware -

```

MIDDLEWARE = [

'django.middleware.security.SecurityMiddleware',

'django.contrib.sessions.middleware.SessionMiddleware',

'django.middleware.common.CommonMiddleware',

'django.middleware.csrf.CsrfViewMiddleware',

'static_compressor.middleware.MinifyClassMiddleware', # Add this line, right after csrf middleware.

'django.contrib.auth.middleware.AuthenticationMiddleware',

```

  

Make sure, you have set up path of static files and static root directory.

```

STATICFILES_DIRS = (

os.path.join(BASE_DIR, 'static'),

)

  

STATIC_ROOT = os.path.join(BASE_DIR, 'all_staticfiles')

```

Update the static files storage:

  

```

STATICFILES_STORAGE = 'static_compressor.staticfiles_storage.CompressedStaticFilesStorage'

```

*Run the below command in your terminal to build the static files.*

  

```

$ python manage.py collectstatic_compress

```

  

When you run `$ python manage.py collectstatic_compress` it will have an additional post-processing to compress your static files and it creates *data.json* file which contains classes from all included css and js files.

  

The class selectors which js files considers and change :

```

querySelector('.flex-box');

querySelectorAll('.flex-boxes');

classList.contains('active');

classList.add('active);

classList.remove('active');

classList.toggle('active');

```

  

If your adding classes to the DOM based on http response or a common function which appends class to the DOM, then consider excluding those words. Use *EXCLUDED_CLASSNAMES_FROM_MINIFYING* setting attribute and include those words in the list.

  

Make sure that your web server is configured to serve precompressed static files:

  

* If using nginx:

* Setup [ngx_http_gzip_static_module](https://nginx.org/en/docs/http/ngx_http_gzip_static_module.html) to serve gzip (.gz) precompressed files.

* Out of tree module [ngx_brotli](https://github.com/google/ngx_brotli) is required to serve Brotli (.br) precompressed files.

*  [Caddy](https://caddyserver.com/) will serve .gz and .br without additional configuration.

  

Also, as Brotli is not supported by all browsers you should make sure that your reverse proxy/CDN honor the Vary header, and your web server set it to [`Vary: Accept-Encoding`](https://blog.stackpath.com/accept-encoding-vary-important).

  

### Available Storages

  

*  `static_compress.CompressedStaticFilesStorage`: Generate `.br` and `.gz` from your static files

*  `static_compress.CompressedManifestStaticFilesStorage`: Like [`ManifestStaticFilesStorage`](https://docs.djangoproject.com/en/1.11/ref/contrib/staticfiles/#manifeststaticfilesstorage), but also generate compressed files for the hashed files

*  `static_compress.CompressedCachedStaticFilesStorage`: Like [`CachedStaticFilesStorage`](https://docs.djangoproject.com/en/1.11/ref/contrib/staticfiles/#cachedstaticfilesstorage), but also generate compressed files for the hashed files

You can also add support to your own backend by applying `static_compressor.staticfiles_storage.CompressMixin` to your class.

By default it will only compress files ending with `.js`, `.css` and `.svg`. This is controlled by the settings below.

  

### Settings

  

_django-static-class-minifier_ settings and their default values:

  

```

MINIFY_CLASS_HTML = False # Change it to True in production environment

EXCLUDE_STATIC_JS_FILES = [] # exclude js libraries from classnames minifier

EXCLUDE_STATIC_CSS_FILES = []

EXCLUDE_STATIC_SVG_FILES = []

EXCLUDE_STATIC_DIRECTORY = []

EXCLUDE_URL_MINIFICATION = []

EXCLUDED_CLASSNAMES_FROM_MINIFYING = []

# By default, the admin files classes won't be minified.

STATIC_CLASSES_FILE_NAME = 'data.json' # It should be an json file

CLASS_SALT_VALUE = 'ascii_lowercase' # Choices - 'ascii_lowercase' or 'ascii_uppercase' or 'ascii_letters' or custom characters. The custom characters should not contain special characters and the length of salt should be greater then 8. Example : CLASS_SALT_VALUE = '_abcdefghijk123'.

  
# Incase, Inside your app if there is static directory then include it in STATIC_INCLUDE_DIRS

  

STATIC_INCLUDE_DIRS = (

os.path.join(BASE_DIR, 'faq/static'), # Example : Let the app name be faq

)

STATIC_COMPRESS_FILE_EXTS = ['js', 'css', 'svg']

STATIC_COMPRESS_METHODS = ['gz', 'br']

STATIC_COMPRESS_KEEP_ORIGINAL = True

STATIC_COMPRESS_MIN_SIZE_KB = 30

```

### Configuration Types :

|Settings|Type | Description|
|---|---|---|
|EXCLUDE_STATIC_JS_FILES| _Array_ |These js files will be excluded from classnames shortening, In other words the class names won't be changed. |
|EXCLUDE_STATIC_CSS_FILES|_Array_|Same as above but for css files.
|EXCLUDE_STATIC_SVG_FILES| _Array_| Same as above but for svg files |
|EXCLUDE_STATIC_DIRECTORY| _Array_| The directory name in the array will be excluded from class names shortening.|
|EXCLUDE_URL_MINIFICATION|_Array_| The URL in the array will exclude from shortening of class names.
|EXCLUDED_CLASSNAMES_FROM_MINIFYING|_Array_| The words in an array won't be shortened.
|MINIFY_CLASS_HTML|_Boolean_| If its True it minifies class names in the HTML. Make sure there is JSON file or it will throws an error.
|STATIC_CLASSES_FILE_NAME|_String_| The JSON file name. By default its data.json|
|STATIC_INCLUDE_DIRS|_Tuple_| Includes static directory inside the app.|
|CLASS_SALT_VALUE|_String_|Choices - 'ascii_lowercase' or 'ascii_uppercase' or 'ascii_letters' or custom characters. The custom characters should not contain special characters and the length of salt should be greater then 8. Example : CLASS_SALT_VALUE = '_abcdefghijk123'.|


### File size reduction

```

Original file - 100k style.css

compressed class minifier file - 70k style.css (30% reduction in file size)

(Note - reduction of the file depends on the number of class selectors used and the length of the class name.)

After brotli and Gzip compression - 40k style.css.gz (60% reduction in file size, in total), 35k style.css.br (65% reduction in file size)

```

  

### Licence

[![Alt](https://camo.githubusercontent.com/2b5c48821f22738887c98a07f95852b610fb555b/68747470733a2f2f696d672e736869656c64732e696f2f61706d2f6c2f61746f6d69632d64657369676e2d75692e7376673f?raw=true  "MIT License")](https://github.com/Navaneeth-Nagesh/django-static-class-minifier/blob/master/LICENSE)

  

_Happy coding! :)_