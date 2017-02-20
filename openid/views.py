import os
import hashlib
import requests
import logging
import json

from jose import jwk, jwt
from jose.utils import base64url_decode

from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic import ListView
from django.contrib.auth.models import User
from django.contrib.auth import logout, authenticate, login
from django.shortcuts import redirect

from .models import Provider

logger = logging.getLogger(__name__)

def verify_token(id_token, provider):
    header, _ = id_token.split('.', 1)
    try:
        kid = json.loads(base64url_decode(header.encode('UTF-8')).decode('UTF-8'))['kid']
        alg = json.loads(base64url_decode(header.encode('UTF-8')).decode('UTF-8'))['alg']
    except (KeyError):
        logger.error('Invalid header')
        return False

    jwks_uri = provider.jwks_uri

    r = requests.get(jwks_uri)
    jwk_json = r.json()

    logger.debug(jwk_json)

    try:
        jwk_json = list(filter(lambda x: x['kid'] == kid, jwk_json['keys']))[0]
    except (KeyError):
        logger.error('Invalid JWK')
        return False

    if not 'alg' in jwk_json:
        jwk_json['alg'] = alg

    key = jwk.construct(jwk_json)
    message, encoded_sig = id_token.rsplit('.', 1)
    message = message.encode('UTF-8')
    encoded_sig = encoded_sig.encode('UTF-8')

    logger.debug(message)
    logger.debug(encoded_sig)

    decoded_sig = base64url_decode(encoded_sig)
    verified = key.verify(message, decoded_sig)
    
    return verified

def authenticate_user(request, subject, issuer, access_token):
    try:
        user = User.objects.get(username=subject)
    except User.DoesNotExist:
        user = User(username=subject)
        user.is_staff = True
        user.save()

    password = hashlib.sha256(os.urandom(1024)).hexdigest()
    user.set_password(password)
    user.save()

    user = authenticate(username=subject, password=password)
    if user is not None:
        login(request, user)

        request.session['sub'] = subject
        request.session['iss'] = issuer
        request.session['access_token'] = access_token

    return user

def openid_logout(request):
    logout(request)
    return redirect('openid:login')

def openid_login(request):
    try:
        client_id, state = request.GET['state'].rsplit('.', 1)
    except (KeyError):
        return HttpResponse("Invalid state parameter", status=401)

    if state != request.session['state']:
        return HttpResponse("Invalid state parameter", status=401)

    try:
        code = request.GET['code']
    except (KeyError):
        return HttpResponse("Invalid code parameter", status=401)

    try:
        provider = Provider.objects.get(client_id=client_id)
    except (Provider.DoesNotExist):
        return HttpResponse("OIDC provider not found", status=401)

    client_secret = provider.client_secret
    redirect_uri = provider.redirect_uri
    token_endpoint = provider.token_endpoint
    
    payload = {'code': code, 'client_id': client_id, 
            'client_secret': client_secret, 'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'}

    r = requests.post(token_endpoint, data=payload)
    credentials = r.json()

    logger.debug(credentials)

    access_token = credentials.get('access_token', '')
    id_token = credentials.get('id_token', '')

    verified = verify_token(id_token, provider)

    logger.debug("Token is valid: {}".format(verified))

    if not verified:
        return HttpResponse("Invalid token signature", status=401)

    jwt_json = jwt.get_unverified_claims(id_token)

    sub = jwt_json.get('sub', '')
    iss = jwt_json.get('iss', '')

    user = authenticate_user(request, sub, iss, access_token)

    if user is not None:
        logger.debug("User {} logged in".format(user.username))
        next_url = settings.OPENID_LOGIN_REDIRECT if settings.OPENID_LOGIN_REDIRECT else '/'
    else:
        next_url = 'openid:login'
        logger.warning("Could not log in user with subject {} issuer {}".format(sub, iss))

    return redirect(next_url)

class LoginView(ListView):

    model = Provider
    context_object_name = 'provider_list'

    template_name = 'openid/login.html'

    def get_context_data(self, **kwargs):
        context = super(LoginView, self).get_context_data(**kwargs)

        state = hashlib.sha256(os.urandom(1024)).hexdigest()

        context['state'] = state
        self.request.session['state'] = state

        return context
