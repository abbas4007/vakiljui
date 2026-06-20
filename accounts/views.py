from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.views.generic import CreateView
from django.urls import reverse_lazy
from .forms import SignupForm


class SignupView(CreateView) :
    form_class = SignupForm
    template_name = 'accounts/signup.html'
    success_url = reverse_lazy('home:index')

    def form_valid(self, form) :
        response = super().form_valid(form)
        login(self.request, self.object)
        return response

    def get_context_data(self, **kwargs) :
        ctx = super().get_context_data(**kwargs)
        ctx['robots'] = 'noindex, follow'
        ctx['meta_title'] = 'ثبت‌نام در سامانه وکلا'
        ctx['meta_description'] = 'ثبت‌نام وکلا و کاربران عادی'
        return ctx

def login_view(request):
    """صفحه ورود به حساب کاربری"""
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                # هدایت به پنل ادمین
                if user.is_staff:
                    return redirect('admin:index')
                else:
                    return redirect('home:index')
    else:
        form = AuthenticationForm()

    return render(request, 'accounts/login.html', {
        'form': form,
        'robots': 'noindex, follow',
        'meta_title': 'ورود به حساب کاربری',
        'meta_description': 'ورود به سامانه وکلا'
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


def logout_view(request) :
    """خروج از حساب کاربری"""
    logout(request)
    return redirect('home:index')