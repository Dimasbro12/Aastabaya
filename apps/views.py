from multiprocessing import context
from django.shortcuts import get_object_or_404, render, redirect, reverse
from .forms import ContactForm
from .services.API_service import BPSInfographicService, BPSNewsService, BPSPublicationService, IPMService
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate, logout, login as auth_login
from rest_framework.response import Response
from rest_framework import serializers, status, viewsets
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .serializers import HumanDevelopmentIndexSerializer, UserSerializer, DataSerializers, NewsSerializer, InfographicSerializer, PublicationSerializer, BookmarkSerializer
from .models import HumanDevelopmentIndex, User, Data, News, Infographic, Publication, Bookmark
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.conf import settings

from django.contrib.contenttypes.models import ContentType
class NewsViewSet(viewsets.ModelViewSet):
    queryset = News.objects.all()
    serializer_class = NewsSerializer

class BookmarkViewSet(viewsets.ModelViewSet):
    queryset = Bookmark.objects.all()
    serializer_class = BookmarkSerializer
    

class InpographicViewSet(viewsets.ModelViewSet):
    queryset = Infographic.objects.all()
    serializer_class = InfographicSerializer

class PublicationViewSet(viewsets.ModelViewSet):
    queryset = Publication.objects.all()
    serializer_class = PublicationSerializer

class HumanDevelopmentIndexViewSet(viewsets.ModelViewSet):
    queryset = HumanDevelopmentIndex.objects.all()
    serializer_class = HumanDevelopmentIndexSerializer

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_bookmark(request):
    """
    Menambahkan item ke bookmark pengguna.
    Membutuhkan 'content_type_name' ('news', 'infographic', 'publication') dan 'object_id'.
    """
    serializer = BookmarkSerializer(data=request.data)
    if serializer.is_valid():
        # Memeriksa apakah bookmark sudah ada
        content_type = serializer.validated_data['content_type']
        object_id = serializer.validated_data['object_id']
        if Bookmark.objects.filter(user=request.user, content_type=content_type, object_id=object_id).exists():
            return Response({"error": "Item ini sudah ada di bookmark Anda."}, status=status.HTTP_409_CONFLICT)
        
        # Menyimpan bookmark dengan user yang sedang login
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def view_bookmarks(request):
    """
    Menampilkan semua bookmark milik pengguna yang sedang login.
    """
    bookmarks = Bookmark.objects.filter(user=request.user)
    serializer = BookmarkSerializer(bookmarks, many=True, context={'request': request})
    return Response(serializer.data)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_bookmark(request, pk):
    bookmark = get_object_or_404(Bookmark, pk=pk, user=request.user)
    bookmark.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['GET'])
def sync_bps_news(request):
    try:
        created_count, updated_count = BPSNewsService.sync_news()
        return Response({
            "status": "success",
            "message": f"Sinkronisasi berita selesai. Data baru: {created_count}, data diperbarui: {updated_count}.",
            "details": {"created": created_count, "updated": updated_count}
        })
    except Exception as e:
        return Response({
            "status": "error",
            "message": str(e)
        }, status=500)
        
@api_view(['GET'])
def sync_bps_infographic(request):
    try:
        created_count, updated_count = BPSInfographicService.sync_infographic()
        return Response({
            "status": "success",
            "message": f"Sinkronisasi infografis selesai. Data baru: {created_count}, data diperbarui: {updated_count}.",
            "details": {"created": created_count, "updated": updated_count}
        })
    except Exception as e:
        return Response({
            "status": "error",
            "message": str(e)
        }, status=500)
        
@api_view(['GET'])
def sync_bps_publication(request):
    try:
        created_count, updated_count = BPSPublicationService.sync_publication()
        return Response({
            "status": "success",
            "message": f"Sinkronisasi publikasi selesai. Data baru: {created_count}, data diperbarui: {updated_count}.",
            "details": {"created": created_count, "updated": updated_count}
        })
    except Exception as e:
        return Response({
            "status": "error",
            "message": str(e)
        }, status=500)

