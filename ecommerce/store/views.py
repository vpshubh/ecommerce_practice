from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.db.models import Q, Avg, Count
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.views.generic import ListView
from .models import *
import json
from users.forms import CustomUserCreationForm  # Add this import at the top


def home(request):
    """Enhanced home page with featured products and categories"""
    featured_products = Product.objects.filter(is_featured=True, is_active=True)[:12]
    categories = Category.objects.filter(is_active=True)[:8]
    latest_products = Product.objects.filter(is_active=True).order_by('-created_at')[:8]
    
    context = {
        'featured_products': featured_products,
        'categories': categories,
        'latest_products': latest_products,
    }
    return render(request, 'store/home.html', context)

def product_list(request):
    """Enhanced product listing with search, filters, and pagination"""
    products = Product.objects.filter(is_active=True)
    categories = Category.objects.filter(is_active=True)
    brands = Brand.objects.filter(is_active=True)
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query) |
            Q(category__name__icontains=search_query)
        )
    
    # Category filter
    category_slug = request.GET.get('category')
    selected_category = None
    if category_slug:
        selected_category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=selected_category)
    
    # Brand filter
    brand_id = request.GET.get('brand')
    if brand_id:
        products = products.filter(brand_id=brand_id)
    
    # Price filter
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)
    
    # Sorting
    sort_by = request.GET.get('sort', 'created_at')
    if sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')
    elif sort_by == 'name':
        products = products.order_by('name')
    elif sort_by == 'rating':
        products = products.annotate(avg_rating=Avg('reviews__rating')).order_by('-avg_rating')
    else:
        products = products.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(products, 12)
    page = request.GET.get('page')
    products = paginator.get_page(page)
    
    context = {
        'products': products,
        'categories': categories,
        'brands': brands,
        'search_query': search_query,
        'selected_category': selected_category,
        'current_sort': sort_by,
    }
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'store/partials/product_grid.html', {'products': products})
    return render(request, 'store/product_list.html', {
        'products': products,
        'popular_products': Product.objects.popular()[:4]  # Implement this queryset
    })
    # return render(request, 'store/product_list.html', context)

def product_detail(request, slug):
    """Enhanced product detail with reviews and related products"""
    product = get_object_or_404(Product, slug=slug, is_active=True)
    reviews = product.reviews.filter(is_approved=True).order_by('-created_at')
    related_products = Product.objects.filter(
        category=product.category, 
        is_active=True
    ).exclude(id=product.id)[:4]
    
    # Check if user has purchased this product
    has_purchased = False
    user_review = None
    if request.user.is_authenticated:
        try:
            has_purchased = OrderItem.objects.filter(
                order__user=request.user, 
                product=product,
                order__status='delivered'
            ).exists()
            
            user_review = Review.objects.get(product=product, user=request.user)
        except Review.DoesNotExist:
            pass
    
    context = {
        'product': product,
        'reviews': reviews,
        'related_products': related_products,
        'has_purchased': has_purchased,
        'user_review': user_review,
    }
    return render(request, 'store/product_detail.html', context)

@login_required
def add_to_cart(request):
    """AJAX endpoint to add products to cart"""
    if request.method == 'POST':
        try:
            # Handle both form data and JSON data
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                product_id = data.get('product_id')
                quantity = int(data.get('quantity', 1))
            else:
                product_id = request.POST.get('product_id')
                quantity = int(request.POST.get('quantity', 1))
            
            product = Product.objects.get(id=product_id, is_active=True)
            cart, created = Cart.objects.get_or_create(user=request.user)
            
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart, 
                product=product,
                defaults={'quantity': quantity}
            )
            
            if not created:
                cart_item.quantity += quantity
                cart_item.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Item added to cart',
                'cart_count': cart.total_items
            })
        except Product.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Product not found'})
        except Exception as e:
            print(f"Cart error: {e}")  # This will show in your Django console
            return JsonResponse({'success': False, 'message': 'An error occurred'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})
@login_required
def cart_view(request):
    """Enhanced shopping cart view"""
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    context = {
        'cart': cart,
        'cart_items': cart.items.all(),
    }
    return render(request, 'store/cart.html', context)

