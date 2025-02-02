from django.urls import path
from . import views

urlpatterns = [
    path('groups/manager/users', views.managers_group),
    path('groups/delivery-crew/users', views.delivery_group),
    path('category', views.CategoriesView.as_view()),
    path('menu-items', views.MenuItemsView.as_view()),
    path('menu-items/<int:pk>', views.SingleMenuItemView.as_view()),
    path('cart/menu-items', views.CartItemView.as_view({'get':'list', 'post':'create', 'delete': 'destroy'})),
    path('orders', views.order_item),
    path('orders/<int:pk>', views.single_order_item),
    #path('orders/assign-order', views.assign_orders_to_delicrew),
    #path('orders/view-assigned-orders', views.view_assigned_orders),

]