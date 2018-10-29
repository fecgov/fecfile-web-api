# NXG-FEC-Backend

## Installation

*NOTE: Requires [virtualenv](http://virtualenv.readthedocs.org/en/latest/),
[virtualenvwrapper](http://virtualenvwrapper.readthedocs.org/en/latest/) and
[Node.js](http://nodejs.org/).*
- Also requires Python version 3.5.0.  You can run multiple versions of Python with Pyenv.
  [https://amaral.northwestern.edu/resources/guides/pyenv-tutorial](https://amaral.northwestern.edu/resources/guides/pyenv-tutorial)

* Fork this repository.
* `$ git clone git@github.com:/SalientCRGT-FEC/nxg-fec-back.git`
* `$ mkvirtualenv nxg-fec-back-venv`
* `$ cd nxg-fec-back`
* `$ pip install -r requirements.txt`
* `$ npm install -g bower`
* `$ npm install`
* `$ bower install`
* `$ python manage.py migrate`
* `$ python manage.py loaddata fixtures/base_data`
* `$ python manage.py loaddata fixtures/committee_base_data`
* `$ python manage.py runserver 0.0.0.0:8080`

