from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from .models import User, UserTrustScore


def register_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        phone = request.POST.get("phone")
        member_id = request.POST.get("member_id")
        password = request.POST.get("password")

        # Basic validation
        if not username or not phone or not member_id or not password:
            return render(request, 'register.html', {
                'error': 'All fields are required.',
                'username': username,
                'phone': phone,
                'member_id': member_id,
            })

        if len(password) < 6:
            return render(request, 'register.html', {
                'error': 'Password must be at least 6 characters.',
                'username': username,
                'phone': phone,
                'member_id': member_id,
            })

        if User.objects.filter(username=username).exists():
            return render(request, 'register.html', {
                'error': 'Username already exists.',
                'username': username,
                'phone': phone,
                'member_id': member_id,
            })

        if User.objects.filter(phone=phone).exists():
            return render(request, 'register.html', {
                'error': 'Phone number already registered.',
                'username': username,
                'phone': phone,
                'member_id': member_id,
            })

        if User.objects.filter(member_id=member_id).exists():
            return render(request, 'register.html', {
                'error': 'Member ID already registered.',
                'username': username,
                'phone': phone,
                'member_id': member_id,
            })

        user = User.objects.create_user(
            username=username,
            phone=phone,
            member_id=member_id,
            password=password
        )
        UserTrustScore.objects.create(user=user)

        return redirect('login')

    return render(request, 'register.html')


@login_required
def create_user_view(request):
    if not request.user.is_staff:
        raise PermissionDenied()

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        member_id = request.POST.get('member_id')
        password = request.POST.get('password')
        is_staff = request.POST.get('is_staff') == 'on'

        if User.objects.filter(username=username).exists():
            return render(request, 'create_user.html', {'error': 'Username already exists'})
        if User.objects.filter(member_id=member_id).exists():
            return render(request, 'create_user.html', {'error': 'Member ID already exists'})
        if User.objects.filter(phone=phone).exists():
            return render(request, 'create_user.html', {'error': 'Phone number already exists'})

        user = User.objects.create_user(
            username=username,
            email=email,
            phone=phone,
            member_id=member_id,
            password=password,
            is_staff=is_staff
        )
        UserTrustScore.objects.create(user=user)
        return redirect('dashboard')

    return render(request, 'create_user.html')


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            UserTrustScore.objects.get_or_create(user=user)
            return redirect('dashboard')
        else:
            return render(request, 'login.html', {'error': 'Invalid login'})

    return render(request, 'login.html')


def selflogin_view(request):
    """Allow login using phone number and member_id (both required).

    NOTE: This bypasses password authentication and should be used only
    in trusted/self-service environments or paired with additional
    verification (OTP) in production.
    """
    if request.method == 'POST':
        phone = request.POST.get('phone', '').strip()
        member_id = request.POST.get('member_id', '').strip()

        if not phone or not member_id:
            return render(request, 'selflogin.html', {'error': 'Phone and Member ID are required.'})

        try:
            user = User.objects.get(phone=phone, member_id=member_id)
        except User.DoesNotExist:
            return render(request, 'selflogin.html', {'error': 'No matching user found.'})

        # Mark backend so Django accepts this user for login
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(request, user)
        UserTrustScore.objects.get_or_create(user=user)
        return redirect('dashboard')

    return render(request, 'selflogin.html')


def logout_view(request):
    logout(request)
    return redirect('login')