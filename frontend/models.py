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


class PendingUser(models.Model):

    class Meta:
        unique_together = ('email', 'passcode')

    commonname = models.CharField(max_length=100)
    email = models.EmailField(max_length=200)
    address = models.CharField(max_length=200, null=True, blank=True)
    zip_code = models.CharField(max_length=50, null=True, blank=True)
    state = models.CharField(max_length=50, null=True, blank=True)
    country = models.CharField(max_length=50, null=True, blank=True)
    activation_code = models.CharField(max_length=36, unique=True)
    passcode = models.ForeignKey(Passcode, on_delete=models.CASCADE)

    @staticmethod
    def get_by_activation_code(code: str):
        return PendingUser.objects.get(activation_code=code)
