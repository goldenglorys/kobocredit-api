# Kobolend API
## Description
Api code for Kobolend App

## Technologies
- Django >= 2.1
- Django Rest Framework
- Djoser (Note: Djoser requires Django 3.7-3.8.0 to work efficiently)
- Postgresql

## Setup Instructions
1. You need to have pipenv installed to continue with this. Pipenv can be installed with 
`pip install pipenv`

2. Fork this repository to your main account and clone from there, move into it and install necessary dependencies using 
`pipenv install`

3. Create your environment variables file with `cat .env.example > .env` and update the necessary variables
   
4. Create a postgres database and fill in the credentials (db_name, db_user, db_password) in the .env file.

5. It is preferable to be in pipenv shell when executing commands
`pipenv shell`

6. Update your db with created migrations using `python manage.py migrate`

7. The platform has 4 major types of users (or user roles) => ["superuser", "manager", "society_manager", "secretary", "member"]. Create these roles using groups in shell
```
  python manage.py shell
  >>> from django.contrib.auth.models import Group
  >>> Group.objects.create(name='superuser')
  >>> Group.objects.create(name='manager')
  >>> Group.objects.create(name='secretary')
  >>> Group.objects.create(name='member')

```
  <!-- >>> Group.objects.bulk_create([Group(name='superuser'), Group(name='manager'), Group(name='secretary'), Group(name='member')]  -->

8. Create a super user `python manage.py createsuperuser`

<!-- 9. Populate db with random users by running the command
   `python manage.py gen_fake_data` -->

9. Startup the server with `python manage.py runserver`

10. Access admin at `/admin`

11. Login with the superuser account created, create `Savings & Loan Accounts` in the account model, create an an `HQ`, and create users as much as you wanted according to their role