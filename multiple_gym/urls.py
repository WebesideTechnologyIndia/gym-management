from django.urls import path
from . import views

urlpatterns = [
    # Root URL
    path("", views.login_view, name="home"),
    # Authentication
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    # Super Admin URLs
    path("superadmin/", views.superadmin_dashboard, name="superadmin_dashboard"),
    path("create-gym/", views.create_gym, name="create_gym"),
    # Gym Admin URLs
    path("gymadmin/<int:gym_id>/", views.gymadmin_dashboard, name="gymadmin_dashboard"),
    path("gym/<int:gym_id>/", views.gym_detail, name="gym_detail"),
    path("gym/<int:gym_id>/add-member/", views.add_member, name="add_member"),
    # Member URLs
    path("member/", views.member_dashboard, name="member_dashboard"),
    path("create_membership/", views.create_membership, name="create_membership"),
    
    # FIXED: Add both membership_list patterns
    path("membership_list/", views.membership_list, name="membership_list"),  # WITHOUT gym_id
    path("membership_list/<int:gym_id>/", views.membership_list, name="membership_list_gym"),  # WITH gym_id
    
    path("detail/<int:pk>/", views.membership_detail, name="membership_detail"),
    path("gymadmin/", views.gymadmin_home, name="gymadmin_home"),
    # Membership Plan URLs
    path("plans/", views.plan_list, name="plan_list"),
    path("plans/create/", views.create_plan, name="create_plan"),
    path("plans/detail/<int:pk>/", views.plan_detail, name="plan_detail"),
    path(
        "membership/<int:membership_id>/add-payment/",
        views.add_payment,
        name="add_payment",
    ),
    path(
        "membership/<int:membership_id>/payment-history/",
        views.payment_history,
        name="payment_history",
    ),
    path("api/plan-price/<int:plan_id>/", views.get_plan_price, name="get_plan_price"),
    path("pending-payments/", views.pending_payments_view, name="pending_payments"),
]