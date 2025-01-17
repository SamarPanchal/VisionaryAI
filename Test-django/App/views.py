from django.shortcuts import render, redirect, HttpResponse
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.core.mail import send_mail
from django.conf import settings
from App.models import Profile 
from django.contrib.auth.decorators import login_required
from App import ai_file
from Test import settings as setting
import uuid
import datetime
from datetime import timedelta
import stripe
from django.utils.timezone import now
from django.http import JsonResponse

website_domain = '127.0.0.1:8000'


plans = {
    'free': 0.00,
    'basic': 2.99,
    'pro': 5.99 ,
    'None': None
}

def home_page(request):
    return render(request, "index.html")

        

@login_required
def subscription_success(request):
    return render(request, "subscription_success.html")


@login_required
def subscription_status(request):
    profile = Profile.objects.get(user=request.user)
    subscription_end_date = profile.subscription_datetime or now()
    
    # Calculate the time remaining
    time_remaining = max(subscription_end_date - now(), timedelta(0))
    print(time_remaining)
    
    if request.method == 'POST':
        profile.subscription_plan = 'Free'
        profile.subscription_datetime = str(now())
        profile.image_left = 0
        profile.save()
        messages.success(request, f"Successfully cancled the subscription")
        return redirect('/dashboard')
    
    return render(request, 'subscription_status.html', {
        'subscription_end_date': subscription_end_date.strftime('%B %d, %Y %H:%M:%S'),
        'time_remaining': str(time_remaining).split('.')[0]  # Removes microseconds
    })
    
@login_required
def subscription_cancelled(request):
    messages.error(request, "Your subscription was cancelled. Please try again.")
    return redirect('/pricing/None/')

def subscription_page(request, plan):
    context = {'plan': plan}
    if request.user.is_anonymous:
        context["owned_plan"] = 'Free'
        if request.method == 'POST':
            messages.error(request, "Please login to subscribe...")
            return redirect('/login')
    else:
        profile = Profile.objects.get(user=request.user)
        context["owned_plan"] = str(profile.subscription_plan)
        if request.method == 'POST':
                if profile.subscription_plan == 'Free':
                    if plan not in plans:
                        messages.error(request, "Invalid subscription plan selected.")
                        return redirect('/dashboard')
                    elif plan == 'free':
                        messages.success(request, "You are now subscribed to the Free Plan.")
                        return redirect('/dashboard')
                    else:
                        context["owned_plan"] = str(profile.subscription_plan)
                        return redirect(f'/payment/{plan}')
                else:
                    return redirect('/subscription_status')
    return render(request, "subscription.html", context)


def change_password(request, token):
    context = {'token': token}
    try:
        profile = Profile.objects.get(forget_token=token)
        if request.method == "POST":
            new_password = request.POST.get("new_password1")
            confirm_password = request.POST.get("new_password2")
            if new_password and confirm_password and new_password == confirm_password:
                if len(new_password) < 8:
                    messages.error(request, "Password must be at least 8 characters long.")
                elif not any(char.isdigit() for char in new_password):
                    messages.error(request, "Password must include at least one number.")
                elif not any(char.isalpha() for char in new_password):
                    messages.error(request, "Password must include at least one letter.")
                else:
                    user = profile.user
                    user.set_password(new_password)
                    user.save()
                    profile.forget_token = ""
                    profile.save()
                    messages.success(request, "Password has been reset successfully.")
                    return redirect('/login')
            else:
                messages.error(request, "Passwords do not match.")
    except Profile.DoesNotExist:
        messages.error(request, "Invalid or expired token.")
    return render(request, "change_password.html", context)

# views.py
@login_required
def confirm_payment(request, payment_intent_id):
    profile = Profile.objects.get(user=request.user)
    try:
        payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        plan = payment_intent.metadata.get('plan')
        print(payment_intent)
        if payment_intent.status == "succeeded":
            if plan == 'basic':
                profile.subscription_plan = 'Basic'
                profile.subscription_datetime = datetime.datetime.now() + datetime.timedelta(days=30)
                profile.image_left += 250
            elif plan == 'pro':
                profile.subscription_plan = 'Pro'
                profile.subscription_datetime = datetime.datetime.now() + datetime.timedelta(days=30)
                profile.image_left += 1000
            profile.save()
            messages.success(request, f"Your payment was successful! {plan.capitalize()} plan activated.")
            return redirect(f'/subscription-success')
        else:
            messages.error(request, f"Payment status: {payment_intent.status}. Please try again.")
    except Exception as e:
        messages.error(request, f"Error retrieving payment intent: {e}")
    return redirect('/subscription/None/')


