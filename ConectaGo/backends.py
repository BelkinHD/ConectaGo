from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User

class EmailBackend(ModelBackend):
    """
    Custom authentication backend to authenticate users using their email address.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        users = User.objects.filter(email__iexact=username)
        if not users.exists():
            return None
        user = users[0]  # or logic to choose the correct user
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None

    def get_user(self, user_id):
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
        return user if self.user_can_authenticate(user) else None
