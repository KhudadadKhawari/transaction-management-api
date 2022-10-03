from unicodedata import category
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Transaction, Category

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'password','first_name','last_name']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        user = User.objects.create_user(
            validated_data['username'].lower(),
            validated_data['email'].lower(),
            validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name']
        )
        return user


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class TransactionSerializer(serializers.ModelSerializer):
    category = CategorySerializer()
    class Meta:
        model = Transaction
        fields = ['id', 'title', 'amount', 'transaction_type', 'description', 'date', 'category']

    # to_representation get the category name and set it to the transaction
    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['category'] = CategorySerializer(instance.category).data['name']
        return rep

    # to_internal_value find the category by name and current user and set it to the transaction
    def to_internal_value(self, data):
        rep = super().to_internal_value(data)
        category_name = data['category']['name']
        rep['category'] = Category.objects.get(name=category_name, user=self.context['request'].user)
        return rep

