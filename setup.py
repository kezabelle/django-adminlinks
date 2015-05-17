import os
from distutils.core import setup
from setuptools import find_packages

HERE = os.path.abspath(os.path.dirname(__file__))


def make_readme(root_path):
    FILES = ('README.rst', 'LICENSE', 'CHANGELOG', 'CONTRIBUTORS')
    for filename in FILES:
        filepath = os.path.realpath(os.path.join(root_path, filename))
        if os.path.isfile(filepath):
            with open(filepath, mode='r') as f:
                yield f.read()


LONG_DESCRIPTION = "\r\n\r\n----\r\n\r\n".join(make_readme(HERE))


setup(
    name='django-adminlinks',
    version='0.8.2',
    description='Django template tags for rendering links to the '
                'administration.',
    author='Keryn Knight',
    author_email='python-package@kerynknight.com',
    license="BSD License",
    keywords="django",
    long_description=LONG_DESCRIPTION,
    url='https://github.com/kezabelle/django-adminlinks',
    packages=find_packages(exclude=['docs*']),
    install_requires=(
        'Django>=1.4',
        'django-classy-tags>=0.6.1',
    ),
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Natural Language :: English',
        'Topic :: Internet :: WWW/HTTP :: Site Management',
        'Topic :: Text Processing :: Markup :: HTML',
        'License :: OSI Approved :: BSD License',
    ],
    platforms=['OS Independent'],
)