@login_required
@require_POST
def update_cart(request):
    """AJAX endpoint to update cart item quantity"""
    item_id = request.POST.get('item_id')
    quantity = int(request.POST.get('quantity'))
    
    try:
        cart_item = CartItem.objects.get(
            id=item_id, 
            cart__user=request.user
        )
        
        if quantity <= 0:
            cart_item.delete()
            message = 'Item removed from cart'
        else:
            cart_item.quantity = quantity
            cart_item.save()
            message = 'Cart updated'
        
        cart = cart_item.cart
        return JsonResponse({
            'success': True,
            'message': message,
            'cart_total': float(cart.total_amount),
            'cart_count': cart.total_items
        })
    except CartItem.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Item not found'})

@login_required
def wishlist_view(request):
    """User's wishlist"""
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    wishlist_items = WishlistItem.objects.filter(wishlist=wishlist).order_by('-added_at')
    
    context = {
        'wishlist_items': wishlist_items,
    }
    return render(request, 'store/wishlist.html', context)

@login_required
@require_POST
def toggle_wishlist(request):
    """AJAX endpoint to add/remove from wishlist"""
    product_id = request.POST.get('product_id')
    
    try:
        product = Product.objects.get(id=product_id)
        wishlist, created = Wishlist.objects.get_or_create(user=request.user)
        
        wishlist_item, created = WishlistItem.objects.get_or_create(
            wishlist=wishlist,
            product=product
        )
        
        if not created:
            wishlist_item.delete()
            message = 'Removed from wishlist'
            in_wishlist = False
        else:
            message = 'Added to wishlist'
            in_wishlist = True
        
        return JsonResponse({
            'success': True,
            'message': message,
            'in_wishlist': in_wishlist
        })
    except Product.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Product not found'})

@login_required
def checkout(request):
    """Enhanced checkout process"""
    cart = get_object_or_404(Cart, user=request.user)
    
    if not cart.items.exists():
        messages.error(request, 'Your cart is empty')
        return redirect('cart')
    
    addresses = request.user.addresses.all()
    
    if request.method == 'POST':
        # Process order
        address_id = request.POST.get('address_id')
        payment_method = request.POST.get('payment_method')
        
        if not address_id:
            messages.error(request, 'Please select a delivery address')
            return render(request, 'store/checkout.html', {'cart': cart, 'addresses': addresses})
        
        address = get_object_or_404(Address, id=address_id, user=request.user)
        
        # Create order
        order = Order.objects.create(
            user=request.user,
            total_amount=cart.total_amount,
            payment_method=payment_method,
            shipping_name=address.name,
            shipping_phone=address.phone,
            shipping_address_line_1=address.address_line_1,
            shipping_address_line_2=address.address_line_2,
            shipping_city=address.city,
            shipping_state=address.state,
            shipping_postal_code=address.postal_code,
            shipping_country=address.country,
        )
        
        # Create order items
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                price=cart_item.product.price
            )
        
        # Clear cart
        cart.items.all().delete()
        
        messages.success(request, f'Order #{order.order_id} placed successfully!')
        return redirect('order_detail', order_id=order.order_id)
    
    context = {
        'cart': cart,
        'addresses': addresses,
    }
    return render(request, 'store/checkout.html', context)

@login_required
def order_detail(request, order_id):
    """Order detail view"""
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    
    context = {
        'order': order,
    }
    return render(request, 'store/order_detail.html', context)

@login_required
def order_history(request):
    """User's order history"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'orders': orders,
    }
    return render(request, 'users/order_history.html', context)

@login_required
def profile(request):
    """User profile page"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    addresses = request.user.addresses.all()
    recent_orders = request.user.orders.all()[:5]
    
    context = {
        'profile': profile,
        'addresses': addresses,
        'recent_orders': recent_orders,
    }
    return render(request, 'users/profile.html', context)

@login_required
@require_POST
def add_review(request, product_id):
    """Add product review"""
    product = get_object_or_404(Product, id=product_id)
    
    # Check if user has already reviewed
    if Review.objects.filter(product=product, user=request.user).exists():
        messages.error(request, 'You have already reviewed this product')
        return redirect('product_detail', slug=product.slug)
    
    rating = int(request.POST.get('rating'))
    title = request.POST.get('title')
    comment = request.POST.get('comment')
    
    # Check if user has purchased this product
    has_purchased = OrderItem.objects.filter(
        order__user=request.user,
        product=product,
        order__status='delivered'
    ).exists()
    
    Review.objects.create(
        product=product,
        user=request.user,
        rating=rating,
        title=title,
        comment=comment,
        is_verified_purchase=has_purchased
    )
    
    messages.success(request, 'Review added successfully!')
    return redirect('product_detail', slug=product.slug)

