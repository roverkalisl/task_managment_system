from django.contrib import admin
from django.urls import include, path

# 🔹 Accounts
from accounts.views import login_view, register_view, logout_view, create_user_view

# 🔹 Task
from task.views import dashboard, tasks_view, submit_task, create_task_view

# 🔹 Wallet
from wallet.views import wallet_view, withdraw_request

# 🔹 Media (image upload)
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    # 🔐 Auth
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('create-user/', create_user_view, name='create_user'),
    path('logout/', logout_view, name='logout'),

    # 🏠 Dashboard
    path('', dashboard, name='dashboard'),

    # 📋 Tasks
    path('tasks/', tasks_view, name='tasks'),
    path('tasks/create/', create_task_view, name='create_task'),
    path('submit/<int:task_id>/', submit_task, name='submit_task'),

    # Mobile / API (DRF)
    path('api/', include('api.urls')),

    # 💰 Wallet
    path('wallet/', wallet_view, name='wallet'),
    path('withdraw/', withdraw_request, name='withdraw'),

    # 🧑‍💼 Admin
    path('admin/', admin.site.urls),
]

# 📸 Media files (for screenshot upload)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)