# Develop a safe back-end architecture with Django ORM  - OpenClassrooms project 12

This project is about developing a safe back-end architecture with Django ORM in order to help "Epic Events", a start-up 
organizing parties. A full admin management app and a CRM API are to be developed for creating clients, contracts and events.

## Project structure

The root is composed of :

a requirements.txt file listing all the necessary packages for this project

a .gitignore file

a log folder with an errors.log file for error loggings.

a src folder containing:

- a manage.py which permits a command-line utility that works similar to the django-admin command.
- an eventmanager folder with all the applications' settings and urls.
- an authentication app responsible for the definition of users and their authentication.
- a crm_api app responsible for the full API.

## Database

This app works with PostgreSQL as a database.

If you do not have it on your computer, you can follow the process on this link:

```bash
https://www.postgresql.org/download/
```

Once it is installed on your computer, create a new database with the following parameters:

- Database name: event_manager
- Host: 127.0.0.1
- Port: 5432

## Installation

Clone [the repository](https://github.com/Bricevne/P12_epicevents.git) on your computer.

```
git clone https://github.com/Bricevne/P12_epicevents.git
```

Get into the root directory P12_epicevents/

Set your virtual environment under [python 3.10](https://www.python.org/downloads/release/python-3100/)

```bash
pipenv install # Install pipenv
pipenv shell # Activate the virtual environment
pip install -r requirements.txt # Install the dependencies
```

Create a file where you'll put the django secret key:

```bash
touch .env # File for environment variables
```

Insert your django secret key in the .env file

```bash
DJANGO_SECRET_KEY="DJANGO_SECRET_KEY"
```

Export your postgresql app path in order to access the postgresql server.

```bash
export PATH="/Applications/Postgres.app/Contents/Versions/latest/bin:$PATH"
```

You can then make the migrations:

```bash
python manage.py migrate
```

## Launch the local server

In the src folder run the following code to access the web application:

```bash
python manage.py runserver # Start the local server
```

You can now open your navigator with the URL 'http://127.0.0.1:5000/admin' to access the administration.

## Use Postman to test the API's endpoints

This API is documented with Postman.

### Postman installation

You can install Postman by following the instructions from the following url:

```bash
https://www.postman.com/downloads/"
```

### Authentication

The /login endpoints do not need an authentication token to access.

All the other endpoints are only accessible by an authenticated user after generation of a simple JWT access token. 
Moreover, a user has access to different endpoints depending on their permission.

### Permissions

Permissions for this app are separated in 3 groups:
- Sales: Can create new clients and contracts, and can update the ones they are responsible for. Can also create new events.
- Support: Can update events they are responsible for, and vew information about the corresponding clients.
- Management: Can create new users and can view and update all users, clients, contracts and events.

### Structure

Nested routers are used to access the urls.

Here are the available urls:

- /users : List of users
- /users/:user_id : Detail of a user
- /clients : List of clients
- /clients/:client_id : Detail of a client
- /clients/:client_id/contracts : List of contracts of a client
- /clients/:client_id/contracts/:contract_id : Detail of a contract of a client
- /clients/:client_id/events : List of events of  client
- /clients/:client_id/events/:event_id : Detail of an event of a client

### Collection test

You can access this API's collections by importing data (File -> Import -> Link) with the following link:

```bash
https://documenter.getpostman.com/view/18689622/2s8ZDeUeR7
```

This collection is divided into several folders:

- "Authentication": /login endpoints which do not need an access token.
- "Clients": /clients endpoints. Needs an access token.
- "Users": /users endpoints. Needs an access token.
- "Contracts": /contracts endpoints. Needs an access token.
- "Events": /events endpoints. Needs an access token.

For ease of use, this API collection automatically add the JWT access token to environment variables after logging with an account. 
This variable is thus inherited by the Clients, Users, Contracts and Events folders.

## License

[MIT](https://choosealicense.com/licenses/mit/)