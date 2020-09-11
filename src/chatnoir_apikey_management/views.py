from concurrent.futures import ThreadPoolExecutor

from django.core.mail import EmailMultiAlternatives
from django.shortcuts import redirect, render
from django.template.loader import get_template
from django.utils.crypto import get_random_string

from .forms import KeyRequestForm
from .models import PendingApiUser

send_mail_executor = ThreadPoolExecutor(max_workers=20)


def index(request):
    if request.method == 'POST':
        form = KeyRequestForm(request.POST)

        if form.is_valid():
            activation_code = get_random_string(length=36)
            try:
                instance = PendingApiUser.objects.get(email=form.cleaned_data['email'],
                                                      passcode=form.cleaned_data['passcode'])
                form.update_instance(instance, activation_code)
            except PendingApiUser.DoesNotExist:
                instance = form.save(commit=False)
                instance.activation_code = activation_code
                instance.save()

            mail_context = {
                'activation_code': activation_code
            }
            mail_content_plain = get_template('apikey_email/confirmation_email.txt').render(mail_context, request)
            mail_content_html = get_template('apikey_email/confirmation_email.html').render(mail_context, request)
            mail = EmailMultiAlternatives(
                'Complete your ChatNoir API key request',
                mail_content_plain,
                'no-reply@chatnoir.eu',
                [instance.email]
            )
            mail.attach_alternative(mail_content_html, 'text/html')
            send_mail_executor.submit(mail.send)

            return redirect('apikey_management:request_sent')
        else:
            return render(request, 'apikey_frontend/index.html', {'form': form})
    else:
        form = KeyRequestForm()

    return render(request, 'apikey_frontend/index.html', {'form': form})


def request_sent(request):
    return render(request, 'apikey_frontend/request_sent.html', {})


def activate(request, activation_code):
    context = {}

    user = PendingApiUser.activate_by_code(activation_code)
    if user:
        user, api_key = user
        context['api_key'] = api_key

        mail_content_plain = get_template('apikey_email/apikey_email.txt').render(context, request)
        mail_content_html = get_template('apikey_email/apikey_email.html').render(context, request)
        mail = EmailMultiAlternatives(
            'Your ChatNoir API key',
            mail_content_plain,
            'no-reply@chatnoir.eu',
            [user.email]
        )
        mail.attach_alternative(mail_content_html, 'text/html')
        send_mail_executor.submit(mail.send)

    return render(request, 'apikey_frontend/activate.html', context)
