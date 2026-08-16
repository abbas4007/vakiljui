from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from .models import  LawyerVerification



User = get_user_model()




class SignupForm(UserCreationForm):

    email = forms.EmailField(required=True)

    phone = forms.CharField(
        max_length=20,
        required=False
    )

    class Meta:
        model = User
        fields = (
            'username',
            'email',
            'phone',
            'password1',
            'password2',
        )


class LawyerVerificationForm(forms.ModelForm):

    class Meta:
        model = LawyerVerification

        fields = (
            'full_name',
            'national_id',
            'bar_association',
            'license_number',
            'document',
        )

        labels = {
            'full_name': 'نام و نام خانوادگی',
            'national_id': 'کد ملی',
            'bar_association': 'کانون وکلا',
            'license_number': 'شماره پروانه وکالت',
            'document': 'تصویر یا فایل پروانه وکالت',
        }

        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'نام و نام خانوادگی'
            }),

            'national_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'کد ملی'
            }),

            'bar_association': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'مثلاً کانون وکلای دادگستری همدان'
            }),

            'license_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'شماره پروانه وکالت'
            }),

            'document': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': '.jpg,.jpeg,.png,.pdf'
            }),
        }