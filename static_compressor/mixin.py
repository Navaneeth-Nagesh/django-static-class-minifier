import codecs
import json
from string import ascii_lowercase
import itertools
import string
import re
import os
from os.path import getatime, getctime, getmtime
import errno
import shutil

from django.core.exceptions import ImproperlyConfigured

from static_compressor import compressors
from django.contrib.staticfiles.storage import StaticFilesStorage

__all__ = ["CompressMixin"]


DEFAULT_METHODS = ["gz", "br"]
METHOD_MAPPING = {
    "gz": compressors.ZopfliCompressor,
    "br": compressors.BrotliCompressor,
    "gz+zlib": compressors.ZlibCompressor,
    # gz+zlib and gz cannot be used at the same time, because they produce the same file extension.
}


class CompressMixin:
    allowed_extensions = []
    compress_methods = []
    keep_original = True
    compressors = []
    minimum_kb = 0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # We access Django settings lately here, to allow our app to be imported without
        # defining DJANGO_SETTINGS_MODULE.
        from django.conf import settings

        self.frequency = dict()
        self.collection_of_classes = list()

        self.allowed_extensions = getattr(
            settings, "STATIC_COMPRESS_FILE_EXTS", ["js", "css", "svg"])
        self.compress_methods = getattr(
            settings, "STATIC_COMPRESS_METHODS", DEFAULT_METHODS)
        self.keep_original = getattr(
            settings, "STATIC_COMPRESS_KEEP_ORIGINAL", True)
        self.minimum_kb = getattr(settings, "STATIC_COMPRESS_MIN_SIZE_KB", 30)
        self.static_root = getattr(
            settings, "STATIC_ROOT", ".")

        self.exclude_js_files = getattr(
            settings, "EXCLUDE_STATIC_JS_FILES", [])
        self.exclude_css_files = getattr(
            settings, "EXCLUDE_STATIC_CSS_FILES", [])

        self.not_included_words = ['ttf', 'woff2', 'www', 'woff', 'js', 'otf', 'eot',
                                   'svg', 'com', 'in', 'css', 'add', 'contains', 'remove', 'toggle', 'move']

        if os.path.exists(self.static_root) and os.path.isdir(self.static_root):
            shutil.rmtree(self.static_root)

        valid = [i for i in self.compress_methods if i in METHOD_MAPPING]
        if not valid:
            raise ImproperlyConfigured(
                "No valid method is defined in STATIC_COMPRESS_METHODS setting.")
        if "gz" in valid and "gz+zlib" in valid:
            raise ImproperlyConfigured(
                "STATIC_COMPRESS_METHODS: gz and gz+zlib cannot be used at the same time.")
        self.compressors = [METHOD_MAPPING[k]() for k in valid]

    def get_alternate_compressed_path(self, name):
        for compressor in self.compressors:
            ext = compressor.extension
            if name.endswith(".{}".format(ext)):
                path = self.path(name)
            else:
                path = self.path("{}.{}".format(name, ext))
            if os.path.exists(path):
                return path
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), path)

    def get_accessed_time(self, name):
        if self.keep_original:
            return super().get_accessed_time(name)
        return self._datetime_from_timestamp(getatime(self.get_alternate_compressed_path(name)))

    def get_created_time(self, name):
        if self.keep_original:
            return super().get_created_time(name)
        return self._datetime_from_timestamp(getctime(self.get_alternate_compressed_path(name)))

    def get_modified_time(self, name):
        if self.keep_original:
            return super().get_modified_time(name)
        alt = self.get_alternate_compressed_path(name)
        return self._datetime_from_timestamp(getmtime(alt))

    def post_process(self, paths, dry_run=False, **options):
        if hasattr(super(), "post_process"):
            yield from super().post_process(paths, dry_run, **options)

        if dry_run:
            return

        for path in paths.keys():
            if not path.startswith('admin'):
                self._create_json_file(path)

        self._json_creation()

        for name in paths.keys():
            if not self._is_file_allowed(name):
                continue

            source_storage, path = paths[name]
          
            # Process if file is big enough
            if os.path.getsize(self.path(path)) < self.minimum_kb * 1024:
                continue
            src_mtime = source_storage.get_modified_time(path)
            dest_path = self._get_dest_path(path)
            with self._open(dest_path) as file:
                for compressor in self.compressors:
                    dest_compressor_path = "{}.{}".format(
                        dest_path, compressor.extension)
                    # Check if the original file has been changed.
                    # If not, no need to compress again.
                    full_compressed_path = self.path(dest_compressor_path)
                    try:
                        dest_mtime = self._datetime_from_timestamp(
                            getmtime(full_compressed_path))
                        file_is_unmodified = dest_mtime.replace(
                            microsecond=0) >= src_mtime.replace(microsecond=0)
                    except FileNotFoundError:
                        file_is_unmodified = False
                    if file_is_unmodified:
                        continue

                    # Delete old gzip file, or Nginx will pick the old file to serve.
                    # Note: Django won't overwrite the file, so we have to delete it ourselves.
                    if self.exists(dest_compressor_path):
                        self.delete(dest_compressor_path)
                    out = compressor.compress(path, file)

                    if out:
                        self._save(dest_compressor_path, out)
                        if not self.keep_original:
                            self.delete(name)
                        yield dest_path, dest_compressor_path, True

                    file.seek(0)

    def _create_json_file(self, file):
        if file.endswith('.css'):
            if file not in self.exclude_css_files:
                with self._open(file) as current_file:
                    read_css_file = current_file.read().decode('utf-8').strip()

                    # To remove quotes in css
                    remove_unwanted_css_fragments = re.sub(re.compile(
                        "[\'\"].*?[\'\"]", re.DOTALL), '', read_css_file)

                    # To remove stream of comments
                    remove_unwanted_css_fragments = re.sub(re.compile(
                        "/\*.*?\*/", re.DOTALL), '', remove_unwanted_css_fragments)
                            
                    # To remove single line comments
                    remove_unwanted_css_fragments = re.sub(re.compile(
                        "//.*?\n"), '', remove_unwanted_css_fragments)

                    regex = re.compile(
                        r'\.-?[_a-zA-Z]+[_a-zA-Z0-9-]*[^#+@+,+.+)+/+(+^+:+!+{+~+ +}+\'+\"+>+<+^+[+]')

                    all_classes = regex.findall(
                        remove_unwanted_css_fragments)
                    for class_instance in all_classes:
                        word = class_instance[1:]
                        self.collection_of_classes.append(word)

        if file.endswith('.svg'):
            with self._open(file) as current_file:
                read_svg_file = current_file.read().decode('utf-8').strip()

                regex = re.compile(r'class[ \t]*=[ \t]*"[^"]+"')
                all_classes = regex.findall(read_svg_file)
                for class_instance in all_classes:
                    for class_name in class_instance[7:-1].split():
                        self.collection_of_classes.append(class_name)
                
        if file.endswith('.js'):
            if not file in self.exclude_js_files:
                with self._open(file) as current_file:
                    read_js_file = current_file.read().decode('utf-8').strip()

                    query_selector_regex = re.compile(
                        r'querySelector\([\'\"][^\'\"]*?\.[^\'\"]*?[\'\"]\)')
                    query_selector_classname = query_selector_regex.findall(
                        read_js_file)

                    query_selector_all_regex = re.compile(
                        r'querySelectorAll\([\'\"][^\'\"]*?\.[^\'\"]*?[\'\"]\)')
                    query_selector_all_classname = query_selector_all_regex.findall(
                        read_js_file)

                    get_element_by_classname_regex = re.compile(
                        r'getElementsByClassName\([\'\"]([^)]+)[\'\"]\)')
                    get_elements_by_classes = get_element_by_classname_regex.findall(
                        read_js_file)

                    get_just_class_from_selectors = re.compile(
                        r'\.[_a-zA-Z]+[_a-zA-Z0-9-]*')
                    get_query_selector_class_name = get_just_class_from_selectors.findall(
                        ''.join(query_selector_classname))

                    get_query_selector_all_class_name = get_just_class_from_selectors.findall(
                        ''.join(query_selector_all_classname))

                    for instance in get_query_selector_all_class_name:
                        self.collection_of_classes.append(instance[1:])

                    for instance in get_query_selector_class_name:
                        self.collection_of_classes.append(instance[1:])

    
    def _json_creation(self):
        for word in self.collection_of_classes:
            class_instance = word.strip()

            if not word in self.not_included_words:
                if not class_instance in self.frequency:
                    self.frequency[class_instance] = 0
                self.frequency[class_instance] += 1

        length_of_frequency = len(self.frequency)

        sorted_by_value = dict(
            sorted(self.frequency.items(), key=lambda x: x[1], reverse=True))

        for (generated_code_word, key) in zip(itertools.islice(self.iter_all_strings(), length_of_frequency), sorted_by_value.keys()):
            sorted_by_value[key] = generated_code_word

        sorted_by_key_length = dict(
            sorted(sorted_by_value.items(), key=lambda x: len(x[0]), reverse=True))

        with open('data.json', 'w') as outfile:
            json.dump(sorted_by_key_length, outfile,
                      indent=4, separators=(',', ':'))

        print('created a data.json file!')

    def _get_dest_path(self, path):
        if hasattr(self, "hashed_name"):
            return self.hashed_name(path)

        return path

    def _is_file_allowed(self, file):
        for extension in self.allowed_extensions:
            if file.endswith("." + extension):
                return True
        return False
    
    def iter_all_strings(self):
        for size in itertools.count(start=1):
            for s in itertools.product(ascii_lowercase, repeat=size):
                yield "".join(s)
