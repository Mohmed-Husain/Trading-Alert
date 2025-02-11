from django.shortcuts import render,redirect
from django.contrib import messages
from django.contrib .auth.decorators import login_required
from .forms import UserRegisterForm , UserUpdateForm , ProfileUpdateForm
from django.core.mail import send_mail
from django.http import HttpResponse

#temporary
def send_test_email(request):
    send_mail(
        'Test Email',
        'This is a test email from Django.',
        'arkonafoob@gmail.com',
        ['202351166@iiitvadodara.ac.in'],
        fail_silently=False,
    )
    return HttpResponse("Test email sent successfully!")

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save() 
            Username = form.cleaned_data.get('username')
            messages.success(request, f'Your Account has created been created ,You can login!')
            return redirect('login')
    else:
        form = UserRegisterForm()
        
    return render(request, 'users/register.html',{'form':form ,'title': 'Register'}) 

@login_required
def profile(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST,instance=request.user)
        p_form = ProfileUpdateForm(request.POST,request.FILES,
                                   instance=request.user.profile)
        
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request ,f'Your Account has been updated!')
            return redirect('profile')

    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)


    context={
        'u_form':u_form,
        'p_form':p_form,
        'title':'Profile'
    }
    return render(request, 'users/profile.html', context)