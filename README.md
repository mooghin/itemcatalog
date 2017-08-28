# itemcatalog
Item Catalog project for Udacity Full Stack Nanodegree

Author: Megan Elmore

## Requirements

This project can be run in the [Udacity Fullstack Nanodegree VM](https://github.com/udacity/fullstack-nanodegree-vm).

All files in my itemcatalog repository should be copied into /vagrant/catalog.

## Setup

1. cd into the /vagrant directory in your local copy of the [Udacity Fullstack Nanodegree VM](https://github.com/udacity/fullstack-nanodegree-vm) repo.
2. Start the virtual machine: `vagrant up`
3. ssh into the virtual machine: `vagrant ssh`
4. Inside the virtual machine, get into the shared directory with the project files: `cd /vagrant/catalog`
5. Populate the database with some items to test: `python catalog_init.py`
6. Set up Flask to run the project: `export FLASK_APP=views.py`
7. Run the project: `flask run`.
8. Visit http://localhost:5000 or http://localhost:5000/catalog in your browser to see the front page of ItemCatalog.

## Authentication

This project uses OAuth with Google Accounts to authenticate users.

There is a log in button at the top right of the navigation bar that will start the authentication flow. Follow the instructions on screen, and when you are authenticated you will be redirected to the main page.

When you are not logged in, you can only view the catalog.

When you are logged in, you can add new items from any page; add new items to a category. You can log out by clicking the button at the top right of the navigation bar.

## Authorization for editing and deleting items

Authenticated users can also edit and delete items, but only those items which they created. They will not be shown the option to edit or delete an item they do not own, and edit/delete operations will only proceed once authorization is verified.

## API endpoints
http://localhost:5000/catalog.json returns the whole catalog in JSON format.
http://localhost:5000/catalog/Hiking.json returns only the items in the Hiking category in JSON format.
http://localhost:5000/catalog/Hiking/daypack.json returns only the daypack item from the Hiking category in JSON format.

API users can also create if they have an access token.
API users can edit and delete item if their access token identifies them
as the owner of the object.

Go to http://localhost:5000/api/request_token to get a token.

This app uses OAuth to authenticate a user once with their Google account, and then the server generates its own unique token. The user can then make API requests by authenticating with this token as their "username".

For example, in Postman, you can use the following HTTP requests with the authorization type "Basic Auth" and give the token as the username. Leave the password blank.

**To create a new item:**

POST http://localhost:5000/api/new_item?category=Camping&name=alite%20chair&description=easy%20to%20set%20up

Required parameters: category, name
Optional parameters: description

**To edit an existing item:**

PUT http://localhost:5000/api/edit_item?category=Camping&name=alite%20chair&new_name=mantis%chair&new_description=so%20comfortable

Required parameters: category, name
Optional parameters: new_name, new_description, new_category

**To delete an existing item:**

DELETE http://localhost:5000/api/delete_item?category=Hiking&name=daypack

Required parameters: category, name

## Resources

I based much of the code structure, especially the OAuth functionality, on my solutions and the instructor code provided with the Udacity classes Full Stack Fundamentals, Authentication and Authorization: OAuth, and Designing RESTful APIs.

I styled my app using Bootstrap and drew examples from their [public documentation](https://getbootstrap.com/docs/4.0/getting-started/introduction/).
