"""
URL configuration for _moldx project.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/topics/http/urls/

Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, include


urlpatterns = [
    path('api/', include([
        path('', include('identity.urls')),
        path('', include('masterdata.urls')),
        path('', include('filecenter.urls')),
        path('', include('reporting.urls')),
        path('', include('process.urls')),
    ])),
]