from django.shortcuts import render,get_object_or_404,redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import Http404
from .models import *
from .forms import *
from environ import Env

# Create your views here.

@login_required
def chat_view(request, chatroom_name='public-chat'):

    chat_group=get_object_or_404(ChatGroup,group_name=chatroom_name)
    if request.user not in chat_group.members.all():
        chat_group.members.add(request.user)
    chat_messages=chat_group.group_messages.all()
    form = ChatMessageCreateForm()

    other_user=None

    if chat_group.is_private:
        if request.user not in chat_group.members.all():
            raise Http404()

        for member in chat_group.members.all():
            if member != request.user:
                other_user=member
                break

    if chat_group.groupchat_name:
        if request.user not in chat_group.members.all():
            if request.user.emailaddress_set.filter(verified=True).exists():
                chat_group.members.add(request.user)
            else:
                messages.warning(request,"You Need To Verify the Email Address")
                return redirect("profile-settings")

    
    if request.htmx:
        form = ChatMessageCreateForm(request.POST)
        if form.is_valid:
            
            message = form.save(commit=False)

            message.author = request.user
            message.group = chat_group
            message.save()
           
            
            context={
                'message':message,
                'user':request.user
            }

            return render(request,"chatApp/partial/chat_message_p.html",context)
           # return redirect('home')

    context={"chat_messages":chat_messages,
    'form':form,
    'other_user':other_user,
    'chatroom_name':chatroom_name,
    'chat_group':chat_group
    
    }

    return render(request,"chatApp/chat.html",context)



def get_or_create_chatroom(request,username):
    if request.user.username == username:
        return  redirect("home")

    other_user=User.objects.get(username=username)
    my_chatroom=request.user.chat_groups.filter(is_private=True)


    if my_chatroom.exists():
        for chat in my_chatroom:
            if other_user in chat.members.all():
                chatroom=chat
                break

            else:
                chatroom=ChatGroup.objects.create(is_private=True)
                chatroom.members.add(request.user,other_user)

    else:
        chatroom=ChatGroup.objects.create(is_private=True)
        chatroom.members.add(request.user,other_user)

    return redirect('chatroom',chatroom.group_name)
@login_required
def create_chatgroup(request):

    form = NewGroupForm()

    if (request.method == "POST"):
        form = NewGroupForm(request.POST)
        if form.is_valid:
            new_groupchat=form.save(commit=False)
            new_groupchat.is_admin=request.user
            new_groupchat.save()
            new_groupchat.members.add(request.user)
            return redirect('chatroom',new_groupchat.group_name)


    context={
        'form': form
    }

    return render(request,"chatApp/create_chatgroup.html",context)

@login_required
def chatroom_edit_view(request, chatroom_name):
    chat_group = get_object_or_404(ChatGroup, group_name=chatroom_name)
    if request.user != chat_group.is_admin:
        raise Http404()
    
    form = ChatRoomEditForm(instance=chat_group) 
    
    if request.method == 'POST':
        form = ChatRoomEditForm(request.POST, instance=chat_group)
        if form.is_valid():
            form.save()
            
            remove_members = request.POST.getlist('remove_members')
            for member_id in remove_members:
                member = User.objects.get(id=member_id)
                chat_group.members.remove(member)  
                
            return redirect('chatroom', chatroom_name) 
    
    context = {
        'form' : form,
        'chat_group' : chat_group
    }   
    return render(request, 'chatApp/chatroom_edit.html', context) 

@login_required
def chatroom_delete_view(request, chatroom_name):
    chat_group = get_object_or_404(ChatGroup, group_name=chatroom_name)
    if request.user != chat_group.is_admin:
        raise Http404()
    
    if request.method == "POST":
        chat_group.delete()
        messages.success(request, 'Chatroom deleted')
        return redirect('home')
    
    return render(request, 'chatApp/chatroom_delete.html', {'chat_group':chat_group})