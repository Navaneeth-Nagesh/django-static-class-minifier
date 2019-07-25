from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings

import codecs
import json
from string import ascii_lowercase
import itertools
import string
import re
import os

class Command(BaseCommand):
    help = 'minify all classes'

    def handle(self, *args, **kwargs):

        self.json_file_name = getattr(
            settings, "STATIC_CLASSES_FILE_NAME", 'data.json')

        try:
            with open(self.json_file_name) as f:
                data = json.load(f)
        except:
            print('{file_name} file is not found'.format(
                file_name=self.json_file_name))

        self.static_root = getattr(
            settings, "STATIC_ROOT", ".")

        self.not_included_words = ['ttf', 'woff2', 'www', 'woff', 'js', 'otf', 'eot', 'svg', 'com', 'in', 'css', 'add', 'contains', 'remove', 'toggle', 'move']

        for root, dirs, files in os.walk(self.static_root):
            # remove admin files
            for file in files:
                if file.endswith('.css'):
                    read_css_file = open(os.path.join(root, file)).read()
                    
                    # To remove stream of comments
                    read_css_file = re.sub(re.compile(
                        "/\*.*?\*/", re.DOTALL), '', read_css_file)

                    for (key, value) in data.items():
                        read_css_file = re.sub(r'\.{key}'.format(
                            key=re.escape(key)), '.{value}'.format(value=re.escape(value)), read_css_file)

                    write_css_file = open(os.path.join(root, file), 'w')
                    write_css_file.write(read_css_file)
                    write_css_file.close()

                if file.endswith('.js'):
                    read_js_file = codecs.open(os.path.join(root, file), 'r','utf-8').read()

                    html_class_regex = re.compile(r'class[ \t]*=[ \t]*"[^"]+"')
                    all_class_attributes = html_class_regex.findall(
                        read_js_file)

                    for class_attribute in all_class_attributes:
                        minified_classes_in_attribute = [
                            data[class_name] if class_name in data else class_name for class_name in class_attribute[7:-1].split()]
                        new_attribute = 'class="' + \
                            ' '.join(minified_classes_in_attribute) + '"'
                        read_js_file = re.sub(
                            class_attribute, new_attribute, read_js_file)
                    
                    get_selector_regex = re.compile(
                        r'querySelector\([\'\"][^\'\"]*?\.[^\'\"]*?[\'\"]\)')

                    selector_collection = get_selector_regex.findall(read_js_file)

                    querySelector = self.create_dictionary_of_selectors(data, selector_collection)

                    for (key, value) in querySelector.items():
                        read_js_file = re.sub(
                            re.escape(key), value, read_js_file)

                    get_selector_all_regex = re.compile(
                        r'querySelectorAll\([\'\"][^\'\"]*?\.[^\'\"]*?[\'\"]\)')
                    selector_all_collection = get_selector_all_regex.findall(
                        read_js_file)

                    querySelector_all = self.create_dictionary_of_selectors(
                        data, selector_all_collection)

                    for (key, value) in querySelector_all.items():
                        read_js_file = re.sub(
                            re.escape(key), value, read_js_file)

                    get_element_by_classname_regex = re.compile(r'getElementsByClassName\([\'\"][^\'\"]*?[^\'\"]*?[\'\"]\)')
                    class_collection = get_element_by_classname_regex.findall(
                        read_js_file)

                    get_elements_by_classes = self.create_dictionary_of_non_dot_selector(
                        data, class_collection)

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

                    class_list_add_collection = class_list_add_elements_regex.findall(read_js_file)
                    class_list_remove_collection = class_list_remove_elements_regex.findall(
                        read_js_file)
                    class_list_contains_collection = class_list_contains_elements_regex.findall(
                        read_js_file)
                    class_list_toggle_collection = class_list_toggle_elements_regex.findall(
                        read_js_file)

                    classlist_add = self.create_dictionary_of_non_dot_selector(data,
                        class_list_add_collection)
                    classlist_remove = self.create_dictionary_of_non_dot_selector(data,
                        class_list_remove_collection)
                    classlist_contains = self.create_dictionary_of_non_dot_selector(data,
                        class_list_contains_collection)
                    classlist_toggle = self.create_dictionary_of_non_dot_selector(data,
                        class_list_toggle_collection)

                    for (key, value) in classlist_add.items():
                        read_js_file = re.sub(re.escape(key), value, read_js_file)

                    for (key, value) in classlist_remove.items():
                        read_js_file = re.sub(re.escape(key), value, read_js_file)

                    for (key, value) in classlist_contains.items():
                        read_js_file = re.sub(re.escape(key), value, read_js_file)

                    for (key, value) in classlist_toggle.items():
                        read_js_file = re.sub(re.escape(key), value, read_js_file)

                    write_js_file = codecs.open(os.path.join(root, file), 'w', 'utf-8')
                    write_js_file.write(read_js_file)
                    write_js_file.close()

                if file.endswith('.svg'):
                    read_svg_file = codecs.open(
                        os.path.join(root, file), 'r', 'utf-8').read()

                    regex = re.compile(r'class[ \t]*=[ \t]*"[^"]+"')

                    all_class_attributes = regex.findall(read_svg_file)

                    for class_attribute in all_class_attributes:
                        minified_classes_in_attribute = [
                            data[class_name] if class_name in data else class_name for class_name in class_attribute[7:-1].split()]
                        new_attribute = 'class="' + \
                            ' '.join(minified_classes_in_attribute) + '"'
                        read_svg_file = re.sub(
                            class_attribute, new_attribute, read_svg_file)

                    
                    for (key, value) in data.items():
                        read_svg_file = re.sub(r'\.{key}'.format(
                            key=re.escape(key)), '.{value}'.format(value=re.escape(value)), read_svg_file)
                    
                    write_svg_file = codecs.open(
                        os.path.join(root, file), 'w', 'utf-8')
                    write_svg_file.write(read_svg_file)
                    write_svg_file.close()

        print('compiled!')
    def create_dictionary_of_selectors(self, data, selector_collection):
        dictionary = dict()

        for instance in selector_collection:
            x = instance

            for (key, value) in data.items():
                instance = re.sub(r'\.{key}'.format(
                    key=re.escape(key)), '.{value}'.format(value=re.escape(value)), instance)
                dictionary[x] = instance

        return dictionary


    def create_dictionary_of_non_dot_selector(self, data, selector_collection):
        dictionary = dict()

        for instance in selector_collection:
            x = instance

            for (key, value) in data.items():
                instance = re.sub(r'{key}'.format(
                    key=re.escape(key)), '{value}'.format(value=re.escape(value)), instance)
                dictionary[x] = instance

        return dictionary
