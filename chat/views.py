from django.shortcuts import redirect
from django.views.generic import ListView, CreateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import Conversation, Message
from .forms import ConversationForm, MessageForm
from django.db.models import Q
from rest_framework import viewsets
from .serializers import ConversationSerializer, MessageSerializer
from team.permissions import IsAdminOrReadOnly

class ChatHomeView(LoginRequiredMixin, ListView):
    model = Conversation
    template_name = 'chat/home.html'
    
    def get_queryset(self):
        return Conversation.objects.filter(
            Q(participants=self.request.user) | Q(client__user=self.request.user)
        ).distinct()

class ConversationListView(LoginRequiredMixin, ListView):
    model = Conversation
    template_name = 'chat/conversation_list.html'
    
    def get_queryset(self):
        return Conversation.objects.filter(
            Q(participants=self.request.user) | Q(client__user=self.request.user)
        ).distinct()

class ConversationCreateView(LoginRequiredMixin, CreateView):
    model = Conversation
    form_class = ConversationForm
    template_name = 'chat/conversation_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        response = super().form_valid(form)
        self.object.participants.add(self.request.user)
        if not self.object.conversation_type:
            self.object.conversation_type = 'client' if self.object.client else 'team'
            self.object.save()
        return response
    
    def get_success_url(self):
        return reverse_lazy('chat:conversation_detail', kwargs={'pk': self.object.pk})

class ConversationDetailView(LoginRequiredMixin, DetailView):
    model = Conversation
    template_name = 'chat/conversation_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['message_form'] = MessageForm()
        return context
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = MessageForm(request.POST, request.FILES)
        if form.is_valid():
            message = form.save(commit=False)
            message.conversation = self.object
            message.sender = request.user
            message.save()
            return redirect('chat:conversation_detail', pk=self.object.pk)
        context = self.get_context_data()
        context['message_form'] = form
        return self.render_to_response(context)

class ConversationViewSet(viewsets.ModelViewSet):
    queryset = Conversation.objects.all()
    serializer_class = ConversationSerializer
    permission_classes = [IsAdminOrReadOnly]
    
    def get_queryset(self):
        return Conversation.objects.filter(
            Q(participants=self.request.user) | Q(client__user=self.request.user)
        ).distinct()

class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [IsAdminOrReadOnly]
    
    def get_queryset(self):
        return Message.objects.filter(
            conversation__in=Conversation.objects.filter(
                Q(participants=self.request.user) | Q(client__user=self.request.user)
            )
        )
    
    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)