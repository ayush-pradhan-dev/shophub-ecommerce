from functools import wraps
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required


def seller_required(view_func):
    """
    Decorator for function-based views. Ensures the user is logged in,
    has role=SELLER, AND is verified. Raises 403 otherwise (not a redirect —
    an unverified seller trying to access seller URLs is a permissions issue,
    not a "please log in" issue).
    """
    @login_required
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.can_sell:
            raise PermissionDenied("You must be a verified seller to access this page.")
        return view_func(request, *args, **kwargs)
    return wrapper


class SellerRequiredMixin:
    """
    Mixin for class-based views (CreateView, UpdateView, DeleteView, ListView).
    Must be listed BEFORE the generic view class in the inheritance list, e.g.:
        class ProductCreateView(SellerRequiredMixin, CreateView): ...
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        if not request.user.can_sell:
            raise PermissionDenied("You must be a verified seller to access this page.")
        return super().dispatch(request, *args, **kwargs)


class SellerOwnsObjectMixin:
    """
    Ensures a seller can only edit/delete/view THEIR OWN products —
    not another seller's, even if they guess the URL/ID directly.
    Must be combined with SellerRequiredMixin.
    """
    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(seller=self.request.user)
    