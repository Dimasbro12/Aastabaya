from re import A
from django.shortcuts import get_object_or_404, render
from .services.API_service import get_news_data
from .services.API_service import get_inpographic_data
from .services.API_service import get_publication_data
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import serializers
from rest_framework import status
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .serializers import UserSerializer, DataSerializers
from .models import User, Data

@api_view(['POST'])
def register_user(request):
    if request.method == 'POST':
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def user_login(request):
    if request.method == 'POST':
        username = request.data.get('username')
        password = request.data.get('password')

        user = None
        if '@' in username:
            try:
                user = User.objects.get(email=username)
            except ObjectDoesNotExist:
                pass

        if not user:
            user = authenticate(username=username, password=password)

        if user:
            token, _ = Token.objects.get_or_create(user=user)
            return Response({'token': token.key}, status=status.HTTP_200_OK)

        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def user_logout(request):
    if request.method == 'POST':
        try:
            # Delete the user's token to logout
            request.user.auth_token.delete()
            return Response({'message': 'Successfully logged out.'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def ApiOverview(request):
    api_urls = {
        'all_items' : '/',
        'Search by Category' : '/?category=category_name',
        'Search by Subcategory' : '/?subcategory=category_name',
        'Add': '/create',
        'Update': '/update/pk',
        'Delete': '/item/pk/delete'
    }
    return Response(api_urls)


@api_view(['POST'])
def add_data (request):
    data = DataSerializers(data=request.data)
    if Data.objects.filter(**request.data).exists():
        raise serializers.ValidationError('This data already exists')
    if data.is_valid():
        data.save()
        return Response(data.data)
    else:
        return Response(status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
def view_data (request):
    if request.query_params:
        data = Data.objects.filter(**request.query_params.dict())
    else:
        data = Data.objects.all()
    if data:
        serializer = DataSerializers(data, many=True)
        return Response(serializer.data)
    else:
        return Response(status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
def update_data (request, pk):
    datas = Data.objects.get(pk=pk)
    data = DataSerializers(instance=datas, data=request.data)
    if data.is_valid():
        data.save()
        return Response(data.data)
    else:
        return Response(status=status.HTTP_404_NOT_FOUND)

@api_view(['DELETE'])
def delete_data (request, pk):
    data = get_object_or_404(data, pk=pk)
    data.delete()
    return Response(status=status.HTTP_202_ACCEPTED)
    
    
def apps(request):
    # Fetch data directly from the service functions
    dataNews = get_news_data()
    dataInpographic = get_inpographic_data()
    dataPublication = get_publication_data()

    context = {
        'dataNews': dataNews,
        'dataInpographic': dataInpographic,
        'dataPublication': dataPublication,
    }
    return render(request, 'index.html', context)


