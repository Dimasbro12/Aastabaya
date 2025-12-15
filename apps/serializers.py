from rest_framework import serializers
from .models import Bookmark, HumanDevelopmentIndex, User, Data, News, Infographic, Publication, HotelOccupancyCombined, HotelOccupancyYearly
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

class BookmarkSerializer(serializers.ModelSerializer):
    """
    Serializer untuk model Bookmark.
    Ini secara dinamis menserialisasi `content_object` berdasarkan tipenya.
    """
    content_object = serializers.SerializerMethodField()
    content_type_name = serializers.CharField(source='content_type.model', read_only=True)

    class Meta:
        model = Bookmark
        fields = ['id', 'user', 'content_type_name', 'object_id', 'content_object', 'created_at']

    def get_content_object(self, obj):
        """
        Menggunakan serializer yang sesuai berdasarkan instance dari content_object.
        """
        if isinstance(obj.content_object, News):
            return NewsSerializer(obj.content_object, context=self.context).data
        if isinstance(obj.content_object, Infographic):
            return InfographicSerializer(obj.content_object, context=self.context).data
        if isinstance(obj.content_object, Publication):
            return PublicationSerializer(obj.content_object, context=self.context).data
        return None

class HumanDevelopmentIndexSerializer(serializers.ModelSerializer):
    class Meta:
        model = HumanDevelopmentIndex
        fields = ['id', 'location_name', 'location_type', 'year', 'ipm_value']

class HotelOccupancyCombinedSerializer(serializers.ModelSerializer):
    class Meta:
        model = HotelOccupancyCombined
        fields = ['id', 'year', 'month', 'mktj', 'tpk', 'rlmta', 'rlmtnus', 'rlmtgab', 'gpr']

class HotelOccupancyYearlySerializer(serializers.ModelSerializer):
    class Meta:
        model = HotelOccupancyYearly
        fields = ['id', 'year', 'mktj', 'tpk', 'rlmta', 'rlmtnus', 'rlmtgab', 'gpr']
