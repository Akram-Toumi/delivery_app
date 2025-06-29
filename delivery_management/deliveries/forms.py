from django import forms
from django.contrib.auth import get_user_model
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, HTML
from .models import DeliveryOrder, Customer, Truck, Route

User = get_user_model()

class DeliveryOrderForm(forms.ModelForm):
    class Meta:
        model = DeliveryOrder
        fields = [
            'customer', 'weight_kg', 'priority',
            'pickup_address', 'pickup_latitude', 'pickup_longitude',
            'delivery_address', 'delivery_latitude', 'delivery_longitude',
            'requested_delivery_date', 'special_instructions'
        ]
        widgets = {
            'pickup_latitude': forms.HiddenInput(),
            'pickup_longitude': forms.HiddenInput(),
            'delivery_latitude': forms.HiddenInput(),
            'delivery_longitude': forms.HiddenInput(),
            'requested_delivery_date': forms.DateInput(attrs={'type': 'date'}),
            'pickup_address': forms.Textarea(attrs={'rows': 3}),
            'delivery_address': forms.Textarea(attrs={'rows': 3}),
            'special_instructions': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('customer', css_class='form-group col-md-6'),
                Column('weight_kg', css_class='form-group col-md-3'),
                Column('priority', css_class='form-group col-md-3'),
            ),
            Row(
                Column('pickup_address', css_class='form-group col-md-6'),
                Column('delivery_address', css_class='form-group col-md-6'),
            ),
            'pickup_latitude',
            'pickup_longitude',
            'delivery_latitude',
            'delivery_longitude',
            Row(
                Column('requested_delivery_date', css_class='form-group col-md-6'),
            ),
            'special_instructions',
            Submit('submit', 'Create Delivery Order', css_class='btn btn-primary')
        )

class RouteOptimizationForm(forms.Form):
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    trucks = forms.ModelMultipleChoiceField(
        queryset=Truck.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple
    )
    include_pending_orders = forms.BooleanField(initial=True, required=False)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'date',
            'trucks',
            'include_pending_orders',
            Submit('optimize', 'Optimize Routes', css_class='btn btn-success')
        )

class TruckForm(forms.ModelForm):
    class Meta:
        model = Truck
        fields = ['license_plate', 'capacity_kg', 'driver', 'is_active']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['driver'].queryset = User.objects.filter(role='driver')
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('license_plate', css_class='form-group col-md-6'),
                Column('capacity_kg', css_class='form-group col-md-6'),
            ),
            Row(
                Column('driver', css_class='form-group col-md-6'),
                Column('is_active', css_class='form-group col-md-6'),
            ),
            Submit('submit', 'Save Truck', css_class='btn btn-primary')
        )