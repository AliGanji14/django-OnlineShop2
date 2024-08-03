import random
from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages

from .forms import UserRegisterForm
from .models import OtpCode
from utils import send_otp_code


class UserRegisterView(View):
    form_class = UserRegisterForm

    def get(self, request):
        form = self.form_class
        return render(request, 'accounts/register.html', {'form': form})

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            phone_number = form.cleaned_data['phone_number']
            email = form.cleaned_data['email']
            full_name = form.cleaned_data['full_name']
            password = form.cleaned_data['password']

            randon_code = random.randint(10000, 99999)

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
        return redirect('home:home')


class UserRegisterVerifyCodeView(View):
    def get(self, request):
        pass

    def post(self, request):
        pass
