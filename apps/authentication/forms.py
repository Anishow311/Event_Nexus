from django import forms
from .models import CustomUser


class RegistrationForm(forms.ModelForm):

    password = forms.CharField(
        widget=forms.PasswordInput
    )

    confirm_password = forms.CharField(
        widget=forms.PasswordInput
    )

    club_name = forms.CharField(
        max_length=200,
        required=False
    )

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'role']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Admin cannot register through the public registration page
        self.fields['role'].choices = [
            ('STUDENT', 'Student'),
            ('CLUB', 'Club'),
        ]

    def clean(self):
        cleaned_data = super().clean()

        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        role = cleaned_data.get('role')

        if password and confirm_password:
            if password != confirm_password:
                raise forms.ValidationError(
                    "Passwords do not match."
                )

        if role == 'STUDENT':
            if not cleaned_data.get('first_name'):
                self.add_error(
                    'first_name',
                    'First name is required for students.'
                )

            if not cleaned_data.get('last_name'):
                self.add_error(
                    'last_name',
                    'Last name is required for students.'
                )

        elif role == 'CLUB':
            if not cleaned_data.get('club_name'):
                self.add_error(
                    'club_name',
                    'Club name is required for clubs.'
                )

        return cleaned_data


class LoginForm(forms.Form):
    email = forms.EmailField(
        label="Email Address",
        widget=forms.EmailInput(attrs={'placeholder': 'Enter your email', 'autocomplete': 'email'})
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter your password', 'autocomplete': 'current-password'})
    )