import codecs
import json
from string import ascii_lowercase
import itertools
import string
import re
import os
from os.path import getatime, getctime, getmtime
import errno
from collections import OrderedDict

from django.core.exceptions import ImproperlyConfigured
from django.core.files.base import ContentFile
from django.contrib.staticfiles.storage import StaticFilesStorage

from static_compressor import compressors

from yaspin import yaspin

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
        self.exclude_svg_files = getattr(
            settings, "EXCLUDE_STATIC_SVG_FILES", [])

        if not len(self.exclude_js_files) == 0:
            for js_file in self.exclude_js_files:
                if not js_file.endswith('.js'):
                    raise Exception('NOT A VALID JS FILE')

        if not len(self.exclude_css_files) == 0:
            for css_file in self.exclude_css_files:
                if not css_file.endswith('.css'):
                    raise Exception('NOT A VALID CSS FILE')

        if not len(self.exclude_svg_files) == 0:
            for svg_file in self.exclude_svg_files:
                if not svg_file.endswith('.svg'):
                    raise Exception('NOT A VALID SVG FILE')

        self.exclude_static_directory = getattr(
            settings, "EXCLUDE_STATIC_DIRECTORY", [])

        self.json_file_name = getattr(
            settings, "STATIC_CLASSES_FILE_NAME", 'data.json')

        self.css_quoted_salt = '1234567890!@#$%^&*-+_|abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'

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

    def create_dictionary_of_selectors(self, selector_collection):
        dictionary = dict()

        for instance in selector_collection:
            x = instance

            for (key, value) in self.data.items():
                instance = re.sub(r'\.{key}'.format(
                    key=re.escape(key)), '.{value}'.format(value=re.escape(value)), instance)
                dictionary[x] = instance

        return dictionary

    def create_dictionary_of_non_dot_selector(self, selector_collection):
        dictionary = dict()

        for instance in selector_collection:
            x = instance

            for (key, value) in self.data.items():
                instance = re.sub(r'{key}'.format(
                    key=re.escape(key)), '{value}'.format(value=re.escape(value)), instance)
                dictionary[x] = instance

        return dictionary

    def iter_all_strings(self):
        for size in itertools.count(start=1):
            for s in itertools.product(self.css_quoted_salt, repeat=size):
                yield "".join(s)

    def _minify(self, file, destination, original_file):
        if destination.endswith('.css') or original_file.endswith('.css') and original_file not in self.exclude_css_files:
            read_css_file = file.read().decode('utf-8')

            if self.exists(destination):
                file.close()
                self.delete(destination)
                self.delete(original_file)

            # To remove stream of comments
            read_css_file = re.sub(re.compile(
                "/\*.*?\*/", re.DOTALL), '', read_css_file)

            quoted = dict()

            quotes_regex = re.compile(
                r'[\'\"].*?[\'\"]')
            quoted_texts = quotes_regex.findall(
                read_css_file)

            for instance in quoted_texts:
                if not instance in quoted:
                    quoted[instance] = 0
                quoted[instance] += 1

            for (generated_code_word, key) in zip(itertools.islice(self.iter_all_strings(), len(quoted)), quoted.keys()):
                quoted[key] = generated_code_word
                read_css_file = re.sub(r'{sentence}'.format(
                    sentence=key), '"' + generated_code_word + '"', read_css_file)

            sorted_quoted = OrderedDict(
                sorted(quoted.items(), key=lambda x: len(x[0]), reverse=True))

            for (key, value) in self.data.items():
                read_css_file = re.sub(r'\.{key}'.format(
                    key=re.escape(key)), '.{value}'.format(value=re.escape(value)), read_css_file)

            for (key, value) in sorted_quoted.items():
                read_css_file = re.sub(r'[\'\"]{value}[\'\"]'.format(
                    value=re.escape(value)), '{key}'.format(key=key), read_css_file)

            content_file = ContentFile(read_css_file.encode())
            self._save(original_file, content_file)
            new_file = self._save(destination, content_file)
            return new_file

        elif destination.endswith('.js') or original_file.endswith('.js') and original_file not in self.exclude_js_files:
            read_js_file = file.read().decode('utf-8')

            if self.exists(destination):
                file.close()
                self.delete(destination)
                self.delete(original_file)

            html_class_regex = re.compile(r'class[ \t]*=[ \t]*"[^"]+"')
            all_class_attributes = html_class_regex.findall(
                read_js_file)

            for class_attribute in all_class_attributes:
                minified_classes_in_attribute = [
                    self.data[class_name] if class_name in self.data else class_name for class_name in class_attribute[7:-1].split()]
                new_attribute = 'class="' + \
                    ' '.join(minified_classes_in_attribute) + '"'
                read_js_file = re.sub(
                    class_attribute, new_attribute, read_js_file)

            get_selector_regex = re.compile(
                r'querySelector\([\'\"][^\'\"]*?\.[^\'\"]*?[\'\"]\)')

            selector_collection = get_selector_regex.findall(
                read_js_file)

            querySelector = self.create_dictionary_of_selectors(selector_collection)

            for (key, value) in querySelector.items():
                read_js_file = re.sub(
                    re.escape(key), value, read_js_file)

            get_selector_all_regex = re.compile(
                r'querySelectorAll\([\'\"][^\'\"]*?\.[^\'\"]*?[\'\"]\)')
            selector_all_collection = get_selector_all_regex.findall(
                read_js_file)

            querySelector_all = self.create_dictionary_of_selectors(selector_all_collection)

            for (key, value) in querySelector_all.items():
                read_js_file = re.sub(
                    re.escape(key), value, read_js_file)

            get_element_by_classname_regex = re.compile(
                r'getElementsByClassName\([\'\"][^\'\"]*?[^\'\"]*?[\'\"]\)')
            class_collection = get_element_by_classname_regex.findall(
                read_js_file)

            get_elements_by_classes = self.create_dictionary_of_non_dot_selector(class_collection)

            for (key, value) in get_elements_by_classes.items():
                read_js_file = re.sub(
                    re.escape(key), value, read_js_file)

            class_list_add_elements_regex = re.compile(
                r'classList.add\([\'\"][^\'\"]*?[^\'\"]*?[\'\"]\)')
            class_list_contains_elements_regex = re.compile(
                r'classList.contains\([\'\"][^\'\"]*?[^\'\"]*?[\'\"]\)')
            class_list_remove_elements_regex = re.compile(
                r'classList.remove\([\'\"][^\'\"]*?[^\'\"]*?[\'\"]\)')
            class_list_toggle_elements_regex = re.compile(
                r'classList.toggle\([\'\"][^\'\"]*?[^\'\"]*?[\'\"]\)')

            class_list_add_collection = class_list_add_elements_regex.findall(
                read_js_file)
            class_list_remove_collection = class_list_remove_elements_regex.findall(
                read_js_file)
            class_list_contains_collection = class_list_contains_elements_regex.findall(
                read_js_file)
            class_list_toggle_collection = class_list_toggle_elements_regex.findall(
                read_js_file)

            classlist_add = self.create_dictionary_of_non_dot_selector(class_list_add_collection)
            classlist_remove = self.create_dictionary_of_non_dot_selector(class_list_remove_collection)
            classlist_contains = self.create_dictionary_of_non_dot_selector(class_list_contains_collection)
            classlist_toggle = self.create_dictionary_of_non_dot_selector(class_list_toggle_collection)

            for (key, value) in classlist_add.items():
                read_js_file = re.sub(
                    re.escape(key), value, read_js_file)

            for (key, value) in classlist_remove.items():
                read_js_file = re.sub(
                    re.escape(key), value, read_js_file)

            for (key, value) in classlist_contains.items():
                read_js_file = re.sub(
                    re.escape(key), value, read_js_file)

            for (key, value) in classlist_toggle.items():
                read_js_file = re.sub(
                    re.escape(key), value, read_js_file)

            content_file = ContentFile(read_js_file.encode())
            self._save(original_file, content_file)
            new_file = self._save(destination, content_file)

            return new_file

        elif destination.endswith('.svg') or original_file.endswith('.svg') and original_file not in self.exclude_svg_files:
            read_svg_file = file.read().decode('utf-8')

            if self.exists(destination):
                file.close()
                self.delete(destination)
                self.delete(original_file)

            regex = re.compile(r'class[ \t]*=[ \t]*"[^"]+"')

            all_class_attributes = regex.findall(read_svg_file)

            for class_attribute in all_class_attributes:
                minified_classes_in_attribute = [
                    self.data[class_name] if class_name in self.data else class_name for class_name in class_attribute[7:-1].split()]
                new_attribute = 'class="' + \
                    ' '.join(minified_classes_in_attribute) + '"'
                read_svg_file = re.sub(
                    class_attribute, new_attribute, read_svg_file)

            
            for (key, value) in self.data.items():
                read_svg_file = re.sub(r'\.{key}'.format(
                    key=re.escape(key)), '.{value}'.format(value=re.escape(value)), read_svg_file)
            
            content_file = ContentFile(read_svg_file.encode())
            self._save(original_file, content_file)
            new_file = self._save(destination, content_file)

            return new_file
        else:
            return destination

    def post_process(self, paths, dry_run=False, **options):
       
        if hasattr(super(), "post_process"):
            yield from super().post_process(paths, dry_run, **options)

        if dry_run:
            return

        with yaspin(text="Collecting all static files", color="cyan") as sp:

            all_directories = set()
        
            with open(self.json_file_name) as f:
                self.data = json.load(f, object_pairs_hook=OrderedDict)

                for name in paths.keys():

                    source_storage, path = paths[name]
                    
                    dest_path = self._get_dest_path(path)
                    with self._open(dest_path) as file:
                        new_file = file
                        current_directory = path.split('\\')[0]
                    
                        if current_directory != 'admin' and current_directory not in self.exclude_static_directory:
                            
                            new_path = self._minify(file, dest_path, name)
                            new_file = self._open(new_path)

                        if current_directory not in all_directories:
                            sp.write('> {directory_name} is compressing...'.format(
                                directory_name=current_directory))
                            all_directories.add(current_directory)

                        if not self._is_file_allowed(name):
                            continue

                        # Process if file is big enough
                        if os.path.getsize(self.path(path)) < self.minimum_kb * 1024:
                            continue

                        src_mtime = source_storage.get_modified_time(path)
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
                            out = compressor.compress(path, new_file)

                            if out:
                                self._save(dest_compressor_path, out)
                                if not self.keep_original:
                                    self.delete(name)
                                yield dest_path, dest_compressor_path, True

                            new_file.seek(0)

            sp.ok("✔")

    def _get_dest_path(self, path):
        if hasattr(self, "hashed_name"):
            return self.hashed_name(path)

        return path

    def _is_file_allowed(self, file):
        for extension in self.allowed_extensions:
            if file.endswith("." + extension):
                return True
        return False
