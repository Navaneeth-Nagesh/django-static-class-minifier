# Django Static class minifier

### Description

The class minifier package shortens the class name in the DOM to single character and reduces the file size. more about the algorithm in the upcoming blog post.

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
'static_compressor.middleware.MinifyClassMiddleware', # Add this line, right after security middleware.
'django.contrib.sessions.middleware.SessionMiddleware',
```

Make sure, you have set up path of static files and static root directory.
```
STATICFILES_DIRS = (
os.path.join(BASE_DIR, 'static'),
)

STATIC_ROOT = os.path.join(BASE_DIR, 'all_staticfiles')
```
Update the static files storage:

`STATICFILES_STORAGE = 'static_compressor.staticfiles_storage.CompressedStaticFilesStorage'`

When you run `$ python manage.py collectstatic` it will have an additional post-processing pass to compress your static files and it creates data.json file which contains classes from all included css files and js files.

The class selectors which js files consider and change -
```
querySelector('.flex-box');
querySelectorAll('.flex-boxes');
classList.contains('active');
classList.add('active);
classList.remove('active');
classList.toggle('active');
```

If your adding classes to the DOM based on http response or a common function which appends class to the dom, then consider excluding those files. Right now that's the limitation of this project. In the future, There might be a syntax to consider those classes.

Make sure that your web server is configured to serve precompressed static files:

* If using nginx:
	* Setup [ngx_http_gzip_static_module](https://nginx.org/en/docs/http/ngx_http_gzip_static_module.html) to serve gzip (.gz) precompressed files. 
	* Out of tree module [ngx_brotli](https://github.com/google/ngx_brotli) is required to serve Brotli (.br) precompressed files.
* [Caddy](https://caddyserver.com/) will serve .gz and .br without additional configuration.

Also, as Brotli is not supported by all browsers you should make sure that your reverse proxy/CDN honor the Vary header, and your web server set it to [`Vary: Accept-Encoding`](https://blog.stackpath.com/accept-encoding-vary-important).

### Available Storages

* `static_compress.CompressedStaticFilesStorage`: Generate `.br` and `.gz` from your static files
* `static_compress.CompressedManifestStaticFilesStorage`: Like [`ManifestStaticFilesStorage`](https://docs.djangoproject.com/en/1.11/ref/contrib/staticfiles/#manifeststaticfilesstorage), but also generate compressed files for the hashed files
* `static_compress.CompressedCachedStaticFilesStorage`: Like [`CachedStaticFilesStorage`](https://docs.djangoproject.com/en/1.11/ref/contrib/staticfiles/#cachedstaticfilesstorage), but also generate compressed files for the hashed files
You can also add support to your own backend by applying `static_compressor.staticfiles_storage.CompressMixin` to your class.
By default it will only compress files ending with `.js`, `.css` and `.svg`. This is controlled by the settings below.

### Settings
_django-static-class-minifier_ settings and their default values:

```
EXCLUDE_STATIC_JS_FILES = [''] # exclude libraries from classnames minifier
EXCLUDE_STATIC_CSS_FILES = ['']
EXCLUDE_URL_MINIFIFICATION = ['']
MINIFY_CLASS_HTML =  False # Change it to True in production environment
# By default, the admin files classes won't be minified.
STATIC_CLASSES_FILE_NAME = 'data.json' # It should be an json file
EXCLUDED_CLASSNAMES_FROM_MINIFYING = ['']

STATIC_COMPRESS_FILE_EXTS = ['js', 'css', 'svg']
STATIC_COMPRESS_METHODS = ['gz', 'br']
STATIC_COMPRESS_KEEP_ORIGINAL = True
STATIC_COMPRESS_MIN_SIZE_KB = 30
```

### File size reduction
```
Original file - 100k style.css
compressed class minifier file - 70k style.css (30% reduction in file size)
(Note - reduction of the file depends on the number of class selectors used and the length of the class name.)
After brotli and Gzip compression - 40k style.css.gz (60% reduction in file size, in total), 35k style.css.br (65% reduction in file size) 
```
### Credits
I have merged the code with django-static-compress package to enable gzip and brotli compression.
In case, if you just use brotli and gzip compression without using class minifier. You can use [django-static-compress](https://github.com/whs/django-static-compress)
The author of django-static-compress [Manatsawin Hanmongkolchai](https://github.com/whs)

### Licence
Licensed under the [MIT License](https://github.com/Navaneeth-Nagesh/django-static-class-minifier/blob/master/LICENCE)