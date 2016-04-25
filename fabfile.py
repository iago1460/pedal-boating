from fabric.api import env, local

env.python = 'python2.7'


def quickstart():
    local('python manage.py migrate')
    local('python manage.py create_example_data')
    local('python manage.py runserver')
