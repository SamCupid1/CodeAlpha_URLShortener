from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class URLCreateForm(forms.Form):
    url = forms.CharField(
        label="Destination URL",
        max_length=2048,
        widget=forms.URLInput(
            attrs={
                "placeholder": "https://example.com/your-long-link",
                "autocomplete": "url",
                "class": "input input-bordered w-full",
            }
        ),
    )

    def clean_url(self):
        value = self.cleaned_data["url"].strip()
        validator = URLValidator(schemes=["http", "https"])
        try:
            validator(value)
        except ValidationError as exc:
            raise forms.ValidationError(
                _("Enter a valid URL beginning with http:// or https://.")
            ) from exc
        return value


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={
                "class": "input input-bordered w-full",
                "autocomplete": "email",
                "placeholder": "you@example.com",
            }
        ),
    )

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ("username", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "input input-bordered w-full")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if get_user_model().objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(_("An account with this email already exists."))
        return email
