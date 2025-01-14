from .auth import Auth
import base64
import flask
import ldap


class BasicAuth(Auth):
    def __init__(self, app):
        Auth.__init__(self, app)
        self._users = 0

    def is_authorized(self):
        header = flask.request.headers.get('Authorization', None)
        if not header:
            return False
        username_password = base64.b64decode(header.split('Basic ')[1])
        username_password_utf8 = username_password.decode('utf-8')
        username, password = username_password_utf8.split(':', 1)
        
        username=username+'@butec.com.lb'
        
        connect=ldap.initialize('ldap://192.168.10.10')
        connect.set_option(ldap.OPT_REFERRALS, 0)
        try:
            connect.simple_bind_s(username, password)
        except:
            return False

        result = connect.search_s('dc=butec,dc=com,dc=lb',
                                  ldap.SCOPE_SUBTREE,
                                  f'userPrincipalName={username}',
                                  ['memberOf'])
        result=result[0][1].get('memberOf')
#         print(result[0][1])
#         result=result[0][1]
        result=b'CN=AMI_BAMSYS,OU=IT Groups,OU=IT,OU=Beirut,DC=butec,DC=com,DC=lb' in result
        return result

    def login_request(self):
        return flask.Response(
            'Login Required',
            headers={'WWW-Authenticate': 'Basic realm="User Visible Realm"'},
            status=401)

    def auth_wrapper(self, f):
        def wrap(*args, **kwargs):
            if not self.is_authorized():
                return flask.Response(status=403)

            response = f(*args, **kwargs)
            return response
        return wrap

    def index_auth_wrapper(self, original_index):
        def wrap(*args, **kwargs):
            if self.is_authorized():
                return original_index(*args, **kwargs)
            else:
                return self.login_request()
        return wrap
