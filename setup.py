import os
from distutils.core import setup
from adminlinks import __version__

setup(
    name='django-adminlinks',
    version=__version__,
    description='Django templatetags for rendering links to the administration.',
    author='Keryn Knight',
    author_email='github@kerynknight.com',
    license = "BSD License",
    keywords = "django",
    long_description=open(os.path.join(os.path.dirname(__file__), 'README')).read(),
    url='https://github.com/kezabelle/django-adminlinks',
    packages=['adminlinks', 'adminlinks/templatetags'],
    install_requires=['django-classy-tags>=0.3.4.1'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Site Management',
        'License :: OSI Approved :: BSD License',
    ],
    platforms=['OS Independent'],
)
