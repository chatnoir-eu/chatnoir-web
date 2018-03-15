from django.core.mail import EmailMultiAlternatives
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.template.loader import get_template
from django.utils.crypto import get_random_string

from .forms import KeyRequestForm
from .models import Passcode, PendingUser, User


def index(request):
    if request.method == 'POST':
        form = KeyRequestForm(request.POST)

        if form.is_valid():
            activation_code = get_random_string(length=36)
            try:
                instance = PendingUser.objects.get(email=form.cleaned_data['email'],
                                                   passcode=form.cleaned_data['passcode'])
                form.update_instance(instance, activation_code)
            except PendingUser.DoesNotExist:
                instance = form.save(commit=False)
                instance.activation_code = activation_code
                instance.save()

            mail_context = {
                'activation_code': activation_code
            }
            mail_content_plain = get_template('frontend/confirmation_email.txt').render(mail_context, request)
            mail_content_html = get_template('frontend/confirmation_email.html').render(mail_context, request)
            mail = EmailMultiAlternatives(
                'Complete your ChatNoir API key request',
                mail_content_plain,
                'no-reply@chatnoir.eu',
                [instance.email]
            )
            mail.attach_alternative(mail_content_html, 'text/html')
            mail.send()

            return HttpResponseRedirect('/request_sent')
        else:
            return render(request, 'frontend/index.html', {'form': form})
    else:
        form = KeyRequestForm()

    return render(request, 'frontend/index.html', {'form': form})


def request_sent(request):
    return render(request, 'frontend/request_sent.html', {})


def activate(request, activation_code):
    context = {}

    api_key, email = User.issue_api_key(activation_code)
    if api_key:
        context['api_key'] = api_key

        mail_content_plain = get_template('frontend/apikey_email.txt').render(context, request)
        mail_content_html = get_template('frontend/apikey_email.html').render(context, request)
        mail = EmailMultiAlternatives(
            'Your ChatNoir API key',
            mail_content_plain,
            'no-reply@chatnoir.eu',
            [email]
        )
        mail.attach_alternative(mail_content_html, 'text/html')
        mail.send()

    return render(request, 'frontend/activate.html', context)
