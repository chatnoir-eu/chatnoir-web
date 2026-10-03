"""
Create (or reuse) an unrestricted demo API key for the all-in-one image.

The ChatNoir migrations already create a root key and a "DEFAULT ISSUE KEY",
but both are restricted to requests from 127.0.0.1/::1, so they don't work
when the API is reached from outside the container (e.g. via a mapped Docker
port). This script issues a separate, unrestricted child key for demo/testing
purposes and prints it so it can be picked up from the container logs or the
file it is written to.

Intended to be run via: chatnoir-manage shell < create-demo-apikey.py
"""

from chatnoir_api.models import ApiConfiguration, ApiKey

DEMO_KEY_COMMENT = 'ALL-IN-ONE DEMO KEY'

config = ApiConfiguration.objects.get()
root_key = config.default_issue_key
while root_key.parent_id:
    root_key = root_key.parent

demo_key, created = ApiKey.objects.get_or_create(
    comments=DEMO_KEY_COMMENT,
    defaults={
        'user': root_key.user,
        'parent': root_key,
        'issuer': 'all-in-one-demo',
        'allowed_remote_hosts': '',
    },
)

if created:
    demo_key.roles.set(root_key.roles.all())

with open('/opt/chatnoir-web/demo-apikey.txt', 'w') as f:
    f.write(demo_key.api_key + '\n')

print(f'DEMO_API_KEY={demo_key.api_key}')
