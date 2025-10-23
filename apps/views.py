from django.shortcuts import render
from .services.API_service import get_news_data
from .services.API_service import get_inpographic_data
from .services.API_service import get_publication_data


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
