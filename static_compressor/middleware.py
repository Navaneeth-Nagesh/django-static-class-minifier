import re
from django.template.response import TemplateResponse
from django.http import HttpResponse
import json
from django.conf import settings

class MinifyClassMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

        self.not_allowed_url_minification = getattr(
            settings, "EXCLUDE_URL_MINIFICATION", [])

        self.should_minify = getattr(
            settings, "MINIFY_CLASS_HTML", False)

        self.json_file_name = getattr(
            settings, "STATIC_CLASSES_FILE_NAME", 'data.json')

        self.inline_style = getattr(
            settings, "STATIC_INLINE_CSS", False)

        if self.should_minify:
            try:
                with open(self.json_file_name) as f:
                    self.data = json.load(f)
            except:
                print('{file_name} file is not found'.format(
                    file_name=self.json_file_name))

    def __call__(self, request):
        response = self.get_response(request)
        content = response.content.decode('utf-8')

        def process_request(self, request):
            pass

        if request.path.endswith('js') or request.path.endswith('json') or request.path.endswith('css'):
            return response

        if not request.get_full_path().startswith('/admin') and not request.get_full_path() in self.not_allowed_url_minification and self.should_minify:
            class_regex = re.compile(r'class[ \t]*=[ \t]*"[^"]+"')
            all_class_attributes = class_regex.findall(content)

            if self.inline_style:
                style_regex = re.compile(r'<style(.*?)</style>')
                all_inline_styles = style_regex.findall(content)

                for inline_style in all_inline_styles:
                    original_style = inline_style

                    for (key, value) in self.data.items():
                        inline_style = re.sub(r'\.{key}'.format(
                            key=re.escape(key)), '.{value}'.format(value=value), inline_style)

                    content = re.sub(r'{key}'.format(
                        key=re.escape(original_style)), inline_style, content)

            for class_attribute in all_class_attributes:
                minified_classes_in_attribute = [
                    self.data[class_name] if class_name in self.data else class_name for class_name in class_attribute[7:-1].split()]
                new_attribute = 'class="' + \
                    ' '.join(minified_classes_in_attribute) + '"'
                content = re.sub(class_attribute, new_attribute, content)

            new_response = HttpResponse(content.encode())
            new_response['Content-Length'] = str(len(new_response.content))
            return new_response

        return response
