from django.db import models
from team.models import TeamMember

class Client(models.Model):

    CRNCY_CHOICES = (
        ('USD', 'USD'),
        ('INR', 'INR'),
        ('GBP', 'GBP'),
    )

    user = models.ForeignKey(TeamMember, on_delete=models.CASCADE, related_name='client_profile')
    company = models.CharField(max_length=200)
    address = models.TextField()
    website = models.URLField(blank=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    vat_number = models.CharField(max_length=50, blank=True)
    payment_terms = models.TextField(blank=True)
    preferred_currency = models.CharField(max_length=3, choices=CRNCY_CHOICES, default='USD')
    logo = models.ImageField(upload_to='client_logos/', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} ({self.company})"

class ClientNote(models.Model):
    """Internal notes about clients"""
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='notes')
    content = models.TextField()
    created_by = models.ForeignKey(TeamMember, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_public = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Note for {self.client.company}"

class ClientFile(models.Model):
    """Files associated with clients"""
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to='client_files/')
    description = models.CharField(max_length=200)
    uploaded_by = models.ForeignKey(TeamMember, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.description