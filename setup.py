import os
from distutils.core import setup
from setuptools import find_packages
from adminlinks import __version__

HERE = os.path.abspath(os.path.dirname(__file__))


def tidy_requirements(requirement_file):
    """
    simplistic parsing of our requirements files to generate dependencies for
    the setup file.
    """
    outdata = []
    with open(requirement_file) as dependencies:
        for line in dependencies:
            line = line.strip()
            # make sure any hard pinned versions are instead treated as loose
            # minimum versions, see
            # http://hynek.me/articles/sharing-your-labor-of-love-pypi-quick-and-dirty/
            line = line.replace('==', '>=')
            if line and not line.startswith('#') and line not in outdata:
                outdata.append(line)
    return outdata

setup(
    name='django-adminlinks',
    version=__version__,
    description='Django template tags for rendering links to the '
                'administration.',
    author='Keryn Knight',
    author_email='github@kerynknight.com',
    license="BSD License",
    keywords="django",
    long_description=open(os.path.join(HERE, 'README')).read(),
    url='https://github.com/kezabelle/django-adminlinks',
    packages=find_packages(exclude=['docs*']),
    install_requires=tidy_requirements(os.path.join(HERE, 'adminlinks',
                                                    'requirements.txt')),
    include_package_data=True,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Natural Language :: English',
        'Topic :: Internet :: WWW/HTTP :: Site Management',
        'Topic :: Text Processing :: Markup :: HTML',
        'License :: OSI Approved :: BSD License',
    ],
    platforms=['OS Independent'],
)
