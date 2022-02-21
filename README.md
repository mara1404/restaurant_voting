# Restaurant voting

## Launching project

##### Environment and pip packages
```commandline
virtualenv --python=python3 venv
source venv/bin/activate
pip3 install -r requirements.list
```

##### local.py file
Change `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `DATABASES` values as needed
```commandline
cp examples/local.py.example restaurant_voting/settings/local.py
```

##### Migrations
```commandline
python manage.py migrate
```

##### Tests
```commandline
python manage.py test
```

##### Running server
```commandline
python manage.py runserver
```

## API usage

User daily vote count saved in User model.  

All views require user to be authenticated. Easiest way is to create Django superuser and login through Django admin page

restaurant list and restaurant history views ordered by biggest rating and most distinct users, so winner restaurant is first element in lists

/restaurant/create/ - create restaurant. POST data: {'title': 'x', 'address': 'x'}  
/restaurant/list/ - list of restaurants with ratings and current user vote information  
/restaurant/history/ - list of restaurants history. Query param filters:
- date_after - date
- date_before - date
- restaurants (multiple) - restaurant id

/restaurant/winners_history/ - list of winner restaurants. Query param filters:
- date_after - date
- date_before - date
- restaurants (multiple) - restaurant id

/restaurant/<restaurant_id>/update/ - update restaurant. POST data: {'title': 'x', 'address': 'x'}  
/restaurant/<restaurant_id>/delete/ - delete restaurant  
/restaurant/<restaurant_id>/vote/ - vote for restaurant
