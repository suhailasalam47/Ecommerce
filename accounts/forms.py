from django import forms
from .models import Account, UserProfile


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
        # self.fields["first_name"].widget.attrs[
        #     "placeholder"
        # ] = "Enter first name"
        # self.fields["last_name"].widget.attrs[
        #     "placeholder"
        # ] = "Enter last name"
        # self.fields["email"].widget.attrs[
        #     "placeholder"
        # ] = "Enter email address"
        # self.fields["phone_number"].widget.attrs[
        #     "placeholder"
        # ] = "Enter your phone number"
        for field in self.fields:
            self.fields[field].widget.attrs["class"] = "form-control"
        

class UserForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ("first_name","last_name","phone_number")

    def __init__(self, *arg, **kwargs):
        super(UserForm, self).__init__(*arg, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs["class"] = "form-control"


class UserProfileForm(forms.ModelForm):
    profile_picture = forms.ImageField(required=False, error_messages={'invalid':("Please upload a valid file format")}, widget=forms.FileInput)
    class Meta:
        model = UserProfile
        fields = ("address_line1","address_line2","city","state","country","profile_picture")

    def __init__(self, *arg, **kwargs):
        super(UserProfileForm, self).__init__(*arg, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs["class"] = "form-control"


# class OtpVerificationForm(forms.ModelForm):
#     class Meta:
#         model = Account
#         fields = ("phone_number")

#     def __init__(self, *arg, **kwargs):
#         super(OtpVerificationForm, self).__init__(*arg, **kwargs)
#         for field in self.fields:
#             self.fields[field].widget.attrs["class"] = "form-control"