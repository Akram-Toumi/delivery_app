from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, HTML
from django.contrib.auth import get_user_model
from deliveries.models import Truck, DeliveryOrder
from .models import Route, RouteStop

User = get_user_model()

class RouteForm(forms.ModelForm):
    class Meta:
        model = Route
        fields = ['name', 'truck', 'driver', 'date', 'status']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['driver'].queryset = User.objects.filter(role='driver')
        self.fields['truck'].queryset = Truck.objects.filter(is_active=True)
        
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('name', css_class='form-group col-md-6'),
                Column('date', css_class='form-group col-md-6'),
            ),
            Row(
                Column('truck', css_class='form-group col-md-6'),
                Column('driver', css_class='form-group col-md-6'),
            ),
            'status',
            Submit('submit', 'Save Route', css_class='btn btn-primary')
        )

class RouteOptimizationForm(forms.Form):
    date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        help_text="Select the date for route optimization"
    )
    trucks = forms.ModelMultipleChoiceField(
        queryset=Truck.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple,
        help_text="Select trucks to include in optimization"
    )
    include_pending_orders = forms.BooleanField(
        initial=True,
        required=False,
        help_text="Include pending orders in optimization"
    )
    min_deliveries_per_truck = forms.IntegerField(
        initial=5,
        min_value=1,
        max_value=20,
        help_text="Minimum deliveries per truck"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'date',
            'trucks',
            'include_pending_orders',
            'min_deliveries_per_truck',
            Submit('optimize', 'Optimize Routes', css_class='btn btn-success')
        )

class RouteStopForm(forms.ModelForm):
    class Meta:
        model = RouteStop
        fields = ['route', 'delivery_order', 'stop_number', 'estimated_arrival_time', 'notes']
        widgets = {
            'estimated_arrival_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        route_id = kwargs.pop('route_id', None)
        super().__init__(*args, **kwargs)
        
        if route_id:
            self.fields['route'].initial = route_id
            self.fields['route'].widget = forms.HiddenInput()
            
            # Only show orders that aren't already in this route
            existing_order_ids = RouteStop.objects.filter(route_id=route_id).values_list('delivery_order_id', flat=True)
            self.fields['delivery_order'].queryset = DeliveryOrder.objects.exclude(
                id__in=existing_order_ids
            ).filter(status__in=['pending', 'assigned'])
        
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'route',
            Row(
                Column('delivery_order', css_class='form-group col-md-8'),
                Column('stop_number', css_class='form-group col-md-4'),
            ),
            'estimated_arrival_time',
            'notes',
            Submit('submit', 'Add Stop', css_class='btn btn-primary')
        )

class RouteStatusUpdateForm(forms.ModelForm):
    class Meta:
        model = Route
        fields = ['status']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'status',
            Submit('submit', 'Update Status', css_class='btn btn-primary')
        )