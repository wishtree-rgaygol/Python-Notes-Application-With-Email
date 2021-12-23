import os
from functools import wraps
from flask import Flask, redirect, url_for, request, session, make_response
from flask_dance.contrib.google import make_google_blueprint, google


class DanceGoogleAuth:
    def __init__(self, app=None, return_endpoint='index'):
        self.app = app
        os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = 'True'

        # define a default login_handler
        def func(email, name):
            session['user_email'] = email
            session['user_name'] = name
            return True
        self.login_handler = func

        # init app if given
        if app is not None:
            self.init_app(app, return_endpoint)

    def init_app(self, app, return_endpoint='index'):
        self.app = app

        # read google OAuth credential
        app.config["GOOGLE_OAUTH_CLIENT_ID"] = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
        app.config["GOOGLE_OAUTH_CLIENT_SECRET"] = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")

        # create a blueprint
        google_bp = make_google_blueprint(scope=["profile", "email"], redirect_to='google.verify')

        # define a verifiy route to receive google account info and perform login logic
        @google_bp.route('/verify')
        def verify():
            userinfo = google.get("/oauth2/v1/userinfo")
            if not userinfo.ok:
                return 'Google Login Fail'
            userinfo = userinfo.json()
            email = userinfo['email']
            name = userinfo['family_name'] + ' ' + userinfo['given_name']
            if self.login_handler(email, name):
                session['login'] = True
                if session.get('FLASK_DANCE_GOOGLE_REDIRECT_URL', None) is not None:
                    redirect_url = session.get('FLASK_DANCE_GOOGLE_REDIRECT_URL')
                    session['FLASK_DANCE_GOOGLE_REDIRECT_URL'] = None
                else:
                    redirect_url = url_for(return_endpoint)
                return redirect(redirect_url)
            else:
                session['login'] = False
                return f'Your Google account has no permission to login. <a href="{url_for(return_endpoint)}">Go Back</a>'

        @google_bp.route('/signin')
        def signin():
            if session.get('login', False):
                return f'You are already signed in. <a href="{url_for(return_endpoint)}">Go Back</a>'
            else:
                return redirect(url_for("google.login"))

        # define a signout route
        @google_bp.route('/signout')
        def signout():
            if session.get('login', False):
                resp = make_response(f'SignOut Success. <a href="{url_for(return_endpoint)}">Go Back</a>')
                resp.set_cookie('session', '', expires=0)
                return resp
            else:
                return f'You are not signed in yet. <a href="{url_for(return_endpoint)}">Go Back</a>'

        app.register_blueprint(google_bp, url_prefix="/dance_google_auth")

    def signin_url(self):
        return url_for('google.signin')

    def signout_url(self):
        return url_for('google.signout')

    # define a decorator method
    @staticmethod
    def login_required():
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if request.endpoint is None or request.endpoint.startswith('google.'):  # if requesting login page
                    return f(*args, **kwargs)
                if session.get('login', False):  # if already login
                    return f(*args, **kwargs)
                else:
                    session['FLASK_DANCE_GOOGLE_REDIRECT_URL'] = request.url
                    return redirect(url_for("google.login"))
            return decorated_function
        return decorator

    # define a decorator method
    @staticmethod
    def auth_required(auth_checker):
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if request.endpoint is None or request.endpoint.startswith('google.'):  # if requesting login page
                    return f(*args, **kwargs)
                if not session.get('login', False):  # if not login
                    session['FLASK_DANCE_GOOGLE_REDIRECT_URL'] = request.url
                    return redirect(url_for("google.login"))
                if auth_checker():  # if pass auth_checker
                    return f(*args, **kwargs)
                else:
                    signout_url = url_for('google.signout')
                    return f'No Permission. <a href="{signout_url}">SignOut</a>'
            return decorated_function
        return decorator

    # call this function to login_required all views
    def all_login_required(self):
        @self.app.before_request
        @self.login_required()
        def protect():
            pass

    # call this function to auth_required all views
    def all_auth_required(self, auth_checker):
        @self.app.before_request
        @self.auth_required(auth_checker)
        def protect():
            pass

    # change the login_handler function
    def set_login_handler(self, func):    # func(email,name)
        self.login_handler = func
