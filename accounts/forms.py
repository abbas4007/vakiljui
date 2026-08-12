from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()


class SignupForm(forms.ModelForm):
    password1 = forms.CharField(
        label='رمز عبور',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'autocomplete': 'new-password',
        }),
        min_length=8,
    )

    password2 = forms.CharField(
        label='تکرار رمز عبور',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'autocomplete': 'new-password',
        }),
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'phone')

    def clean_username(self):
        username = self.cleaned_data['username']

        if User.objects.filter(username=username).exists():
            raise forms.ValidationError(
                'این نام کاربری قبلاً ثبت شده است.'
            )

        return username

    def clean_email(self):
        email = self.cleaned_data['email']

        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                'این ایمیل قبلاً ثبت شده است.'
            )

        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()

        if phone and User.objects.filter(phone=phone).exists():
            raise forms.ValidationError(
                'این شماره تلفن قبلاً ثبت شده است.'
            )

        return phone

    def clean(self):
        cleaned_data = super().clean()

        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            self.add_error(
                'password2',
                'رمز عبور و تکرار آن یکسان نیستند.'
            )

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)

        user.set_password(self.cleaned_data['password1'])

        if commit:
            user.save()

        return user