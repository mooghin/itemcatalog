from flask import Flask, render_template, request, redirect, jsonify, url_for, g
app = Flask(__name__)

# Note: This would be removed in production.
# This 'secret' key is only available here for testing purposes.
app.secret_key = 'super secret key'

from sqlalchemy import create_engine, asc, desc
from sqlalchemy.orm import sessionmaker
from models import Base, User, Category, Item

from flask import session as login_session
import random, string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import OAuth2Credentials
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

from flask_httpauth import HTTPBasicAuth

engine = create_engine('sqlite:///itemcatalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']

auth = HTTPBasicAuth()

# Verify users of the API endpoints based on the access token they got from
# localhost:5000/api/request_token
@auth.verify_password
def verify_password(username_or_token, password):
    # First parameter could be used to store a username or an auth token
    # This app will only consider auth tokens without password_hash
    user_id = User.verify_auth_token(username_or_token)
    if user_id:
        user = session.query(User).filter_by(id = user_id).one()
    else:
        # Currently our database only supports authentication with OAuth
        # If we couldn't verify the token, we can't verify this user
        return False

    g.user = user
    return True

# Starts the token request process for folks who want to access
# the Item Catalog through API endpoints.
@app.route('/api/request_token')
def requestAPIToken():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(32))
    login_session['state'] = state
    return render_template('getAPIKey.html', STATE=state)

# Called after successful authorization with Google,
# this generates a token to access the Item Catalog through API endpoints.
# The token is not related to the tokens/codes sent during the OAuth process.
@app.route('/api/make_token', methods=['POST'])
def makeAPIToken():
    # Make sure this request has the state token issued by the server
    # when the user originally visited /login
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    code = request.data

    # BELOW THIS LINE - copied from gconnect - verifies one-time code from Google
    # before issuing our own unique token for API access
    try:
        # Upgrade the one-time code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])

    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 501)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is meant for the intended user.
    # (i.e., the googleapis server returned an id different from the
    # one we got from the flow_from_clientsecrets object when upgrading.)
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app
    # (i.e., the googleapis server returned a client id different from
    # the one that this server knows we should use, from client_secrets.json)
    if result['issued_to'] != CLIENT_ID:
        response = make_response(json.dumps("Token's client ID does not match app's."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # ABOVE THIS LINE: COPIED FROM gconnect - verifying one-time code obtained by client
    # before issuing our own unique token

    # Get the user's information from Google
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)
    data = answer.json()

    # If this user has never requested access before, record them in our database
    user = session.query(User).filter_by(email=data['email']).first()
    if not user:
        user = User(username = data['name'], picture = data['picture'], email = data['email'])
        session.add(user)
        session.commit()

    # Generate our own token that this user can use for the next 10 minutes
    # to make calls to the Item Catalog API endpoints
    token = user.generate_auth_token(600)
    return token.decode('ascii')

# Login page - start the OAuth authorization process
# This creates a state token when the user wants to start login,
# which will be verified during the gconnect callback later
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)

