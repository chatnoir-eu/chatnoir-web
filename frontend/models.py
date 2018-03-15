from .chatnoir import ApiRequest

from django.db import models


class IssueKey(models.Model):
    """
    Issue / master API keys.
    """
    api_key = models.CharField(max_length=36, unique=True)

    def __str__(self):
        return self.api_key


class Passcode(models.Model):
    """
    API key issue passcodes.
    """
    issue_key = models.ForeignKey(IssueKey, on_delete=models.CASCADE)
    passcode = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.passcode


class User(models.Model):
    """
    API keys issued by passcode.
    """
    class Meta:
        unique_together = ('passcode', 'email_address')

    passcode = models.ForeignKey(Passcode, on_delete=models.CASCADE)
    email_address = models.CharField(max_length=200)

    def __str__(self):
        return '{} (passcode: {})'.format(self.email_address, self.passcode)

    @staticmethod
    def issue_api_key(activation_code):
        """
        Issue a new API key.

        :param activation_code: activation code
        :return: 2-tuple containing the new API key and the user's email address or
                 none if an error occurred (e.g., activation code invalid)
        """
        instance = PendingUser.get_by_activation_code(activation_code)
        if not instance:
            return None, None

        issue_key = instance.passcode.issue_key.api_key

        api_request = ApiRequest(issue_key, '_manage_keys', 'create')
        response = api_request.request({
            'user': {
                'common_name': instance.commonname,
                'email': instance.email,
                'organization': instance.organization,
                'address': instance.address,
                'zip_code': instance.zip_code,
                'state': instance.state,
                'country': instance.country,
            },
            'limits': {
                'day': None,
                'week': None,
                'month': None
            },
            'roles': []
        })

        if not response or 'apikey' not in response:
            return None, None

        user = User(passcode=instance.passcode, email_address=instance.email)
        user.save()
        instance.delete()

        return response['apikey'], user.email_address


class PendingUser(models.Model):
    class Meta:
        unique_together = ('email', 'passcode')

    commonname = models.CharField(max_length=100)
    email = models.EmailField(max_length=200)
    organization = models.CharField(max_length=100, null=True, blank=True)
    address = models.CharField(max_length=200, null=True, blank=True)
    zip_code = models.CharField(max_length=50, null=True, blank=True)
    state = models.CharField(max_length=50, null=True, blank=True)
    country = models.CharField(max_length=50, null=True, blank=True)
    activation_code = models.CharField(max_length=36, unique=True)
    passcode = models.ForeignKey(Passcode, on_delete=models.CASCADE)

    @staticmethod
    def get_by_activation_code(activation_code: str):
        """
        :param activation_code: activation code
        :return: pending user identified by `activation_code`
        """
        try:
            return PendingUser.objects.get(activation_code=activation_code)
        except PendingUser.DoesNotExist:
            return None
