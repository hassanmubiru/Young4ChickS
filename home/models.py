from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import date

# Create your models here.
class UserProfile(AbstractUser):
    ROLE_CHOICES = [
        ('farmer', 'Farmer'),
        ('sales_rep', 'Sales Representative'),
        ('manager', 'Manager'),
    ]
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='farmer')
    age = models.PositiveIntegerField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, null=True, blank=True)
    nin_number = models.CharField(max_length=30, unique=True, null=True, blank=True)
    contact = models.CharField(max_length=15, null=True, blank=True)
    recommender_name = models.CharField(max_length=50, null=True, blank=True)
    recommender_nin = models.CharField(max_length=30, null=True, blank=True)
    is_salesagent = models.BooleanField(default=False)
    is_manager = models.BooleanField(default=False)
    phone = models.CharField(max_length=50, unique=True, null=True, blank=True)
    title = models.CharField(max_length=30, null=True, blank=True)

    def __str__(self):
        return f"{self.get_full_name()} ({self.role})"

    class Meta:
        db_table = "farmer_users"
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

class ChickStock(models.Model):
    CHICK_TYPE_CHOICES = [
        ('broiler_local', 'Broiler Local'),
        ('broiler_exotic', 'Broiler Exotic'),
        ('layer_local', 'Layer Local'),
        ('layer_exotic', 'Layer Exotic'),
    ]
    
    chick_type = models.CharField(max_length=20, choices=CHICK_TYPE_CHOICES)
    quantity = models.PositiveIntegerField()
    age_in_days = models.PositiveIntegerField(default=0)
    date_added = models.DateTimeField(auto_now_add=True)
    added_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, related_name='added_stock')
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.get_chick_type_display()} - {self.quantity} chicks"

    class Meta:
        ordering = ['-date_added']

class ChickRequest(models.Model):
    CHICK_TYPE_CHOICES = [
        ('broiler', 'Broiler'),
        ('layer', 'Layer'),
    ]
    BREED_TYPE_CHOICES = [
        ('local', 'Local'),
        ('exotic', 'Exotic'),
    ]
    FARMER_TYPE_CHOICES = [
        ('starter', 'Starter'),
        ('returning', 'Returning'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('sold', 'Sold'),
    ]
    
    farmer = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='chick_requests')
    chick_type = models.CharField(max_length=20, choices=CHICK_TYPE_CHOICES)
    breed_type = models.CharField(max_length=10, choices=BREED_TYPE_CHOICES)
    quantity_requested = models.PositiveIntegerField()
    farmer_type = models.CharField(max_length=15, choices=FARMER_TYPE_CHOICES)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_requests')
    approval_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Request by {self.farmer.get_full_name()} - {self.status}"

    class Meta:
        ordering = ['-created_at']

class Sale(models.Model):
    request = models.OneToOneField(ChickRequest, on_delete=models.CASCADE, related_name='sale')
    completed_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, related_name='completed_sales')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    sale_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Sale for {self.request.farmer.get_full_name()} - UGx {self.total_amount}"

    class Meta:
        ordering = ['-sale_date']

# Keep the original models for backward compatibility if needed
class Stock(models.Model):
    CHICK_TYPE_CHOICES = [
        ('Broiler', 'Broiler'),
        ('Layer', 'Layer')
    ]
    CHICK_BREED_CHOICES = [
        ('Local', 'Local'),
        ('Exotic', 'Exotic')
    ]

    batch_name = models.CharField(max_length=255, unique=True) 
    quantity = models.PositiveIntegerField()
    date_added = models.DateField(auto_now_add=True)
    chick_type = models.CharField(max_length=20, choices=CHICK_TYPE_CHOICES)
    chick_breed = models.CharField(max_length=20, choices=CHICK_BREED_CHOICES)
    price = models.PositiveIntegerField(primary_key=True)
    registered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    chicks_age = models.PositiveIntegerField()

    def __str__(self):
        return self.batch_name

class Feedstock(models.Model):
    FEEDS_TYPE_CHOICES = [
        ('Starter Feeds', 'Starter Feeds'),
        ('Grower Feeds', 'Grower Feeds'),
        ('Layer Feeds', 'Layer Feeds'),
        ('Broiler Feeds', 'Broiler Feeds')
    ]
    FEEDS_BRAND_CHOICES = [
        ('Unga Millers (U) Ltd', 'Unga Millers (U) Ltd'),
        ('Ugachick Poultry Breeders Ltd', 'Ugachick Poultry Breeders Ltd'),
        ('Kaffiika Animal Feeds', 'Kaffiika Animal Feeds'),
        ('Biyinzika Poultry International Limited', 'Biyinzika Poultry International Limited')
    ]

    feeds_name = models.CharField(max_length=50)
    quantity = models.PositiveIntegerField()
    unit_price = models.PositiveIntegerField()
    cost_price = models.PositiveIntegerField()
    feeds_type = models.CharField(max_length=30, choices=FEEDS_TYPE_CHOICES)
    feeds_brand = models.CharField(max_length=50, choices=FEEDS_BRAND_CHOICES)
    feeds_supplier = models.CharField(max_length=50)
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.feeds_name

class Farmer(models.Model):
    FARMER_TYPE_CHOICES = [
        ('Starter', 'Starter'),
        ('Returning', 'Returning')
    ]
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female')
    ]

    fullname = models.CharField(max_length=50)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, null=True)
    nin = models.CharField(max_length=30, unique=True)
    recommender_name = models.CharField(max_length=50)
    recommender_nin = models.CharField(max_length=30)
    tel_number = models.CharField(max_length=15)
    dob = models.DateField()
    farmer_type = models.CharField(max_length=15, choices=FARMER_TYPE_CHOICES)

    def __str__(self):
        return self.fullname

    @property
    def age(self):
        today = date.today()
        return today.year - self.dob.year - ((today.month, today.day) < (self.dob.month, self.dob.day))

class Request(models.Model):
    CHICK_TYPE_CHOICES = [
        ('Broiler', 'Broiler'),
        ('Layer', 'Layer')
    ]
    CHICK_BREED_CHOICES = [
        ('Local', 'Local'),
        ('Exotic', 'Exotic')
    ]
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected')
    ]
    FEEDS_NEEDED_CHOICES = [
        ('Yes', 'Yes'),
        ('No', 'No')
    ]
    DELIVERED_CHOICES = [
        ('Yes', 'Yes'),
        ('No', 'No')
    ]

    farmer = models.ForeignKey(Farmer, on_delete=models.SET_NULL, null=True)
    chick_type = models.CharField(max_length=20, choices=CHICK_TYPE_CHOICES)
    chick_breed = models.CharField(max_length=15, choices=CHICK_BREED_CHOICES)
    quantity = models.PositiveIntegerField()
    date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='Pending')
    feeds_needed = models.CharField(max_length=10, choices=FEEDS_NEEDED_CHOICES)
    feeds_quantity = models.PositiveIntegerField(null=True, blank=True)
    chicks_period = models.PositiveIntegerField()
    delivered = models.CharField(max_length=10, choices=DELIVERED_CHOICES, default='No')

    def __str__(self):
        return f"Request by {self.farmer.fullname} - {self.status}"