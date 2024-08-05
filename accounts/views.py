import random
from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from django.contrib.auth import get_user_model, authenticate, login, logout

from .forms import UserRegisterForm, VerifyCodeForm, UserLoginForm
from .models import OtpCode
from utils import send_otp_code


class UserRegisterView(View):
    form_class = UserRegisterForm
    template_name = 'accounts/register.html'

    def get(self, request):
        form = self.form_class
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            phone_number = form.cleaned_data['phone']
            email = form.cleaned_data['email']
            full_name = form.cleaned_data['full_name']
            password = form.cleaned_data['password']

            randon_code = random.randint(1000, 9999)

            send_otp_code(phone_number, randon_code)
            OtpCode.objects.create(phone_number=phone_number, code=randon_code)

            request.session['user_registration_info'] = {
                'phone_number': phone_number,
                'email': email,
                'full_name': full_name,
                'password': password,
            }
            messages.success(request, 'we sent you a code', 'success')
            return redirect('accounts:verify_code')
        return render(request, self.template_name, {'form': form})


class UserRegisterVerifyCodeView(View):
    form_class = VerifyCodeForm

    def get(self, request):
        form = self.form_class
        return render(request, 'accounts/verify.html', {'form': form})

    def post(self, request):
        user_session = request.session['user_registration_info']
        code_instance = OtpCode.objects.get(phone_number=user_session['phone_number'])

        form = self.form_class(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            if code_instance.is_expired():
                messages.error(request, 'The code has expired. Please request a new code.', 'danger')
                code_instance.delete()
                return redirect('accounts:user_register')
            if cd['code'] == code_instance.code:
                get_user_model().objects.create_user(
                    phone_number=user_session['phone_number'],
                    email=user_session['email'],
                    full_name=user_session['full_name'],
                    password=user_session['password']
                )
                code_instance.delete()
                messages.success(request, 'you registered successfully', 'success')
                return redirect('home:home')
            else:
                messages.error(request, 'this code is wrong', 'danger')
                return redirect('accounts:verify_code')
        return render(request, 'accounts/verify.html', {'form': form})


class UserLogoutView(View):
    def get(self, request):
        logout(request)
        messages.success(request, 'you logged out successfully', 'success')
        return redirect('shop:product_list')


class UserLoginView(View):
    form_class = UserLoginForm
    template_name = 'accounts/login.html'

    def get(self, request):
        form = self.form_class
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            user = authenticate(request, phone_number=cd['phone'], password=cd['password'])
            if user is not None:
                login(request, user)
                messages.success(request, 'you logged in successfully', 'info')
                return redirect('shop:product_list')
            messages.error(request, 'phone or password is wrong', 'warning')
        return render(request, self.template_name, {'form': form})
