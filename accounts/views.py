from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView
from .forms import LawyerVerificationForm, SignupForm
from .models import LawyerVerification
from django.views.generic import CreateView, TemplateView


class SignupView(CreateView) :
    form_class = SignupForm
    template_name = 'accounts/signup.html'
    success_url = reverse_lazy('home:index')

    def form_valid(self, form) :
        self.object = form.save()

        login(
            self.request,
            self.object
        )

        return redirect(self.get_success_url())

    def get_context_data(self, **kwargs) :
        context = super().get_context_data(**kwargs)

        context['robots'] = 'noindex, follow'
        context['meta_title'] = 'ثبت‌نام در سامانه وکلا'
        context['meta_description'] = 'ثبت‌نام وکلا و کاربران عادی'

        return context


def login_view(request) :
    """صفحه ورود به حساب کاربری"""
    if request.method == 'POST' :
        form = AuthenticationForm(request, data = request.POST)
        if form.is_valid() :
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username = username, password = password)
            if user is not None :
                login(request, user)
                return redirect('home:index')
            else :
                return redirect('accounts:login')
    else :
        form = AuthenticationForm()

    return render(request, 'accounts/login.html', {
        'form' : form,
        'robots' : 'noindex, follow',
        'meta_title' : 'ورود به حساب کاربری',
        'meta_description' : 'ورود به سامانه وکلا'
    })


# def login_view(request) :
#     """صفحه ورود به حساب کاربری"""
#     if request.method == 'POST' :
#         form = AuthenticationForm(request, data = request.POST)
#         if form.is_valid() :
#             username = form.cleaned_data.get('username')
#             password = form.cleaned_data.get('password')
#             user = authenticate(username = username, password = password)
#             if user is not None :
#                 login(request, user)
#                 return redirect('home:index')
#     else :
#         form = AuthenticationForm()
#
#     return render(request, 'accounts/login.html', {
#         'form' : form,
#         'robots' : 'noindex, follow',
#         'meta_title' : 'ورود به حساب کاربری',
#         'meta_description' : 'ورود به سامانه وکلا'
#     })

class LawyerVerificationCreateView(
    LoginRequiredMixin,
    CreateView
) :
    model = LawyerVerification
    form_class = LawyerVerificationForm
    template_name = 'accounts/lawyer_verification.html'
    success_url = reverse_lazy('accounts:lawyer_verification_success')

    def dispatch(self, request, *args, **kwargs) :

        if request.user.is_lawyer :
            return redirect('accounts:profile')

        latest_request = (
            LawyerVerification.objects
            .filter(user = request.user)
            .order_by('-created_at')
            .first()
        )

        if latest_request and latest_request.status == LawyerVerification.STATUS_PENDING :
            return redirect('accounts:lawyer_verification_status')

        if latest_request and latest_request.status == LawyerVerification.STATUS_APPROVED :
            return redirect('accounts:profile')

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form) :

        form.instance.user = self.request.user

        return super().form_valid(form)


class LawyerVerificationSuccessView(LoginRequiredMixin, TemplateView) :
    template_name = 'accounts/lawyer_verification_success.html'


class LawyerVerificationStatusView(LoginRequiredMixin, TemplateView) :
    template_name = 'accounts/lawyer_verification_status.html'

    def get_context_data(self, **kwargs) :
        context = super().get_context_data(**kwargs)

        context['verification'] = (
            LawyerVerification.objects
            .filter(user = self.request.user)
            .order_by('-created_at')
            .first()
        )

        return context


def logout_view(request) :
    """خروج از حساب کاربری"""
    logout(request)
    return redirect('home:index')
