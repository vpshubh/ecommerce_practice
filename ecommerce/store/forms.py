from django import forms
from .models import Review
from .models import Category


class ProductFilterForm(forms.Form):
    SORT_CHOICES = [
        ('-created', 'Newest First'),
        ('price', 'Price: Low to High'),
        ('-price', 'Price: High to Low'),
        ('name', 'Name: A-Z'),
    ]

    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        empty_label="All Categories"
    )
    price_min = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={'placeholder': 'Min Price'})
    )
    price_max = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={'placeholder': 'Max Price'})
    )
    sort = forms.ChoiceField(
        choices=SORT_CHOICES,
        required=False,
        initial='-created'
    )
    
class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']