from django.urls import path
from . import views

urlpatterns = [
    # Core pages
    path('', views.home, name='home'),
    
    # Product pages
    path('products/', views.product_list, name='product_list'),
    path('products/<slug:category_slug>/', views.product_list, name='product_list_by_category'),
    path('product/<int:id>/<slug:slug>/', views.product_detail, name='product_detail'),
    
    # Search
    path('search/', views.product_search, name='product_search'),
    path('search/suggestions/', views.search_suggestions, name='search_suggestions'),
    
    # Cart management
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('cart/update/', views.update_cart, name='cart_update'),  # AJAX
    path('cart/remove/<int:product_id>/', views.cart_remove, name='cart_remove'),
    
    # Wishlist
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('wishlist/toggle/', views.toggle_wishlist, name='toggle_wishlist'),  # AJAX
    
    # Checkout and Orders
    path('checkout/', views.checkout, name='checkout'),
    path('orders/', views.order_history, name='order_history'),
    path('order/<str:order_id>/', views.order_detail, name='order_detail'),
    
    # Reviews
    path('product/<int:product_id>/review/', views.add_review, name='add_review'),
    
    # Authentication
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    
    # User profile
    path('profile/', views.profile_view, name='profile'),
]