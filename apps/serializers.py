from rest_framework import serializers
from .models import Bookmark, HumanDevelopmentIndex, User, Data, News, Infographic, Publication, HotelOccupancyCombined, HotelOccupancyYearly
from django.contrib.contenttypes.models import ContentType
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
    # `content_type_name` digunakan untuk membuat bookmark baru (write-only)
    content_type_name = serializers.CharField(write_only=True, help_text="Model name: 'news', 'infographic', or 'publication'")
    # `content_type_model` digunakan untuk menampilkan nama model (read-only)
    content_type_model = serializers.CharField(source='content_type.model', read_only=True)

    class Meta:
        model = Bookmark
        fields = ['id', 'user', 'content_type_model', 'content_type_name', 'object_id', 'content_object', 'created_at']
        read_only_fields = ['user', 'created_at', 'content_object', 'content_type_model']

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

    def validate(self, data):
        """
        Validasi kustom untuk memastikan content_type dan object_id valid.
        """
        content_type_name = data.get('content_type_name').lower()
        object_id = data.get('object_id')
        
        # Mendapatkan model dari ContentType
        try:
            content_type = ContentType.objects.get(app_label='apps', model=content_type_name)
        except ContentType.DoesNotExist:
            raise serializers.ValidationError(f"Tipe konten '{content_type_name}' tidak valid.")

        # Memeriksa apakah objek dengan ID tersebut ada
        model_class = content_type.model_class()
        if not model_class.objects.filter(pk=object_id).exists():
            raise serializers.ValidationError(f"Objek dengan ID {object_id} untuk model '{content_type_name}' tidak ditemukan.")
        
        # Menyimpan instance ContentType untuk digunakan di method create
        data['content_type'] = content_type
        return data

    def create(self, validated_data):
        # Menghapus 'content_type_name' karena tidak ada di model Bookmark
        validated_data.pop('content_type_name', None)
        return Bookmark.objects.create(**validated_data)

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
