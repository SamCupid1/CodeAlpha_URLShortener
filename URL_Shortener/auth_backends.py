from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.db.models import Q


class UsernameOrEmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        identifier = username or kwargs.get(UserModel.USERNAME_FIELD)
        if not identifier or password is None:
            return None

        users = UserModel._default_manager
        try:
            user = users.get_by_natural_key(identifier)
        except ObjectDoesNotExist:
            matches = users.filter(
                Q(**{f"{UserModel.USERNAME_FIELD}__iexact": identifier})
                | Q(email__iexact=identifier)
            ).distinct()
            try:
                user = matches.get()
            except (ObjectDoesNotExist, MultipleObjectsReturned):
                UserModel().set_password(password)
                return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
