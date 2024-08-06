import requests
import json
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages

from shop.models import Product
from .cart import Cart
from .forms import CartAddForm, CouponApplyForm
from .models import Order, OrderItem, Coupon


class CartView(View):
    def get(self, request):
        cart = Cart(request)
        return render(request, 'orders/cart.html', {'cart': cart})


class CartAddView(PermissionRequiredMixin, View):
    permission_required = 'orders.add_order'

    def post(self, request, product_id):
        cart = Cart(request)
        product = get_object_or_404(Product, pk=product_id)
        form = CartAddForm(request.POST)
        if form.is_valid():
            cart.add(product, form.cleaned_data['quantity'])
        return redirect('orders:cart')


class CartRemoveView(View):
    def get(self, request, product_id):
        cart = Cart(request)
        product = get_object_or_404(Product, id=product_id)
        cart.remove(product)
        return redirect('orders:cart')


class OrderCreateView(LoginRequiredMixin, View):
    def get(self, request):
        cart = Cart(request)
        order = Order.objects.create(user=request.user)
        for item in cart:
            (OrderItem.objects.create(
                order=order,
                product=item['product'],
                price=item['price'],
                quantity=item['quantity']
            ))
        cart.clear()
        return redirect('orders:order_detail', order.id)


class OrderDetailView(LoginRequiredMixin, View):
    form_class = CouponApplyForm

    def get(self, request, order_id):
        form = CouponApplyForm
        order = get_object_or_404(Order, pk=order_id)
        return render(request, 'orders/order.html', {'order': order, 'form': form})


MERCHANT = 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
ZP_API_REQUEST = "https://sandbox.zarinpal.com/pg/rest/WebGate/PaymentRequest.json"
ZP_API_VERIFY = "https://sandbox.zarinpal.com/pg/rest/WebGate/PaymentVerification.json"
CallbackURL = 'http://127.0.0.1:8000/orders/verify/'


class OrderPayView(LoginRequiredMixin, View):
    def post(self, request, order_id):
        order = get_object_or_404(Order, pk=order_id)
        request.session['order_pay'] = {
            'order_id': order_id,
        }
        req_data = {
            'MerchantID': MERCHANT,
            'Amount': order.get_total_price(),
            'CallbackURL': CallbackURL,
            'Description': f'#{order.id}: {order.user.phone_number} {order.user.email}',
        }
        req_header = {
            "accept": "application/json",
            "content-type": "application/json'"
        }
        req = requests.post(url=ZP_API_REQUEST, data=json.dumps(req_data), headers=req_header)

        data = req.json()
        authority = data['Authority']

        if 'errors' not in data or len(data['errors']) == 0:
            return redirect(f'https://sandbox.zarinpal.com/pg/StartPay/{authority}')
        else:
            return HttpResponse('Error from zarinpal')


class OrderVerifyView(LoginRequiredMixin, View):
    def get(self, request):
        order_id = request.session['order_pay']['order_id']
        order = get_object_or_404(Order, pk=order_id)
        t_status = request.GET.get('Status')
        t_authority = request.GET['Authority']
        if t_status == 'OK':
            req_header = {"accept": "application/json", "content-type": "application/json'"}
            req_data = {
                'MerchantID': MERCHANT,
                'Amount': order.get_total_price(),
                'Authority': t_authority
            }
            req = requests.post(url=ZP_API_VERIFY, data=json.dumps(req_data), headers=req_header)
            if 'errors' not in req.json():
                data = req.json()
                payment_code = data['Status']
                if payment_code == 100:
                    order.paid = True
                    order.save()
                    return HttpResponse(f'Your payment has been successfully completed. RefID: {data['RefID']}')
                elif payment_code == 101:
                    return HttpResponse(
                        'Your payment has been successfully completed. Of course, this transaction has already been registered')
            else:
                error_code = req.json()['errors']['code']
                error_message = req.json()['errors']['message']
                return HttpResponse(f'Error code: {error_code}, Error Message: {error_message}')

        else:
            return HttpResponse('Transaction failed or canceled by user')


class CouponApplyView(LoginRequiredMixin, View):
    form_class = CouponApplyForm

    def post(self, request, order_id):
        form = self.form_class(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            try:
                coupon = Coupon.objects.get(code__exact=code, active=True)
            except Coupon.DoesNotExist:
                messages.error(request, 'this coupon dose not exists', 'danger')
                return redirect('orders:order_detail', order_id)

            order = Order.objects.get(id=order_id)
            order.discount = coupon.discount
            order.save()
        return redirect('orders:order_detail', order_id)
