from rest_framework import generics, viewsets
from rest_framework.response import Response
from .models import MenuItem, Category, Cart, OrderItem, Order
from .serializers import MenuItemSerializer, CategorySerializer, CartSerializer, OrderItemSerializer, OrderSerializer
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework import permissions
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User, Group
from rest_framework import status
from .permissions import IsManager
from datetime import datetime
#from .throttles import TenCallsPerMinute
from rest_framework.throttling import UserRateThrottle


def handle_group_operation(request, group_name):
    if request.method == "GET":
        group = Group.objects.get(name=group_name)
        users = group.user_set.values_list("username", flat=True)
        print(list(users))
        return Response({f"Users of {group_name} group": list(users)})
    else:
        username = request.data["username"]
        if username:
            user = get_object_or_404(User, username=username)
            group = Group.objects.get(name=group_name)
            if user not in group.user_set.all():
                if request.method == "POST":
                    group.user_set.add(user)
                    return Response({"message": f"user added to the {group_name} group successfully"})
                elif request.method == "DELETE":
                    return Response({"message": f"user is not a member of {group_name} group"})
            else:
                if request.method == "POST":
                    return Response({"message": f"user already added to the {group_name} group"})
                elif request.method == "DELETE":
                    group.user_set.remove(user)
                    return Response({f"{user} successfully removed from {group_name} group."})
        return Response({"message": f"Error adding a user to the {group_name} group"}, status.HTTP_400_BAD_REQUEST)
    

# Admin can add, remove, retrieve and delete user from manager group.
@api_view(["POST", "DELETE","GET"])
@permission_classes([IsAdminUser])
def managers_group(request):
    return handle_group_operation(request, "manager")

# Manager can add, remove, retrieve and delete user from delivery crew group.
@api_view(["POST", "DELETE","GET"])
@permission_classes([IsManager])
def delivery_group(request):
    return handle_group_operation(request, "delivery crew")


class CategoriesView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return []
        
        return [IsAdminUser()]
    

