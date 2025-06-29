from django import forms
from django.db.models import Q
from deliveries.models import DeliveryOrder
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit

class ManualOptimizationForm(forms.Form):
    date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        help_text="Date for the delivery routes"
    )
    num_trucks = forms.IntegerField(
        min_value=1,
        max_value=10,
        initial=3,
        help_text="Number of trucks to use (each with 1500kg capacity)"
    )
    orders = forms.ModelMultipleChoiceField(
        queryset=DeliveryOrder.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        help_text="Select orders to include in optimization"
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        
        # Filter orders based on user role
        if user.role in ['admin', 'manager']:
            self.fields['orders'].queryset = DeliveryOrder.objects.filter(
                Q(status='pending') | Q(status='assigned')
            ).order_by('-requested_delivery_date')
        else:
            self.fields['orders'].queryset = DeliveryOrder.objects.filter(
                customer__user=user,
                status__in=['pending', 'assigned']
            ).order_by('-requested_delivery_date')
        
        # Setup crispy forms
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'date',
            'num_trucks',
            'orders',
            Submit('submit', 'Optimize Routes', css_class='btn-success')
        )