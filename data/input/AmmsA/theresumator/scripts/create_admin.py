import os
if "ADMIN_USER" in os.environ and "ADMIN_PASSWORD" in os.environ:
    from django.contrib.auth.models import User
    user=User.objects.create_user(os.environ['ADMIN_USER'], password=os.environ['ADMIN_PASSWORD'])
    user.is_superuser=True
    user.is_staff=True
    user.save()
