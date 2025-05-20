from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, Category
from .forms import ReviewForm, ProductFilterForm
from django.db.models import Q


def home(request):
    featured_products = Product.objects.filter(available=True)[:8]
    categories = Category.objects.all()
    return render(request, 'store/home.html', {
        'featured_products': featured_products,
        'categories': categories
    })

def product_list(request, category_slug=None):
    form = ProductFilterForm(request.GET or None)
    products = Product.objects.filter(available=True).select_related('category')
    
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)
    
    if form.is_valid():
        if form.cleaned_data['category']:
            products = products.filter(category=form.cleaned_data['category'])
        if form.cleaned_data['price_min']:
            products = products.filter(price__gte=form.cleaned_data['price_min'])
        if form.cleaned_data['price_max']:
            products = products.filter(price__lte=form.cleaned_data['price_max'])
        if form.cleaned_data['sort']:
            products = products.order_by(form.cleaned_data['sort'])
    
    return render(request, 'store/product_list.html', {
        'products': products,
        'form': form,
        'category': category if category_slug else None
    })
def product_detail(request, id, slug):
    product = get_object_or_404(Product, id=id, slug=slug, available=True)
    reviews = product.reviews.all()
    
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()
            return redirect(product.get_absolute_url())
    else:
        form = ReviewForm()
    
    return render(request, 'store/product_detail.html', {
        'product': product,
        'reviews': reviews,
        'form': form
    })
def cart(request):
    return render(request, 'store/cart.html')

def checkout(request):
    return render(request, 'store/checkout.html')


def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1))
    cart.add(product=product, quantity=quantity)
    return redirect('cart_detail')

def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    return redirect('cart_detail')

def cart_detail(request):
    cart = Cart(request)
    return render(request, 'store/cart.html', {'cart': cart})

def product_search(request):
    query = request.GET.get('q', '')
    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query),
            available=True
        )
    else:
        products = Product.objects.none()
    
    return render(request, 'store/search_results.html', {
        'products': products,
        'query': query
    })