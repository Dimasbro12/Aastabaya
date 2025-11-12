from django.shortcuts import get_object_or_404, render, redirect
from .services.API_service import BPSInfographicService, BPSNewsService, BPSPublicationService
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate, logout, login as auth_login
from rest_framework.response import Response
from rest_framework import serializers, status, viewsets
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .serializers import UserSerializer, DataSerializers, NewsSerializer, InfographicSerializer, PublicationSerializer
from .models import User, Data, News, Infographic, Publication


class NewsViewSet(viewsets.ModelViewSet):
    queryset = News.objects.all()
    serializer_class = NewsSerializer


class InpographicViewSet(viewsets.ModelViewSet):
    queryset = Infographic.objects.all()
    serializer_class = InfographicSerializer

class PublicationViewSet(viewsets.ModelViewSet):
    queryset = Publication.objects.all()
    serializer_class = PublicationSerializer

@api_view(['GET'])
def sync_bps_news(request):
    try:
        saved = BPSNewsService.sync_news()
        return Response({
            "status": "success",
            "message": f"{saved} berita berhasil disinkronkan dari API BPS."
        })
    except Exception as e:
        return Response({
            "status": "error",
            "message": str(e)
        }, status=500)
        
@api_view(['GET'])
def sync_bps_infographic(request):
    try:
        saved = BPSInfographicService.sync_infographic()
        return Response({
            "status": "success",
            "message": f"{saved} infografis berhasil disinkronkan dari API BPS."
        })
    except Exception as e:
        return Response({
            "status": "error",
            "message": str(e)
        }, status=500)
        
@api_view(['GET'])
def sync_bps_publication(request):
    try:
        saved = BPSPublicationService.sync_publication()
        return Response({
            "status": "success",
            "message": f"{saved} publikasi berhasil disinkronkan dari API BPS."
        })
    except Exception as e:
        return Response({
            "status": "error",
            "message": str(e)
        }, status=500)
        
        
# --- Views to render HTML pages ---
def signup_page(request):
    """Renders the signup page."""
    return render(request, 'accounts/signup.html')

def login_page(request):
    """Renders the login page."""
    return render(request, 'accounts/login.html')

# --- API Endpoints for Authentication ---
@api_view(['POST'])
def register_user(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def user_login(request):
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
    return redirect('login')

def logout_view(request):
    """
    Logout view that clears both token and session.
    Accepts POST, GET and other methods and redirects to home.
    """
    # Delete token if the user has one
    try:
        if request.user.is_authenticated and hasattr(request.user, 'auth_token'):
            request.user.auth_token.delete()
    except Exception:
        pass
    
    # Clear Django session
    logout(request)
    
    # Redirect to home page
    return redirect('index')

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
    data = get_object_or_404(Data, pk=pk)
    data.delete()
    return Response(status=status.HTTP_202_ACCEPTED)
    
    
def apps(request):
    # Fetch data directly from the service functions
    dataNews = News.objects.all()
    dataInpographic = Infographic.objects.all()
    dataPublication = Publication.objects.all()

    context = {
        'dataNews': dataNews,
        'dataInpographic': dataInpographic,
        'dataPublication': dataPublication,
    }
    return render(request, 'index.html', context)

def dashboard(request):
    # Fetch data directly from the service functions
    
    dataNews = News.objects.all()
    dataInpographic = Infographic.objects.all()
    dataPublication = Publication.objects.all()

    context = {
        'dataNews': dataNews,
        'dataInpographic': dataInpographic,
        'dataPublication': dataPublication,
    }
    return render(request, 'dashboard/dashboard.html', context)