class MenuItemsView(generics.ListCreateAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    throttle_classes = [UserRateThrottle]
    ordering_fields = ["price"]
    search_fields = ["category__title"]

    def get_permissions(self):
        if self.request.method == "GET":
            return []
        elif self.request.method == "POST":
            return [permissions.OR(IsAdminUser(), IsManager())]
        
        #  preventing the "NoneType" error when iterating over the permissions.
        return super().get_permissions()


class SingleMenuItemView(generics.RetrieveUpdateDestroyAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return []
        elif self.request.method == "PUT" or "PATCH" or "DELETE":
            if self.request.data["featured"] == True:
                return [IsManager]
            return [IsManager()]
            


class CartItemView(viewsets.ModelViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    throttle_classes = [UserRateThrottle]
    permission_classes = [IsAuthenticated]

    def list(self, request):
        user = request.user
        cart = Cart.objects.filter(user=user)
        if cart.exists():
            serialized_items = CartSerializer(cart, many=True)
            return Response(serialized_items.data, status=status.HTTP_200_OK)
        else:
            return Response({"message": "The cart is empty."}, status=status.HTTP_200_OK)


    def create(self, request):
        menu_item_id = request.data.get("menu_item_id")
        quantity = request.data.get("quantity", 1)

        try:
            menu_item = MenuItem.objects.get(pk=menu_item_id)
        except MenuItem.DoesNotExist: 
            return Response({"error": "menu-item not found"}, status=status.HTTP_404_NOT_FOUND)
        
        
        user = request.user
        existing_cart = Cart.objects.filter(menuitem=menu_item_id, user=user).first()
            
        # Check cart is already existed
        # if it is existed.
        if existing_cart:
            existing_cart.quantity += quantity
            existing_cart.price += existing_cart.price * quantity
            existing_cart.save()
            serialized_item = CartSerializer(existing_cart)
            return Response(serialized_item.data, status=status.HTTP_200_OK)
            
        # if not existed, create a new cart.
        else:
            cart_item = Cart.objects.create(menuitem=menu_item, user=user, quantity=quantity , 
                                            unit_price=menu_item.price, price=menu_item.price*quantity)
        
            serialized_item = CartSerializer(cart_item)
            return Response(serialized_item.data, status=status.HTTP_201_CREATED)
        
    def destroy(self, request):
        user_cart_items = Cart.objects.filter(user=self.request.user)
        if user_cart_items.exists():
            user_cart_items.delete()
            return Response({"message": "Item is removed from the cart."})
        else:
            return Response({"error": "Menu item not found in the cart."}, status=status.HTTP_404_NOT_FOUND)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([UserRateThrottle,])
def order_item(request):
    if request.method == "POST":
        # if the user is a manager, assign order to delivery crew
        if request.user.groups.filter(name="manager").exists():
            # get orders with deli-crew None value
            orders_to_assign = Order.objects.filter(delivery_crew=None)
            if orders_to_assign.exists():
                deli_crew_group = Group.objects.get(name="delivery crew")
                deli_crew_users = deli_crew_group.user_set.all()
                
                for order in orders_to_assign:
                    if deli_crew_users.exists():
                        # assign the first deli-crew to the order
                        deli_crew_user = deli_crew_users.first()
                        order.delivery_crew = deli_crew_user
                        order.save()

                        # remove this deli-crew from the list
                        deli_crew_users = deli_crew_users.exclude(id=deli_crew_user.id)
                return Response({"message": "Order assigned to delivery crew successfully"})
            else:
                return Response({"message": "Fail to get the order"})

        # if the user is a customer, can order items
        if request.user.is_authenticated:
            cart_items = Cart.objects.filter(user=request.user)
            if not cart_items.exists():
                return Response({"message": "Can't place an order without menuitems in the cart"})
            # convert cart items to order items
            order_items = []
            for item in cart_items:
                order_item = OrderItem(
                    order = None,
                    menuitem = item.menuitem,
                    quantity = item.quantity,
                    unit_price = item.unit_price,
                    price = item.price
                )
                order_items.append(order_item)

            total_price = sum(item.price for item in order_items)

            # create order
            order = Order.objects.create(user=request.user, delivery_crew=None, total=total_price, date=datetime.now(), status=False)

            # map order item with order
            for order_item in order_items:
                order_item.order = order
                order_item.save()

            # after order, flush cart to empty
            cart_items.delete()

            serialized_item = OrderItemSerializer(order_items, many=True)
            return Response(serialized_item.data, status=status.HTTP_201_CREATED)
        else:
            return Response({"message": "user not authenticated"},status=status.HTTP_401_UNAUTHORIZED)
    
    elif request.method == "GET":
        # if the user is a manager, view all orders
        if request.user.groups.filter(name="manager").exists():
            orders = Order.objects.all()
            orders_details = OrderItem.objects.filter(order__in=orders)
            serialized_item = OrderItemSerializer(orders_details, many=True)
            return Response(serialized_item.data, status=status.HTTP_200_OK)

        # if the user is a deli-crew, view his assigned order
        if request.user.groups.filter(name="delivery crew").exists():
            orders_assigned = Order.objects.filter(delivery_crew=request.user)
            order = OrderItem.objects.filter(order__in=orders_assigned)
            serialized_item = OrderItemSerializer(order, many=True)
            return Response(serialized_item.data, status=status.HTTP_200_OK)


        # if the user is a customer, view his own order
        if request.user.is_authenticated:
            user_orders = Order.objects.filter(user=request.user)
            print(user_orders)
            user_orders_items = OrderItem.objects.filter(order__in=user_orders)
            serialized_item = OrderItemSerializer(user_orders_items, many=True)
            print(serialized_item.data)
            return Response(serialized_item.data, status=status.HTTP_200_OK)

@api_view(["DELETE", "PUT"])
@permission_classes([IsAuthenticated])
def single_order_item(request, pk):
    if request.method == "DELETE":
        # if the user is a manager, he can delete the order
        if request.user.groups.filter(name="manager").exists():
            try:
                order = Order.objects.get(pk=pk)
            except Order.DoesNotExist:
                return Response({"error": "order not found"}, status=status.HTTP_400_BAD_REQUEST)

            order.delete()
            return Response({"message": "Order deleted successfully"}, status=status.HTTP_200_OK)
    
    elif request.method == "PUT":
        # if the user is a deli-crew, update the status of the assigned order
        if request.user.groups.filter(name="delivery crew").exists():
            try:
                order = Order.objects.get(pk=pk)
            except Order.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)
        
            new_status = request.data.get("status")
            if new_status is not None:
                order.status = new_status
                order.save()
                serialized_item = OrderSerializer(order)
                return Response(serialized_item.data, status=status.HTTP_200_OK)
        
        else:
            return Response({"message": "Not authorized to modify the order"}, status=status.HTTP_401_UNAUTHORIZED)