@api_view(['GET'])
def sync_human_development_index(request):
    try:
        created_count, updated_count = IPMService.sync_ipm()
        return Response({
            "status": "success",
            "message": f"Sinkronisasi IPM selesai. Data baru: {created_count}, data diperbarui: {updated_count}.",
            "details": {"created": created_count, "updated": updated_count}
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
        # Lakukan login untuk membuat sesi Django
        auth_login(request, user)
        return Response({'token': token.key, 'message': 'Login successful'}, status=status.HTTP_200_OK)

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
    dataNews = News.objects.order_by('-release_date', '-news_id')[:5]
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
    dataNewss = News.objects.order_by('-release_date')
    countNews = News.objects.count()
    dataNews = News.objects.order_by('-release_date', '-news_id')[:5]
    dataNewsLatest = dataNews
    dataInfographic = Infographic.objects.order_by('-id')[:5]
    dataInfographics = Infographic.objects.order_by('-id')
    dataInfographicLatest = Infographic.objects.order_by('-id')[:4]
    dataPublication = Publication.objects.order_by('-date')[:5]
    dataPublications = Publication.objects.order_by('-date')
    dataPublicationsLatest = Publication.objects.order_by('-date')[:5]

    # --- Logika untuk mengambil Bookmark ---
    bookmarked_items = []
    if request.user.is_authenticated:
        # Ambil semua bookmark milik pengguna, dengan prefetch ke content_object
        user_bookmarks = Bookmark.objects.filter(user=request.user).select_related('content_type')

        for bookmark in user_bookmarks:
            item = bookmark.content_object
            if item:
                item_url = '#' # URL default jika tidak ditemukan
                # Tentukan URL berdasarkan tipe model
                if isinstance(item, News):
                    # Arahkan ke halaman daftar berita dengan anchor ke ID item
                    item_url = reverse('news') + f'#news-{item.pk}'
                elif isinstance(item, Infographic):
                    item_url = reverse('infographics') + f'#infographic-{item.pk}'
                elif isinstance(item, Publication):
                    item_url = reverse('publications') + f'#publication-{item.pk}'
                
                bookmarked_items.append({
                    'title': item.title,
                    'url': item_url,
                })
    # --- Akhir dari logika Bookmark ---

    context = {
        'countNews':countNews,
        'dataNewss':dataNewss,
        'dataNews': dataNews,
        'dataInfographic': dataInfographic,
        'dataInfographics': dataInfographics,
        'dataInfographicLatest': dataInfographicLatest,
        'dataPublication': dataPublication,
        'dataPublications': dataPublications,
        'dataNewsLatest': dataNewsLatest,
        'dataPublicationsLatest': dataPublicationsLatest,
        'bookmarked_items': bookmarked_items, # Tambahkan bookmark ke context
    }
    return render(request, 'dashboard/dashboard.html', context)

def infographics(request):
    
    """Merender halaman infografis."""
    infographics_list = Infographic.objects.all().order_by('-id')
    
    # --- Penambahan untuk Bookmark ---
    if request.user.is_authenticated:
        # Dapatkan ContentType untuk model Infographic
        infographic_content_type = ContentType.objects.get_for_model(Infographic)
        # Dapatkan semua bookmark pengguna untuk infografis
        user_bookmarks = Bookmark.objects.filter(
            user=request.user, 
            content_type=infographic_content_type
        ).values('object_id', 'id')
        # Buat set berisi ID infografis yang sudah di-bookmark dan map ke ID bookmark
        bookmarked_infographics = {item['object_id']: item['id'] for item in user_bookmarks}
        for infographic in infographics_list:
            infographic.bookmark_id = bookmarked_infographics.get(infographic.id)

    paginator = Paginator(infographics_list, 12)
    page = request.GET.get('page', 1)
    
    try:
        infographics_data = paginator.page(page)
    except PageNotAnInteger:
        infographics_data = paginator.page(1)
    except EmptyPage:
        infographics_data = paginator.page(paginator.num_pages)
    
    # Get latest news for sidebar
    latest_news = News.objects.order_by('-release_date', '-news_id')[:5]
    news_count = News.objects.count()
    
    context = {
        'dataInpographic': infographics_data,
        'dataNews': latest_news,
        'countNews': news_count,
        'countInfographic': Infographic.objects.count(),
        'page_title': 'Infographics',
        'user': request.user,
    }

    return render(request, 'dashboard/infographics.html', context)

def publications(request):
    """Merender halaman publikasi."""
    publications_list = Publication.objects.all().order_by('-date')

    # --- Penambahan untuk Bookmark ---
    if request.user.is_authenticated:
        # Dapatkan ContentType untuk model Publication
        publication_content_type = ContentType.objects.get_for_model(Publication)
        # Dapatkan semua bookmark pengguna untuk publikasi
        user_bookmarks = Bookmark.objects.filter(
            user=request.user, 
            content_type=publication_content_type
        ).values('object_id', 'id')
        # Buat set berisi ID publikasi yang sudah di-bookmark dan map ke ID bookmark
        bookmarked_publications = {int(item['object_id']): item['id'] for item in user_bookmarks}
        for publication in publications_list:
            publication.bookmark_id = bookmarked_publications.get(int(publication.pub_id))

    paginator = Paginator(publications_list, 10)
    page = request.GET.get('page', 1)
    
    try:
        publications_data = paginator.page(page)
    except PageNotAnInteger:
        publications_data = paginator.page(1)
    except EmptyPage:
        publications_data = paginator.page(paginator.num_pages)
    
    # Get latest news for sidebar
    latest_news = News.objects.order_by('-release_date', '-news_id')[:5]
    news_count = News.objects.count()
    
    context = {
        'dataPublication': publications_data,
        'dataNews': latest_news,
        'countNews': news_count,
        'countPublication': Publication.objects.count(),
        'page_title': 'Publications',
        'user': request.user,
    }

    return render(request, 'dashboard/publications.html', context)

def news(request):
    # Get filters and search query
    search_query = request.GET.get('search', '').strip()
    category_id_filter = request.GET.get('category_id', '').strip()
    sort_order = request.GET.get('sort', 'latest')
    
    # Start with all news
    news_list = News.objects.all()

    # --- Penambahan untuk Bookmark ---
    if request.user.is_authenticated:
        # Dapatkan ContentType untuk model News
        news_content_type = ContentType.objects.get_for_model(News)
        # Dapatkan semua bookmark pengguna untuk berita
        user_bookmarks = Bookmark.objects.filter(
            user=request.user, 
            content_type=news_content_type
        ).values('object_id', 'id')
        # Buat set berisi ID berita yang sudah di-bookmark dan map ke ID bookmark
        bookmarked_news = {item['object_id']: item['id'] for item in user_bookmarks}
        for news_item in news_list:
            news_item.bookmark_id = bookmarked_news.get(news_item.news_id)
    
    # Apply search filter
    if search_query:
        news_list = news_list.filter(
            Q(title__icontains=search_query) |
            Q(content__icontains=search_query) |
            Q(category_name__icontains=search_query)
        )
    
    # Apply category ID filter
    if category_id_filter:
        news_list = news_list.filter(category_id=category_id_filter)
    
    # Apply sorting
    if sort_order == 'oldest':
        news_list = news_list.order_by('release_date', 'news_id')
    else:  # latest (default)
        news_list = news_list.order_by('-release_date', '-news_id')
    
    # Get total count after filtering
    total_count = news_list.count()
    
    # Get available categories for filter dropdown (using category_id)
    available_categories = News.objects.filter(
        category_id__isnull=False,
        category_name__isnull=False
    ).values('category_id', 'category_name').distinct().order_by('category_name')
    
    # Pagination - 15 items per page
    paginator = Paginator(news_list, 15)
    page = request.GET.get('page', 1)
    
    try:
        news_data = paginator.page(page)
    except PageNotAnInteger:
        news_data = paginator.page(1)
    except EmptyPage:
        news_data = paginator.page(paginator.num_pages)
    
    context = {
        'dataNewss': news_data,
        'countNews': News.objects.count(),
        'filtered_count': total_count,
        'search_query': search_query,
        'category_id_filter': category_id_filter,
        'sort_order': sort_order,
        'available_categories': available_categories,
        'page_title': 'News',
        'user': request.user,
    }
    
    return render(request, 'dashboard/news.html', context)

# ======= Tampilan Indikator Strategis Kota Surabaya =======
def ipm(request):
    
    return render(request, 'dashboard/indikator/IPM.html')

def contact_us(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            try:
                name = form.cleaned_data['name']
                surname = form.cleaned_data['surname']
                email = form.cleaned_data['email']
                message = form.cleaned_data['message']
                
                subject = f"Pesan Baru dari {name} {surname} melalui Aastabaya"
                email_message = (
                    f"Anda menerima pesan baru dari formulir kontak Aastabaya:\n\n"
                    f"Nama: {name} {surname}\n"
                    f"Email: {email}\n\n"
                    f"Pesan:\n{message}"
                )

                send_mail(
                    subject,
                    email_message,
                    settings.EMAIL_HOST_USER,  # Alamat pengirim
                    [settings.EMAIL_HOST_USER], # Alamat penerima
                )
                messages.success(request, 'Pesan Anda telah berhasil terkirim!')
            except Exception as e:
                messages.error(request, 'Terjadi kesalahan saat mengirim pesan. Silakan coba lagi.')
                print(f"Error sending email: {e}") # Log error ke konsol
        else:
            # Jika formulir tidak valid, beri tahu pengguna
            messages.warning(request, 'Harap perbaiki kesalahan di bawah ini dan kirimkan formulir lagi.')
            # Di masa mendatang, Anda bisa merender ulang formulir dengan error
            
    return redirect('index')