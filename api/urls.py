from ssl import VERIFY_ALLOW_PROXY_CERTS
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView, TokenObtainPairView
from .import views

urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # authentification
    path('register/', views.RegisterView.as_view()),
    path('login/', views.LoginView.as_view()),
    path('logout/', views.LogoutView.as_view()),
    # path('user/', views.UserView.as_view()),

    # Categories
    path('categories/', views.CategoryListView.as_view()), # list of all categories for a user
    path('category/add/', views.CategoryCreateView.as_view()), # add a category
    path('category/<int:pk>/', views.SingleCategoryView.as_view()), # get, put, del  a single category

    # transactions
    path('transactions/', views.TransactionListView.as_view()), # list of all transactions for a user
    path('transaction/add/<category_id>/', views.TransactionCreateView.as_view()), # add a transaction
    path('transaction/<int:pk>/', views.SingleTransactionView.as_view()), # get, put, del  a single transaction

    # reports
    path('report/daily/', views.DailyReportView.as_view()),
    path('report/weekly/', views.WeeklyReportView.as_view()),
    path('report/monthly/', views.MonthlyReportView.as_view()),
    path('report/category/<pk>/', views.CategoryReportView.as_view()),

    path('random-transactions/', views.AddRandomData.as_view()),
    # path('random-category/', views.AddRandomCategories.as_view()),
]