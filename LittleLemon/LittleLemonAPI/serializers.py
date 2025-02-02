from rest_framework import serializers
from .models import MenuItem, Category, Cart, OrderItem, Order
from django.contrib.auth.models import User

class CategorySerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Category
        fields = ["id", "title"]

class MenuItemSerializer(serializers.ModelSerializer):
    category_id = serializers.IntegerField(write_only=True)
    category = CategorySerializer(read_only=True)

    class Meta:
        model = MenuItem
        fields = ["id", "featured", "title", "price", "category", "category_id"]

class CartSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
            queryset=User.objects.all(),
            default=serializers.CurrentUserDefault())
    menuitem = MenuItemSerializer(read_only=True)
    
    class Meta:
        model = Cart
        fields = ["user", "menuitem", "quantity", "price"]


class OrderSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
            queryset=User.objects.all(),
            default=serializers.CurrentUserDefault())
   

    class Meta:
        model = Order
        fields = ["id", "user", "delivery_crew", "total", "date", "status" ]


class OrderItemSerializer(serializers.ModelSerializer):
    menuitem = MenuItemSerializer(read_only=True)
    order = OrderSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ["menuitem", "quantity", "unit_price", "price", "order"]