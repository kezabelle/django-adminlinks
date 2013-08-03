Crafting a release
==================

* Using `git extras`_, run ``git changelog CHANGELOG``

  * Tidy up the changelog output from now until previous tag.
  * Set the version string to be the current one ...

* ``python setup.py clean``
* Test ``python setup.py sdist``
* Test ``python setup.py bdist_wheel``
* Make sure ``python setup.py --long-description | rst2html.py --halt=3 > /dev/null``
  works ok.
* run bumpversion major/minor/patch

  * Check the tag and commit.

* Push to ``origin`` (GitHub)
* In future, create PyPI releases (see `here`_)

  * ``python setup.py sdist upload -r pypi``
  * ``python setup.py bdist_wheel upload -r pypi``

.. _git extras: https://github.com/visionmedia/git-extras`
.. _here: http://hynek.me/articles/sharing-your-labor-of-love-pypi-quick-and-dirty/
