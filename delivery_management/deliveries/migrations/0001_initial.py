# Generated by Django 5.2.3 on 2025-06-29 18:27

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('company_name', models.CharField(blank=True, max_length=200)),
                ('address', models.TextField()),
                ('latitude', models.DecimalField(decimal_places=8, max_digits=10)),
                ('longitude', models.DecimalField(decimal_places=8, max_digits=11)),
                ('phone', models.CharField(max_length=15)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='DeliveryOrder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order_number', models.CharField(max_length=20, unique=True)),
                ('weight_kg', models.IntegerField(validators=[django.core.validators.MinValueValidator(1)])),
                ('priority', models.CharField(choices=[('low', 'Low'), ('normal', 'Normal'), ('high', 'High'), ('urgent', 'Urgent')], default='normal', max_length=10)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('assigned', 'Assigned'), ('in_transit', 'In Transit'), ('delivered', 'Delivered'), ('failed', 'Failed'), ('cancelled', 'Cancelled')], default='pending', max_length=20)),
                ('pickup_address', models.TextField()),
                ('pickup_latitude', models.DecimalField(decimal_places=8, max_digits=10)),
                ('pickup_longitude', models.DecimalField(decimal_places=8, max_digits=11)),
                ('delivery_address', models.TextField()),
                ('delivery_latitude', models.DecimalField(decimal_places=8, max_digits=10)),
                ('delivery_longitude', models.DecimalField(decimal_places=8, max_digits=11)),
                ('requested_delivery_date', models.DateField()),
                ('estimated_delivery_time', models.DateTimeField(blank=True, null=True)),
                ('actual_delivery_time', models.DateTimeField(blank=True, null=True)),
                ('special_instructions', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='deliveries.customer')),
            ],
        ),
        migrations.CreateModel(
            name='Truck',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('license_plate', models.CharField(max_length=20, unique=True)),
                ('capacity_kg', models.IntegerField(default=1500)),
                ('is_active', models.BooleanField(default=True)),
                ('current_location_lat', models.DecimalField(blank=True, decimal_places=8, max_digits=10, null=True)),
                ('current_location_lon', models.DecimalField(blank=True, decimal_places=8, max_digits=11, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('driver', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Route',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('date', models.DateField()),
                ('total_distance_km', models.DecimalField(decimal_places=2, default=0, max_digits=8)),
                ('estimated_duration_minutes', models.IntegerField(default=0)),
                ('is_optimized', models.BooleanField(default=False)),
                ('status', models.CharField(choices=[('planned', 'Planned'), ('active', 'Active'), ('completed', 'Completed'), ('cancelled', 'Cancelled')], default='planned', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('driver', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('truck', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='deliveries.truck')),
            ],
        ),
        migrations.CreateModel(
            name='RouteStop',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stop_number', models.IntegerField()),
                ('estimated_arrival_time', models.DateTimeField(blank=True, null=True)),
                ('actual_arrival_time', models.DateTimeField(blank=True, null=True)),
                ('is_completed', models.BooleanField(default=False)),
                ('notes', models.TextField(blank=True)),
                ('delivery_order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='deliveries.deliveryorder')),
                ('route', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stops', to='deliveries.route')),
            ],
            options={
                'ordering': ['stop_number'],
                'unique_together': {('route', 'stop_number')},
            },
        ),
    ]