def forget_pass_page(request):
    if request.user.is_anonymous:
        if request.method == "POST":
            email = request.POST.get("email")
            try:
                user = User.objects.get(email=email)
                token = str(uuid.uuid4())
                profile, created = Profile.objects.get_or_create(user=user)
                profile.forget_token = token
                profile.save()
                email_sender(user.username, token, email)
                messages.success(request, "A mail has been sent to your email address.")
                return redirect('/confirm-mail-sent')
            except User.DoesNotExist:
                messages.error(request, "Invalid/unregistered email address.")
    else:
        messages.error(request, "You are already logged in.")
    return render(request, "forgot.html")


def generate_page(request):
    context = {}

    if not request.user.is_anonymous:
        profile = Profile.objects.get(user=request.user)
        
        if profile.subscription_datetime and profile.subscription_datetime < now():
            profile.image_left = 0
            profile.subscription_plan = 'Free'
            profile.subscription_datetime = None
            profile.save()
                
        context['credits_left'] = profile.image_left
        
        if profile.image_left != 0:
            if request.method == "POST":
                prompt = str(request.POST.get("description"))
                options = request.POST.get("options")

                if not prompt or len(prompt.strip()) < 2:
                    messages.error(request, "Invalid or too short prompt.")
                elif len(prompt) > 1000:
                    messages.error(request, "Maximum length reached.")
                else:
                    try:
                        request_img = ai_file.request_image(prompt, options)
                        
                        if request_img:
                            # Save image to file storage and store file path
                            file_path = f"generated_images/{uuid.uuid4()}.png"
                            with open(file_path, "wb") as img_file:
                                img_file.write(request_img.getvalue())
                            
                            profile.image_left -= 1
                            profile.images_generated.append(file_path)
                            profile.save()
                            context['credits_left'] = profile.image_left
                            context['image_path'] = file_path
                        else:
                            raise ValueError("No image was generated.")
                    except Exception as e:
                        messages.error(request, f"Error generating image: {e}")
                        context['error'] = str(e)
        else:
            messages.error(request, "Your plan is over. Please purchase a subscription.")
    else:
        messages.error(request, "Please log in to start generating images.")
        return redirect('/login') 

    return render(request, "generate.html", context)


def login_page(request):
    if request.user.is_anonymous:
        if request.method == "POST":
            username = request.POST.get("username")
            password = request.POST.get("password")
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Logged in successfully as {username}.')
                return redirect('/dashboard')  # Redirect to home or dashboard
            else:
                messages.error(request, "Invalid username or password.")
    else:
        messages.error(request, "You are already logged in.")
    return render(request, "login.html")

@login_required
def logout_page(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect('/login')

@login_required
def payment_page(request, plan):
    amount = plans[plan]
    context = {'plan': plan, 'amount': amount, 'client_secret': None, 'stripe_publish_key': setting.STRIPE_KEY_ID}
    try:
        stripe.api_key = setting.STRIPE_SECRET_KEY
        payment_intent = stripe.PaymentIntent.create(
            amount=int(amount * 100),  # Amount in cents
            currency="usd",
            payment_method_types=["card"],
            metadata={'user_id': request.user.id, 'plan': plan},
        )
        context['client_secret'] = payment_intent.client_secret
        context['payment_intent_id'] = payment_intent.id
    except Exception as e:
        messages.error(request, f"Payment failed: {e}")
        return redirect('/subscription/None/')
    return render(request, "payment.html", context)

@login_required
def dashboard_page(request):
    context = {}
    profile = Profile.objects.get(user=request.user)
    if profile.subscription_plan != 'Free':
        context['plan'] = profile.subscription_plan
    return render(request, "dashboard.html", context)

def confirm_mail_sent(request):
    return render(request, "confirm_mail_sent.html")

@login_required
def view_images_page(request):
    context = {}
    
    profile = Profile.objects.get(user=request.user)
    context['images'] = profile.images_generated
    return render(request, "view_images.html", context)

def register_page(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("password_confirm")
        
        if password != confirm_password:
            messages.error(request, "Passwords do not match")
        elif User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
        elif User.objects.filter(email=email).exists():  # Correcting to check email, not username
            messages.error(request, "Email already exists")
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            Profile.objects.create(user=user)  # Create a Profile for the user
            messages.success(request, "Registration successful. Please login")
            return redirect('/login')
    return render(request, "register.html")

def email_sender(username, token, email):
    subject = f"Password Reset Request - {website_domain}"
    message = f'''
    Dear {username},

    We received a request to reset your password for your account associated with this email address. If you did not make this request, you can ignore this email.

    To reset your password, please click the link below:

    http://{website_domain}/change-password/{token}/

    After clicking the link, you will be able to set a new password for your account. If you encounter any issues, please do not hesitate to contact our support team.

    Thank you for being a valued member of our community.

    Best regards,

    CodeLearn
    {setting.EMAIL_HOST_USER}
    '''
    email_from = setting.EMAIL_HOST_USER
    recipient_list = [email]
    send_mail(subject, message, email_from, recipient_list)
    return True
