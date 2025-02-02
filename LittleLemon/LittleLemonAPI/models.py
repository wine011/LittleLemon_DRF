from django.db import models
from django.contrib.auth.models import User
 
# Create your models here.
class Category(models.Model):
    slug = models.SlugField()
    title = models.CharField(max_length=255, db_index=True, unique=True)

    def __str__(self):
        return self.title

class MenuItem(models.Model):
    title = models.CharField(max_length=255, db_index=True, unique=True)
    price = models.DecimalField(max_digits=6, decimal_places=2, db_index=True)
    #inventory = models.SmallIntegerField()
    featured = models.BooleanField(db_index=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, default=1)

    def __str__(self):
        return self.title

class Cart(models.Model):
    menuitem = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.SmallIntegerField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    unit_price  = models.DecimalField(max_digits=6, decimal_places=2)
    price = models.DecimalField(max_digits=6, decimal_places=2)

    class Meta:
        unique_together = ("menuitem", "user")

    def __str__(self):
        #return self.user
         return f"Cart ID: {self.id} - User: {self.user.username}"

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    delivery_crew = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="delivery_crew", null=True)
    total = models.DecimalField(max_digits=6, decimal_places=2)
    date = models.DateTimeField(db_index=True)
    status = models.BooleanField(db_index=True, default=0)
    #order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.id)
    

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    menuitem = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.SmallIntegerField()
    unit_price = models.DecimalField(max_digits=6, decimal_places=2)
    price = models.DecimalField(max_digits=6, decimal_places=2)

    class Meta:
        unique_together = ["order", "menuitem"]
