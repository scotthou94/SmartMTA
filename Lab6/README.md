# Lab 6 Instructions

## Running the Site
* Navigate to the directory: `django_tutorial/mysite`
* To start the server: `python manage.py runserver 0:8080`
* You should see output similar to the following when the server is up:

```
[ec2-user@ip-172-31-28-9 mysite]$ python manage.py runserver 0:8080
Performing system checks...

System check identified no issues (0 silenced).
March 17, 2018 - 16:01:42
Django version 1.11.11, using settings 'mysite.settings'
Starting development server at http://0:8080/
Quit the server with CONTROL-C.
[17/Mar/2018 16:01:50] "GET /lab/ HTTP/1.1" 200 1104
[17/Mar/2018 16:01:55] "POST /lab/show_temp/ HTTP/1.1" 200 603
[17/Mar/2018 16:01:55] "GET /lab/show_map/ HTTP/1.1" 200 11078
[17/Mar/2018 16:02:19] "POST /lab/show_temp/ HTTP/1.1" 200 604
[17/Mar/2018 16:02:19] "GET /lab/show_map/ HTTP/1.1" 200 13945
```

To test, go to http://34.229.14.242:8080/lab to see the interface with two cities. If you get an error about IP addresses, remember to add the IP to the list in `mysite/settings.py` in the list `ALLOWED_HOSTS`.

## Viewing The Database
* Navigate to `django_tutorial/mysite`
* To view the records written to the database, run `sqlite3 db.sqlite3`
* Run the following commands in the SQLite console

```
.mode column
.headers on
select * from lab_city
```