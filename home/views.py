from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db import models
from datetime import date, timedelta
from .models import UserProfile, ChickStock, ChickRequest, Sale, Stock, Request, Farmer
from .forms import UserRegistrationForm, FarmerProfileForm, ChickRequestForm, ChickStockForm

def home(request):
    """Home page with basic statistics"""
    context = {
        'total_farmers': UserProfile.objects.filter(role='farmer').count(),
        'pending_requests': ChickRequest.objects.filter(status='pending').count(),
        'total_stock': sum(stock.quantity for stock in ChickStock.objects.all()),
    }
    return render(request, 'home/home.html', context)

def register_farmer(request):
    """Register new farmer"""
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        profile_form = FarmerProfileForm(request.POST)
        
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.role = 'farmer'
            profile.save()
            
            messages.success(request, 'Registration successful! You can now login.')
            return redirect('login')
    else:
        user_form = UserRegistrationForm()
        profile_form = FarmerProfileForm()
    
    return render(request, 'home/register_farmer.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })

@login_required
def dashboard(request):
    """Route users to role-specific dashboards"""
    try:
        user_profile = request.user.userprofile
        
        if user_profile.role == 'manager':
            return manager_dashboard(request)
        elif user_profile.role == 'sales_rep':
            return sales_dashboard(request)
        elif user_profile.role == 'farmer':
            return farmer_dashboard(request)
        else:
            messages.warning(request, 'Your account role is not set. Please contact an administrator.')
            return redirect('home')
            
    except UserProfile.DoesNotExist:
        messages.error(request, 'User profile not found. Please complete your registration.')
        return redirect('register_farmer')

@login_required
def farmer_dashboard(request):
    """Main farmer dashboard"""
    try:
        user_profile = request.user.userprofile
        
        if user_profile.role != 'farmer':
            messages.warning(request, 'This dashboard is for farmers only.')
            return redirect('home')
        
        # Get all requests for this farmer
        my_requests = ChickRequest.objects.filter(farmer=user_profile).order_by('-created_at')
        
        # Check if farmer can make a new request (once every 4 months)
        four_months_ago = date.today() - timedelta(days=120)
        can_request = not ChickRequest.objects.filter(
            farmer=user_profile,
            created_at__date__gte=four_months_ago
        ).exists()
        
        # Calculate statistics for the dashboard
        total_requests = my_requests.count()
        pending_requests = my_requests.filter(status='pending').count()
        approved_requests = my_requests.filter(status='approved').count()
        completed_sales = my_requests.filter(status='sold').count()
        
        # Calculate total chicks (sum of all approved/completed requests)
        total_chicks = sum(
            request.quantity_requested for request in my_requests.filter(
                status__in=['approved', 'sold']
            )
        )
        
        # Calculate next request date if needed
        latest_request = my_requests.first()
        next_request_date = None
        if latest_request and not can_request:
            next_request_date = latest_request.created_at.date() + timedelta(days=120)
        
        context = {
            'user_profile': user_profile,
            'requests': my_requests,
            'total_requests': total_requests,
            'pending_requests': pending_requests,
            'approved_requests': approved_requests,
            'completed_sales': completed_sales,
            'total_chicks': total_chicks,
            'can_request': can_request,
            'next_request_date': next_request_date,
        }
        return render(request, 'home/farmer_dashboard.html', context)
            
    except UserProfile.DoesNotExist:
        messages.error(request, 'User profile not found. Please complete your registration.')
        return redirect('register_farmer')

@login_required
def manager_dashboard(request):
    """Manager dashboard for reviewing requests and managing stock"""
    try:
        user_profile = request.user.userprofile
        
        if user_profile.role != 'manager':
            messages.warning(request, 'Access denied. Manager role required.')
            return redirect('dashboard')
            
        pending_requests = ChickRequest.objects.filter(status='pending').order_by('-created_at')
        stock_items = ChickStock.objects.all().order_by('-date_added')
        recent_approvals = ChickRequest.objects.filter(
            approved_by=user_profile,
            status__in=['approved', 'sold']
        ).order_by('-approval_date')[:10]
        
        context = {
            'user_profile': user_profile,
            'pending_requests': pending_requests,
            'stock_items': stock_items,
            'recent_approvals': recent_approvals,
        }
        return render(request, 'home/manager_dashboard.html', context)
        
    except UserProfile.DoesNotExist:
        messages.error(request, 'User profile not found.')
        return redirect('register_farmer')

@login_required
def sales_dashboard(request):
    """Sales representative dashboard"""
    try:
        user_profile = request.user.userprofile
        
        if user_profile.role != 'sales_rep':
            messages.warning(request, 'Access denied. Sales representative role required.')
            return redirect('dashboard')
            
        approved_requests = ChickRequest.objects.filter(status='approved').order_by('-approval_date')
        my_sales = Sale.objects.filter(completed_by=user_profile).order_by('-sale_date')[:10]
        
        # Calculate total revenue
        total_revenue = sum(sale.total_amount for sale in my_sales)
        
        context = {
            'user_profile': user_profile,
            'approved_requests': approved_requests,
            'my_sales': my_sales,
            'total_revenue': total_revenue,
        }
        return render(request, 'home/sales_dashboard.html', context)
        
    except UserProfile.DoesNotExist:
        messages.error(request, 'User profile not found.')
        return redirect('register_farmer')

@login_required
def make_request(request):
    """Create new chick request"""
    user_profile = get_object_or_404(UserProfile, user=request.user)
    
    if user_profile.role != 'farmer':
        messages.error(request, 'Only farmers can make chick requests')
        return redirect('dashboard')
    
    # Check if farmer can make a request
    four_months_ago = date.today() - timedelta(days=120)
    if ChickRequest.objects.filter(farmer=user_profile, created_at__date__gte=four_months_ago).exists():
        messages.error(request, 'You can only make one request every 4 months')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = ChickRequestForm(request.POST)
        if form.is_valid():
            chick_request = form.save(commit=False)
            chick_request.farmer = user_profile
            
            # Calculate total amount
            chick_request.total_amount = chick_request.quantity_requested * 1650  # Fixed price per chick
            chick_request.save()
            
            messages.success(request, f'Request for {chick_request.quantity_requested} {chick_request.get_chick_type_display()} chicks submitted successfully!')
            return redirect('dashboard')
    else:
        form = ChickRequestForm()
    
    return render(request, 'home/make_request.html', {'form': form})

@login_required
def edit_profile(request):
    """Edit user profile"""
    user_profile = get_object_or_404(UserProfile, user=request.user)
    
    if request.method == 'POST':
        profile_form = FarmerProfileForm(request.POST, instance=user_profile)
        if profile_form.is_valid():
            profile_form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('dashboard')
    else:
        profile_form = FarmerProfileForm(instance=user_profile)
    
    return render(request, 'home/edit_profile.html', {'profile_form': profile_form})

@login_required
def manage_stock(request):
    """Manage chick stock (Manager only)"""
    user_profile = get_object_or_404(UserProfile, user=request.user)
    
    if user_profile.role != 'manager':
        messages.error(request, 'Access denied. Manager role required.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = ChickStockForm(request.POST)
        if form.is_valid():
            stock = form.save(commit=False)
            stock.added_by = user_profile
            stock.save()
            messages.success(request, f'Added {stock.quantity} {stock.get_chick_type_display()} chicks to stock')
            return redirect('manage_stock')
    else:
        form = ChickStockForm()
    
    stock_items = ChickStock.objects.all().order_by('-date_added')
    
    return render(request, 'home/manage_stock.html', {
        'form': form,
        'stock_items': stock_items
    })

@login_required
def approve_request(request, request_id):
    """Approve chick request (Manager only)"""
    user_profile = get_object_or_404(UserProfile, user=request.user)
    
    if user_profile.role != 'manager':
        messages.error(request, 'Access denied. Manager role required.')
        return redirect('dashboard')
    
    chick_request = get_object_or_404(ChickRequest, id=request_id)
    
    if chick_request.status != 'pending':
        messages.warning(request, 'This request has already been processed.')
        return redirect('dashboard')
    
    # Check if there's enough stock
    # Map ChickRequest fields to ChickStock chick_type format
    stock_chick_type = f"{chick_request.chick_type}_{chick_request.breed_type}"
    
    available_stock = ChickStock.objects.filter(
        chick_type=stock_chick_type,
        is_available=True
    ).aggregate(total=models.Sum('quantity'))['total'] or 0
    
    if available_stock >= chick_request.quantity_requested:
        chick_request.status = 'approved'
        chick_request.approved_by = user_profile
        chick_request.approval_date = timezone.now()
        chick_request.save()
        
        # Reduce stock
        remaining_needed = chick_request.quantity_requested
        stock_items = ChickStock.objects.filter(
            chick_type=stock_chick_type,
            is_available=True
        ).order_by('date_added')
        
        for stock in stock_items:
            if remaining_needed <= 0:
                break
            if stock.quantity >= remaining_needed:
                stock.quantity -= remaining_needed
                remaining_needed = 0
                if stock.quantity > 0:
                    stock.save()
                else:
                    stock.delete()
            else:
                remaining_needed -= stock.quantity
                stock.delete()
        
        messages.success(request, f'Request approved for {chick_request.farmer.user.get_full_name()}')
    else:
        messages.error(request, f'Insufficient stock. Available: {available_stock}, Requested: {chick_request.quantity_requested}')
    
    return redirect('dashboard')

@login_required
def reject_request(request, request_id):
    """Reject chick request (Manager only)"""
    user_profile = get_object_or_404(UserProfile, user=request.user)
    
    if user_profile.role != 'manager':
        messages.error(request, 'Access denied. Manager role required.')
        return redirect('dashboard')
    
    chick_request = get_object_or_404(ChickRequest, id=request_id)
    
    if chick_request.status != 'pending':
        messages.warning(request, 'This request has already been processed.')
        return redirect('dashboard')
    
    # Update request status to rejected
    chick_request.status = 'rejected'
    chick_request.approved_by = user_profile  # Track who rejected it
    chick_request.approval_date = timezone.now()
    chick_request.save()
    
    messages.warning(request, f'Request rejected for {chick_request.farmer.user.get_full_name()}')
    return redirect('dashboard')

@login_required
def complete_sale(request, request_id):
    """Complete sale (Sales rep only)"""
    user_profile = get_object_or_404(UserProfile, user=request.user)
    
    if user_profile.role != 'sales_rep':
        messages.error(request, 'Access denied. Sales representative role required.')
        return redirect('dashboard')
    
    chick_request = get_object_or_404(ChickRequest, id=request_id)
    
    if chick_request.status != 'approved':
        messages.warning(request, 'This request is not approved for sale.')
        return redirect('dashboard')
    
    # Create sale record
    sale = Sale.objects.create(
        request=chick_request,
        completed_by=user_profile,
        total_amount=chick_request.total_amount
    )
    
    # Update request status
    chick_request.status = 'sold'
    chick_request.save()
    
    messages.success(request, f'Sale completed for {chick_request.farmer.user.get_full_name()}. Amount: UGx {chick_request.total_amount:,}')
    return redirect('dashboard')

@login_required
def request_status(request, request_id):
    """API endpoint for request status"""
    try:
        chick_request = ChickRequest.objects.get(id=request_id, farmer=request.user.userprofile)
        return JsonResponse({
            'status': chick_request.status,
            'status_display': chick_request.get_status_display(),
            'approval_date': chick_request.approval_date.isoformat() if chick_request.approval_date else None,
        })
    except ChickRequest.DoesNotExist:
        return JsonResponse({'error': 'Request not found'}, status=404)
