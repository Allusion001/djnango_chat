from channels.generic.websocket import WebsocketConsumer
from .models import GroupMessage,ChatGroup
import json
from django.template.loader import render_to_string
from asgiref.sync import async_to_sync
from django.shortcuts import get_object_or_404

class ChatroomConsumer(WebsocketConsumer):
    groups = ["broadcast"]

    def connect(self):
        self.user = self.scope['user']
        self.chatroom_name = self.scope['url_route']['kwargs']['chatroom_name'] 
        self.chatroom = get_object_or_404(ChatGroup, group_name=self.chatroom_name)

        async_to_sync(self.channel_layer.group_add)(
            self.chatroom_name, self.channel_name
        )

        if self.user not in self.chatroom.users_online.all():
            self.chatroom.users_online.add(self.user)
            self.update_online_count()

        

        self.accept()


    def receive(self, text_data):
        text_data_json=json.loads(text_data)
        body=text_data_json['body']

        message=GroupMessage.objects.create(
            body=body,
            author=self.user,
            message=self.chatroom
        )

        # context={
        #     'message':message,
        #     'user':self.user
        # }

        # html=render_to_string("chatApp/partial/chat_message_p.html",context=context)

        event={
            'type':'messageHandler',
            'message_id':message.id,
        }

        async_to_sync(self.channel_layer.group_send)(
            self.chatroom_name, event
        )

    def messageHandler(self,event):
            message_id=event['message_id']
            message=GroupMessage.objects.get(id=message_id)
            context={
            'message':message,
            'user':self.user
            }

            html=render_to_string("chatApp/partial/chat_message_p.html",context=context)

            self.send(text_data=html)

    def update_online_count(self):
        online_count=self.chatroom.users_online.count()-1
        
        event={
            'type':'onlineHandler',
            'online_count':online_count
        }

        async_to_sync(self.channel_layer.group_send)(self.chatroom_name,event)
        
    def onlineHandler(self,event):
        context={
            'online_count':event['online_count'],
            'chat_group':self.chatroom
            }
        
   
        html=render_to_string("chatApp/partial/online_count.html",context)
        self.send(text_data=html)

      
    def disconnect(self,close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.chatroom_name, self.channel_name
        )

        if self.user in self.chatroom.users_online.all():
            self.chatroom.users_online.remove(self.user)
            self.update_online_count()

    # def disconnect(self, close_code):
    #     # Called when the socket closes


class OnlineStatusConsumer(WebsocketConsumer):
    def connect(self):
        self.user=self.scope['user']
        self.group_name='online-status'
        self.group=get_object_or_404(ChatGroup,group_name=self.group_name)

        if self.user not in self.group.users_online.all():
            self.group.users_online.add(self.user)

        async_to_sync(self.channel_layer.group_add)(
            self.group_name,self.channel_name
        )

        self.accept()
        self.online_status()

    def disconnect(self,close_code):
        if self.user in self.group.users_online.all():
            self.group.users_online.remove(self.user)
            


        async_to_sync(self.channel_layer.group_discard)(
            self.group_name,self.channel_name
        )

        self.online_status()

        

    def online_status(self):
        event={
            'type':'online_status_handler'
        }

        async_to_sync(self.channel_layer.group_send)(
            self.group_name,event
        )

    def online_status_handler(self,event):
        online_users=self.group.users_online.exclude(id=self.user.id)
        public_chat_users=ChatGroup.objects.get(group_name="public-chat").users_online.exclude(id=self.user.id)

        if public_chat_users:
            online_in_chats=True
        else:
            online_in_chats=False

        context={
            'online_users':online_users,
            'online_in_chats':online_in_chats,
            'public_chat_users':public_chat_users,
        }


        html=render_to_string("chatApp/partial/online_status.html",context=context)
        self.send(text_data=html)