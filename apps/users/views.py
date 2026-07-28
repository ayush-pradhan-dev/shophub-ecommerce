from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.views.generic import CreateView
from .forms import CustomerSignUpForm
from apps.orders.cart import CartService


class SignUpView(CreateView):
    form_class = CustomerSignUpForm
    template_name = 'users/signup.html'
    success_url = reverse_lazy('store:home')

    def form_valid(self, form):
        old_session_key = self.request.session.session_key
        response = super().form_valid(form)
        login(self.request, self.object)
        CartService.merge_guest_cart_into_user(old_session_key, self.object)
        return response


class CustomLoginView(LoginView):
    template_name = 'users/login.html'

    def form_valid(self, form):
        old_session_key = self.request.session.session_key
        response = super().form_valid(form)
        CartService.merge_guest_cart_into_user(old_session_key, self.request.user)
        return response


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('store:home')