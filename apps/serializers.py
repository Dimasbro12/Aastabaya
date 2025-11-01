from rest_framework import serializers
from .models import User, Data, News, Infographic, Publication
from django.db.models import fields


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
        )
        return user
    
class DataSerializers(serializers.ModelSerializer):
    class Meta:
        model = Data
        fields = ('data_name', 'data_description', 'data_image', 'data_view_count', 'data_created_at')
        
class NewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = News
        fields = ('news_id','title','content','category_id','category_name','release_date','picture_url')

class InfographicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Infographic
        fields = ('title','image','dl')
        

class PublicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Publication
        fields = ('pub_id','title','abstract','image','dl','date','size')
        