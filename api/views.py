from unicodedata import category
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed 
from rest_framework import permissions, status
from django.contrib.auth.models import User
from .serializers import UserSerializer, TransactionSerializer, CategorySerializer
from django.utils.decorators import method_decorator
from django.middleware import csrf
from django.contrib.auth import authenticate
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Transaction, Category
from rest_framework.pagination import PageNumberPagination
import random
from rest_framework.generics import ListAPIView
from django.db.models import Q
import datetime


def get_token(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

# Create your views here.
class RegisterView(APIView):
    permission_classes = ()
    authentication_classes = ()

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

class LoginView(APIView):
    permission_classes = ()
    authentication_classes = ()

    def post(self, request):
        username = request.data.get('username').lower()
        password = request.data.get('password')
        response = Response()
        user = authenticate(username=username, password=password)
        if user is not None:
            data = get_token(user)
            response.set_cookie(
                key = settings.SIMPLE_JWT['AUTH_COOKIE'],
                value = data['access'],
                expires = settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'],
                secure = settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
                httponly = settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
                samesite = settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
            )
            csrf.get_token(request)
            response.data = { "success": "Login Successful", "data": data }
            return response
        else:
            raise AuthenticationFailed(detail="Invalid Credentials")

class LogoutView(APIView):
    permission_classes = ()
    authentication_classes = ()

    def post(self, request):
        response = Response()
        response.delete_cookie(settings.SIMPLE_JWT['AUTH_COOKIE'])
        response.data = { "success": "Logout Successful" }
        return response

# @method_decorator(is_user_authenticated, name='dispatch')
class UserView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        serializer = UserSerializer(user)
        return Response(serializer.data)

# Category CRUD
class CategoryListView(ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CategorySerializer
    pagination_class = PageNumberPagination
    page_size = 10

    def get_queryset(self):
        queryset = Category.objects.filter(user=self.request.user)
        # filter by id, name
        id = self.request.query_params.get('id', None)
        name = self.request.query_params.get('name', None)
        if id is not None:
            queryset = queryset.filter(id=id)
        if name is not None:
            queryset = queryset.filter(name__icontains=name)

        search = self.request.query_params.get('search', None)
        if search is not None:
            queryset = queryset.filter(Q(name__icontains=search))

        sort_by = self.request.query_params.get('sort_by', None)
        if sort_by is not None:
            queryset = queryset.order_by(sort_by)

        return queryset


class CategoryCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        serializer = CategorySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=user)
        return Response(serializer.data)

class SingleCategoryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        user = request.user
        try:
            category = Category.objects.get(pk=pk)
            if category.user != user:
                raise AuthenticationFailed(detail="You are not authorized to view this category")
            serializer = CategorySerializer(category)
            return Response(serializer.data)
        except Category.DoesNotExist:
            return Response({"message":"category does not exist"}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        user = request.user
        try:
            category = Category.objects.get(pk=pk)
            if category.user != user:
                raise AuthenticationFailed(detail="You are not authorized to update this category")
            serializer = CategorySerializer(category, data=request.data)
            # add user to the data
            serializer.initial_data['user'] = user.id
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        except Category.DoesNotExist:
            return Response({"message":"category does not exist"}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        user = request.user
        try:
            category = Category.objects.get(pk=pk)
            if category.user != user:
                raise AuthenticationFailed(detail="You are not authorized to delete this category")
            category.delete()
            return Response({"message:","Category Deleted Successfully!"},status=status.HTTP_204_NO_CONTENT)
        except Category.DoesNotExist:
            return Response({"message":"category does not exist"}, status=status.HTTP_404_NOT_FOUND)


# Transaction CRUD
class TransactionListView(ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TransactionSerializer
    pagination_class = PageNumberPagination
    page_size = 10

    def get_queryset(self):
        user = self.request.user
        queryset = Transaction.objects.filter(category__user=user)
        # filtering by id, title, category, transaction_type, date and amount
        id = self.request.query_params.get('id', None)
        title = self.request.query_params.get('title', None)
        category = self.request.query_params.get('category', None)
        transaction_type = self.request.query_params.get('transaction_type', None)
        date = self.request.query_params.get('date', None)
        amount = self.request.query_params.get('amount', None)
        if id:
            queryset = queryset.filter(id=id)
        if title:
            queryset = queryset.filter(title__icontains=title)
        if category is not None:
            queryset = queryset.filter(category__name=category)
        if transaction_type is not None:
            queryset = queryset.filter(transaction_type=transaction_type)
        if date is not None:
            queryset = queryset.filter(date=date)
        if amount is not None:
            queryset = queryset.filter(amount=amount)

        sort_by = self.request.query_params.get('sort_by', None)
        if sort_by is not None:
            queryset = queryset.order_by(sort_by)
            print(sort_by)

        # searcy by searc query
        search = self.request.query_params.get('search', None)
        if search is not None:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(amount__icontains=search) |
                Q(transaction_type__icontains=search) |
                Q(category__name__icontains=search) |
                Q(date__icontains=search) |
                Q(description__icontains=search)
            )

        return queryset

# TransactionCreate View based on Category
class TransactionCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, category_id):
        user = request.user
        category = Category.objects.get(pk=category_id)
        if category.user != user:
            raise AuthenticationFailed(detail="You are not authorized to create transaction for this category")
        category = category.__dict__ # convert to dict used in serializer
        context = {"request": request}
        serializer = TransactionSerializer(data=request.data, context=context)
        serializer.initial_data['category'] = category
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class SingleTransactionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        user = request.user
        try:
            transaction = Transaction.objects.get(pk=pk)
            if transaction.category.user != user:
                raise AuthenticationFailed(detail="You are not authorized to view this transaction")
            serializer = TransactionSerializer(transaction)
            return Response(serializer.data)
        except Transaction.DoesNotExist:
            return Response({"message":"Transaction Not Found"}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        user = request.user
        try:
            transaction = Transaction.objects.get(pk=pk)
            if transaction.category.user != user:
                raise AuthenticationFailed(detail="You are not authorized to update this transaction")

            context = {"request": request}
            serializer = TransactionSerializer(transaction, data=request.data, context=context)

            # check if any field is added to the data so update them
            if 'category' not in serializer.initial_data:
                serializer.initial_data['category'] = transaction.category.__dict__
            else:
                try:
                    serializer.initial_data['category'] = Category.objects.get(user=user, name=serializer.initial_data['category']).__dict__
                except Category.DoesNotExist:
                    raise AuthenticationFailed(detail="Category does not exist")
            if 'transaction_type' not in serializer.initial_data:
                serializer.initial_data['transaction_type'] = transaction.transaction_type
            if 'title' not in serializer.initial_data:
                serializer.initial_data['title'] = transaction.title
            if 'amount' not in serializer.initial_data:
                serializer.initial_data['amount'] = transaction.amount
            if 'description' not in serializer.initial_data:
                serializer.initial_data['description'] = transaction.description

            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        except Transaction.DoesNotExist:
            return Response({"message":"Transaction Not Found"}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        user = request.user
        try:
            transaction = Transaction.objects.get(pk=pk)
            if transaction.category.user != user:
                raise AuthenticationFailed(detail="You are not authorized to delete this transaction")
            transaction.delete()
            return Response({"message":"Transaction Deleted Successfully!"},status=status.HTTP_204_NO_CONTENT)
        except Transaction.DoesNotExist:
            return Response({"message":"Transaction Not Found"}, status=status.HTTP_404_NOT_FOUND)


# Daily, Weekly and Monthly Report and report by category
class DailyReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        today = datetime.date.today()
        transactions = Transaction.objects.filter(category__user=user, date=today)
        serializer = TransactionSerializer(transactions, many=True)
        return Response(serializer.data)

class WeeklyReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        today = datetime.date.today()
        last_week = today - datetime.timedelta(days=7)
        transactions = Transaction.objects.filter(category__user=user, date__range=[last_week, today])
        serializer = TransactionSerializer(transactions, many=True)
        return Response(serializer.data)

class MonthlyReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        today = datetime.date.today()
        last_month = today - datetime.timedelta(days=30)
        transactions = Transaction.objects.filter(category__user=user, date__range=[last_month, today])
        serializer = TransactionSerializer(transactions, many=True)
        return Response(serializer.data)

class CategoryReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        user = request.user
        try:
            category = Category.objects.get(pk=pk)
            if category.user != user:
                raise AuthenticationFailed(detail="You are not authorized to view this category")
            transactions = Transaction.objects.filter(category=category)
            serializer = TransactionSerializer(transactions, many=True)
            return Response(serializer.data)
        except Category.DoesNotExist:
            return Response({"message":"Category Not Found"}, status=status.HTTP_404_NOT_FOUND)


# Add random data to the database
from django.contrib.auth.models import User
from .models import Transaction
import random

class AddRandomCategories(APIView):
    permission_classes = ()

    def get(self, requst):
        user = requst.user
        categories = ['Food', 'Transport', 'Shopping', 'Entertainment', 'Bills', 'Health', 'Education', 'Others']
        for category in categories:
            Category.objects.create(user=user, name=category)
        return Response("Categories added")


class AddRandomData(APIView):
    permission_classes = ()
    
    def get(self, request):
        categories = Category.objects.filter(user=request.user)
        for i in range(101,120):
            transaction = Transaction(
                category = random.choice(categories),
                title = f"Transaction {i}",
                amount = random.randint(100, 1000),
                transaction_type = random.choice(['income', 'expense']),
                description = f"Description {i}",
            )
            transaction.save()
        return Response({"message":"Random Data Added!"})