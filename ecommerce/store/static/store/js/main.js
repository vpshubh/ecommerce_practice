// DOM Ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize carousel
    initCarousel();
    
    // Initialize product tabs
    initProductTabs();
    
    // Add to cart functionality
    setupAddToCart();
    
    // Mobile menu toggle
    setupMobileMenu();
});

// Carousel Functionality
function initCarousel() {
    const slides = document.querySelectorAll('.carousel-slide');
    if (slides.length === 0) return;
    
    let currentSlide = 0;
    slides[currentSlide].classList.add('active');
    
    function nextSlide() {
        slides[currentSlide].classList.remove('active');
        currentSlide = (currentSlide + 1) % slides.length;
        slides[currentSlide].classList.add('active');
    }
    
    // Auto-rotate every 5 seconds
    setInterval(nextSlide, 5000);
}

// Product Tabs
function initProductTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabPanes = document.querySelectorAll('.tab-pane');
    
    if (tabBtns.length === 0) return;
    
    tabBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const tabId = this.getAttribute('data-tab');
            
            // Update active tab button
            tabBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            
            // Update active pane
            tabPanes.forEach(pane => pane.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            
            // Load content if not already loaded
            if (document.getElementById(tabId).innerHTML.trim() === '') {
                loadTabContent(tabId);
            }
        });
    });
    
    // Load initial tab content
    loadTabContent('trending');
}

function loadTabContent(tabId) {
    const url = `/api/products/${tabId}/`;
    const pane = document.getElementById(tabId);
    
    fetch(url)
        .then(response => response.json())
        .then(data => {
            pane.innerHTML = renderProducts(data.products);
        })
        .catch(error => {
            pane.innerHTML = '<p>Error loading products. Please try again.</p>';
            console.error('Error:', error);
        });
}

function renderProducts(products) {
    if (products.length === 0) return '<p>No products found.</p>';
    
    return `
        <div class="products-grid">
            ${products.map(product => `
                <div class="product-card">
                    <div class="product-badge">
                        ${product.discount_percent ? `<span class="discount-badge">-${product.discount_percent}%</span>` : ''}
                        ${product.is_new ? '<span class="new-badge">New</span>' : ''}
                    </div>
                    <a href="/product/${product.id}/" class="product-image">
                        <img src="${product.image}" alt="${product.name}">
                    </a>
                    <div class="product-info">
                        <h3 class="product-title">${product.name}</h3>
                        <div class="product-rating">
                            <div class="stars">
                                ${'<i class="fas fa-star"></i>'.repeat(Math.floor(product.rating))}
                                ${product.rating % 1 >= 0.5 ? '<i class="fas fa-star-half-alt"></i>' : ''}
                                ${'<i class="far fa-star"></i>'.repeat(5 - Math.ceil(product.rating))}
                            </div>
                            <span class="rating-count">(${product.review_count})</span>
                        </div>
                        <div class="product-price">
                            ${product.discount_price ? `
                                <span class="original-price">$${product.price}</span>
                                <span class="current-price">$${product.discount_price}</span>
                            ` : `
                                <span class="current-price">$${product.price}</span>
                            `}
                        </div>
                        <button class="add-to-cart" data-product-id="${product.id}">
                            Add to Cart
                        </button>
                    </div>
                </div>
            `).join('')}
        </div>
    `;
}

// Add to Cart Functionality
function setupAddToCart() {
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('add-to-cart') || 
            e.target.closest('.add-to-cart')) {
            const btn = e.target.classList.contains('add-to-cart') ? 
                e.target : e.target.closest('.add-to-cart');
            const productId = btn.getAttribute('data-product-id');
            
            addToCart(productId, btn);
        }
    });
}

function addToCart(productId, btn) {
    const originalText = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Adding...';
    btn.disabled = true;
    
    fetch('/cart/add/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify({
            product_id: productId,
            quantity: 1
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            btn.innerHTML = '<i class="fas fa-check"></i> Added!';
            updateCartCount(data.cart_count);
            
            // Show cart notification
            showNotification('Product added to cart');
            
            // Reset button after delay
            setTimeout(() => {
                btn.innerHTML = originalText;
                btn.disabled = false;
            }, 2000);
        } else {
            btn.innerHTML = 'Error';
            setTimeout(() => {
                btn.innerHTML = originalText;
                btn.disabled = false;
            }, 2000);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        btn.innerHTML = 'Error';
        setTimeout(() => {
            btn.innerHTML = originalText;
            btn.disabled = false;
        }, 2000);
    });
}

function updateCartCount(count) {
    const cartCountElements = document.querySelectorAll('.cart-count');
    cartCountElements.forEach(el => {
        el.textContent = count;
    });
}

function showNotification(message) {
    const notification = document.createElement('div');
    notification.className = 'notification';
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas fa-check-circle"></i>
            <span>${message}</span>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);
    
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);
}

// Mobile Menu
function setupMobileMenu() {
    const menuToggle = document.querySelector('.mobile-menu-toggle');
    if (!menuToggle) return;
    
    menuToggle.addEventListener('click', function() {
        document.body.classList.toggle('mobile-menu-open');
    });
}

// Helper Functions
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}