# Gets called from /login when a user successfully authenticates
# with Google and needs to exchange the one-time code received for
# an access token. We also keep track of the user in Flask's session
# (login_session) here.
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Make sure this request has the state token issued by the server
    # when the user originally visited /login
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    code = request.data
    try:
        # Upgrade the one-time code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])

    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 501)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is meant for the intended user.
    # (i.e., the googleapis server returned an id different from the
    # one we got from the flow_from_clientsecrets object when upgrading.)
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app
    # (i.e., the googleapis server returned a client id different from
    # the one that this server knows we should use, from client_secrets.json)
    if result['issued_to'] != CLIENT_ID:
        response = make_response(json.dumps("Token's client ID does not match app's."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # If the user is already logged in, return a success without
    # updating all the flask session's variables
    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # At this point, we are handling a correctly authorized user who isn't
    # already logged in. We want to store their credentials for later use.
    login_session['credentials'] = credentials.to_json()
    login_session['gplus_id'] = gplus_id

    # Get the user's information from Google
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)
    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # If user doesn't exist yet in our database, make a record of them
    user = session.query(User).filter_by(email=data['email']).first()
    if not user:
        user = User(username = data['name'], picture = data['picture'], email = data['email'])
        session.add(user)
        session.commit()

    # Prepare output to send back to the client's login page
    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    print("Logged in " + login_session['username'] + "(" + login_session['email'] + ").")
    return output

# DISCONNECT - Revoke a current user's token and reset their login_session.
@app.route('/gdisconnect')
def gdisconnect():
    # Don't need to disconnect if no user is connected
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(json.dumps('Current user is not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Ask Google's API to revoke the user's current token.
    # Since credentials was just stored as a string in login_session, we need to
    # interpret it as a set of OAuth2Credentials from json
    credentials = OAuth2Credentials.from_json(credentials)
    access_token = credentials.access_token
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    # Response code 200: Revoking token was successful. Reset the user's session.
    if result['status'] == '200':
        del login_session['credentials']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        return redirect(url_for('showRecentItems'))

    # Any other response code means the given token was invalid.
    # Since we are disconnecting, it's OK clear the login session anyway.
    else:
        del login_session['credentials']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        return redirect(url_for('showRecentItems'))

# Main page - show all categories and latest items
@app.route('/')
@app.route('/catalog')
def showRecentItems():
    categories = session.query(Category).all()
    topten = session.query(Item).order_by(desc(Item.date_added)).limit(10).all()

    if 'username' not in login_session:
        return render_template('public_catalog.html', categories=categories,
                                topten=topten)
    else:
        return render_template('public_catalog.html', categories=categories,
                                topten=topten, username=login_session['username'])

# Category page - show all items in this category
@app.route('/catalog/<category_name>')
@app.route('/catalog/<category_name>/items')
def showFullCategory(category_name):
    all_categories = session.query(Category).all()
    this_category = session.query(Category).filter_by(name=category_name).one()
    items = session.query(Item).filter_by(category=this_category).all()

    # Show the public template if not logged in
    if 'username' not in login_session:
        return render_template('show_category.html', categories=all_categories,
                                category=this_category, items=items)

    # Show the template with new item capability if logged in
    else:
        return render_template('show_category_protected.html', categories=all_categories,
                                category=this_category, items=items,
                                username=login_session['username'])

# Item page - show the item's name and description
@app.route('/catalog/<category_name>/<item_name>')
def showItem(category_name, item_name):
    all_categories = session.query(Category).all()
    this_category = session.query(Category).filter_by(name=category_name).one()
    item = session.query(Item).filter_by(category=this_category).filter_by(name=item_name).one()

    # Show the public template if not logged in
    if 'username' not in login_session:
        return render_template('show_item.html', categories=all_categories,
                                category=this_category, item=item)

    # Show the template with edit/delete capability if we are logged in.
    else:
        return render_template('show_item_protected.html', categories=all_categories,
                                category=this_category, item=item,
                                username=login_session['username'])

# Item page - show the item's name and description
@app.route('/catalog/<category_name>/new', methods=['GET', 'POST'])
def newItemInCategory(category_name):
    # Can't access this page unless we're logged in
    if 'username' not in login_session:
        return redirect('/login')

    # If we're logged in, handle GET or POST methods correctly.
    if request.method == 'GET':
        all_categories = session.query(Category).all()
        this_category = session.query(Category).filter_by(name=category_name).one()
        return render_template('new_item.html', categories=all_categories,
                                category=this_category, username=login_session['username'])

    elif request.method == 'POST':
        item_name = request.form['name']
        description = request.form['description']
        if not description:
            description = 'no description given'
        new_category_name = request.form['category']
        category = session.query(Category).filter_by(name=new_category_name).one()
        new_item = Item(name=item_name, description=description, category=category)
        session.add(new_item)
        session.commit()
        return redirect(url_for('showFullCategory', category_name=new_category_name))

@app.route('/catalog/new', methods=['GET', 'POST'])
def newItem():
    # Can't access this page unless we're logged in
    if 'username' not in login_session:
        return redirect('/login')

    if request.method == 'GET':
        all_categories = session.query(Category).all()
        return render_template('new_item.html', categories=all_categories,
                                username=login_session['username'])

    elif request.method == 'POST':
        item_name = request.form['name']
        # TODO: Figure out how to make this field required
        description = request.form['description']
        if not description:
            description = 'no description given'
        new_category_name = request.form['category']
        category = session.query(Category).filter_by(name=new_category_name).one()
        new_item = Item(name=item_name, description=description, category=category)
        session.add(new_item)
        session.commit()
        return redirect(url_for('showRecentItems'))


# Edit item page - show a form where the user can edit any details of the item
@app.route('/catalog/<category_name>/<item_name>/edit', methods=['GET', 'POST'])
def editItem(category_name, item_name):
    # Can't access this page unless we're logged in
    if 'username' not in login_session:
        return redirect('/login')

    all_categories = session.query(Category).all()
    this_category = session.query(Category).filter_by(name=category_name).one()
    item = session.query(Item).filter_by(category=this_category).filter_by(name=item_name).one()

    if request.method == 'GET':
        return render_template('edit_item.html', categories=all_categories,
                                category=this_category, item=item, username=login_session['username'])

    elif request.method == 'POST':
        new_name = request.form['name']
        if new_name:
            item_name = new_name
            item.name = new_name
        new_desc = request.form['description']
        if new_desc:
            item.description = new_desc
        new_cat = request.form['category']
        if new_cat:
            category_name = new_cat
            new_category = session.query(Category).filter_by(name=category_name).one()
            item.category = new_category
        session.commit()
        return redirect(url_for('showItem', category_name=category_name, item_name=item_name))


# Delete item page - allow the user to delete this item
@app.route('/catalog/<category_name>/<item_name>/delete', methods=['GET', 'POST'])
def deleteItem(category_name, item_name):
    # Can't access this page unless we're logged in
    if 'username' not in login_session:
        return redirect('/login')

    all_categories = session.query(Category).all()
    this_category = session.query(Category).filter_by(name=category_name).one()
    item = session.query(Item).filter_by(category=this_category).filter_by(name=item_name).one()

    if request.method == 'GET':
        return render_template('delete_item.html', categories=all_categories,
                                category=this_category, item=item,
                                username=login_session['username'])

    elif request.method == 'POST':
        session.delete(item)
        session.commit()
        return redirect(url_for('showFullCategory', category_name=category_name))

# Get the whole catalog from an API call
@app.route('/catalog.json')
def fullCatalogJSON():
    all_categories = session.query(Category).all()
    final_dict = []
    for cat in all_categories:
        cat_items = session.query(Item).filter_by(category=cat).all()
        cat_dict = cat.serialize
        cat_dict['items'] = [i.serialize for i in cat_items]
        final_dict.append(cat_dict)
    return jsonify(final_dict)

# Get one category of the catalog from an API call
@app.route('/catalog/<category_name>.json')
def categoryJSON(category_name):
    category = session.query(Category).filter_by(name=category_name).first()
    if category is not None:
        cat_items = session.query(Item).filter_by(category=category).all()
        cat_dict = category.serialize
        cat_dict['items'] = [i.serialize for i in cat_items]
        return jsonify(cat_dict)
    else:
        return jsonify({'error': 'Category %s does not exist.' % category_name})

# Get one item of the catalog from an API call
@app.route('/catalog/<category_name>/<item_name>.json')
def itemJSON(category_name, item_name):
    category = session.query(Category).filter_by(name=category_name).first()
    if category is None:
        return jsonify({'error': 'Category %s does not exist.' % category_name})

    else:
        item = session.query(Item).filter_by(category=category).filter_by(name=item_name).first()
        if item is None:
            return jsonify({'error': 'Item %s does not exist in category %s.' % (item_name, category_name)})

        else:
            return jsonify(item.serialize)

# Add a new item to the catalog from an API call
@app.route('/api/new_item', methods=['POST'])
@auth.login_required
def apiNewItem():
    category_name = request.args.get('category')
    item_name = request.args.get('name')

    if category_name is None or item_name is None:
        return jsonify({'error': 'Calls to /api/new_item require 2 parameters: category and name.'})

    category = session.query(Category).filter_by(name=category_name).first()

    if category is None:
        return jsonify({'error': 'Cannot add item; Category %s does not exist.' % category_name})

    description = request.args.get('description')
    if description is None:
        description = 'no description given'

    new_item = Item(name=item_name, description=description, category=category)
    session.add(new_item)
    session.commit()
    return jsonify(new_item.serialize)

# Edit an item in the catalog from an API call
@app.route('/api/edit_item', methods=['PUT'])
@auth.login_required
def apiEditItem():
    category_name = request.args.get('category')
    item_name = request.args.get('name')

    if category_name is None or item_name is None:
        return jsonify({'error': 'Calls to /api/edit_item require 2 parameters: category and name.'})

    category = session.query(Category).filter_by(name=category_name).first()

    if category is None:
        return jsonify({'error': 'Cannot edit item; Category %s does not exist.' % category_name})

    item = session.query(Item).filter_by(category=category).filter_by(name=item_name).first()
    if item is None:
        return jsonify({'error': 'Cannot edit item; category %s has no item %s.' % (category_name, item_name)})

    new_name = request.args.get('new_name')
    if new_name is not None:
        item.name = new_name

    new_description = request.args.get('new_description')
    if new_description is not None:
        item.description = new_description

    new_category_name = request.args.get('new_category')
    if new_category_name is not None:
        new_category = session.query(Category).filter_by(name=new_category_name).one()
        if new_category is None:
            return jsonify({'error': 'Cannot edit item; new category %s does not exist.' % new_category_name})
        else:
            item.category = new_category

    session.commit()
    return jsonify(item.serialize)

# Edit an item in the catalog from an API call
@app.route('/api/delete_item', methods=['DELETE'])
@auth.login_required
def apiDeleteItem():
    category_name = request.args.get('category')
    item_name = request.args.get('name')

    if category_name is None or item_name is None:
        return jsonify({'error': 'Calls to /api/delete_item require 2 parameters: category and name.'})

    category = session.query(Category).filter_by(name=category_name).first()

    if category is None:
        return jsonify({'error': 'Cannot delete item; Category %s does not exist.' % category_name})

    item = session.query(Item).filter_by(category=category).filter_by(name=item_name).first()
    if item is None:
        return jsonify({'error': 'Cannot delete item; category %s has no item %s.' % (category_name, item_name)})

    session.delete(item)
    return jsonify({'success': 'Deleted item %s from category %s.' % (item_name, category_name)})

if __name__ == "__main__":
    app.secret_key = 'super secret key'
    app.debug = True
    app.run(host = '0.0.0.0', port = 5000)
