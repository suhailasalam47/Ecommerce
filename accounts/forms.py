from django import forms
from .models import Account


class RegistrationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Enter password"})
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"placeholder": "Confirm password "}
        )
    )

    class Meta:
        model = Account
        fields = ["first_name", "last_name", "email", "phone_number"]

    def __init__(self, *arg, **kwargs):
        super(RegistrationForm, self).__init__(*arg, **kwargs)
        self.fields["first_name"].widget.attrs[
            "placeholder"
        ] = "Enter first name"
        self.fields["last_name"].widget.attrs[
            "placeholder"
        ] = "Enter last name"
        self.fields["email"].widget.attrs[
            "placeholder"
        ] = "Enter email address"
        self.fields["phone_number"].widget.attrs[
            "placeholder"
        ] = "Enter your phone number"
        for field in self.fields:
            self.fields[field].widget.attrs["class"] = "form-control"
