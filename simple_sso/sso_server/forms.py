# -*- coding: utf-8 -*-
from django import forms
from simple_sso.signatures import verify_signature
from simple_sso.sso_server.models import Token, Client


class BaseForm(forms.Form):
    signature = forms.CharField(max_length=64, min_length=64)
    key = forms.CharField(max_length=64)
    
    def __init__(self, *args, **kwargs):
        self.invalid_signature = True
        self.client = None
        return super(BaseForm, self).__init__(*args, **kwargs)
    
    def clean(self):
        data = super(BaseForm, self).clean()
        parameters = [(key, value) for key, value in data.items() if key != 'signature']
        client_key = data['key']
        self.client = Client.objects.get(key=client_key)
        secret = self.client.secret
        signature = data['signature']
        if not verify_signature(parameters, signature, secret):
            raise forms.ValidationError('Invalid signature')
        self.invalid_signature = False
        return data


class RequestTokenRequestForm(BaseForm):
    pass


class AuthorizeForm(BaseForm):
    request_token = forms.CharField(max_length=64, min_length=64)
    
    def clean(self):
        data = super(AuthorizeForm, self).clean()
        request_token = data['request_token']
        try:
            token = Token.objects.get(request_token=request_token, client=self.client, user__isnull=True)
        except Token.DoesNotExist:
            raise forms.ValidationError('Invalid request token')
        return token


class VerificationForm(BaseForm):
    auth_token = forms.CharField(max_length=64, min_length=64)
    
    def clean(self):
        data = super(VerificationForm, self).clean()
        auth_token = data['auth_token']
        try:
            token = Token.objects.get(auth_token=auth_token, user__isnull=False, client=self.client)
        except Token.DoesNotExist:
            raise forms.ValidationError('Invalid auth token')
        return token
