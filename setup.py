from setuptools import find_packages, setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="django-static-class-minifier",
    version="0.1.9",
    url="https://github.com/Navaneeth-Nagesh/django-static-class-minifier",
    author="Navaneeth Nagesh",
    author_email="navaneethnagesh56@gmail.com",
    description="Precompress Django static files with class names shortening.",
    license="MIT",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(exclude=["tests"]),
    keywords="Django, class-minifier, compressor, pre-processor",
    include_package_data=True,
    install_requires=["Django", "Brotli~=1.0.4", "zopfli~=0.1.4", "yaspin~=0.14.3"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Software Development :: Pre-processors",
    ],
)