#def register(request):
  #  """User registration"""
"""     if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}!')
            return redirect('login')
    else:
        form = UserCreationForm()
    
    return render(request, 'users/register.html', {'form': form}) """

def search_suggestions(request):
    """AJAX endpoint for search suggestions"""
    query = request.GET.get('q', '')
    
    if len(query) > 2:
        products = Product.objects.filter(
            Q(name__icontains=query) | Q(category__name__icontains=query),
            is_active=True
        )[:5]
        
        suggestions = [{'name': p.name, 'slug': p.slug} for p in products]
        return JsonResponse({'suggestions': suggestions})
    
    return JsonResponse({'suggestions': []})

def product_search(request):
    query = request.GET.get('q')
    # For now, just display the query
    context = {
        'query': query
    }
    return render(request, 'store/product_search.html', context)

# Add these missing views to your views.py file:

def login_view(request):
    """Custom login view"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'Logged in successfully!')
            next_url = request.GET.get('next', 'home')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password')
    return render(request, 'users/login.html')

def register_view(request):
    """User registration view"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)  # Use custom form instead
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}!')
            return redirect('login')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomUserCreationForm()  # Use custom form instead
    
    return render(request, 'users/register.html', {'form': form})

def logout_view(request):
    """Custom logout view"""
    logout(request)
    messages.success(request, 'You have been logged out successfully!')
    return redirect('home')

@login_required
def profile_view(request):
    """User profile page"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    addresses = request.user.addresses.all()
    recent_orders = request.user.orders.all()[:5]
    
    context = {
        'profile': profile,
        'addresses': addresses,
        'recent_orders': recent_orders,
    }
    return render(request, 'users/profile.html', context)

@login_required
def cart_detail(request):
    """Enhanced shopping cart view"""
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    context = {
        'cart': cart,
        'cart_items': cart.items.all(),
    }
    return render(request, 'store/cart.html', context)

@login_required
def cart_add(request, product_id):
    """Add item to cart (non-AJAX version)"""
    product = get_object_or_404(Product, id=product_id, is_active=True)
    quantity = int(request.POST.get('quantity', 1))
    
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, item_created = CartItem.objects.get_or_create(
        cart=cart, 
        product=product,
        defaults={'quantity': quantity}
    )
    
    if not item_created:
        cart_item.quantity += quantity
        cart_item.save()
    
    messages.success(request, f'{product.name} added to cart!')
    return redirect('product_detail', id=product.id, slug=product.slug)

@login_required
def cart_remove(request, product_id):
    """Remove item from cart"""
    try:
        cart = Cart.objects.get(user=request.user)
        cart_item = CartItem.objects.get(cart=cart, product_id=product_id)
        product_name = cart_item.product.name
        cart_item.delete()
        messages.success(request, f'{product_name} removed from cart!')
    except (Cart.DoesNotExist, CartItem.DoesNotExist):
        messages.error(request, 'Item not found in cart')
    
    return redirect('cart_detail')

# Also update your existing product_detail function to handle both id and slug:
def product_detail(request, id, slug):
    """Enhanced product detail with reviews and related products"""
    product = get_object_or_404(Product, id=id, slug=slug, is_active=True)
    reviews = product.reviews.filter(is_approved=True).order_by('-created_at')
    related_products = Product.objects.filter(
        category=product.category, 
        is_active=True
    ).exclude(id=product.id)[:4]
    
    # Check if user has purchased this product (for verified reviews)
    has_purchased = False
    user_review = None
    if request.user.is_authenticated:
        has_purchased = OrderItem.objects.filter(
            order__user=request.user, 
            product=product,
            order__status='delivered'
        ).exists()
        
        try:
            user_review = Review.objects.get(product=product, user=request.user)
        except Review.DoesNotExist:
            pass
    
    context = {
        'product': product,
        'reviews': reviews,
        'related_products': related_products,
        'has_purchased': has_purchased,
        'user_review': user_review,
    }
    return render(request, 'store/product_detail.html', context)