from django.urls import path
from . import views

urlpatterns = [
    # Danh sách
    path('', views.get_paintings, name='get_paintings'),  # GET /api/paintings
    
    # Tạo frame mới
    path('create-frame/', views.create_new_frame, name='create_new_frame'),  # POST /api/paintings/create-frame
    
    # Chi tiết frame theo số
    path('<int:frame_number>/', views.get_painting_detail, name='get_painting_detail'),  # GET /api/paintings/{frame_number}
    
    # Upload/Delete ảnh
    path('<int:frame_number>/upload-image/', views.upload_image_to_frame, name='upload_image_to_frame'),  # POST /api/paintings/{frame_number}/upload-image
    path('<int:frame_number>/delete-image/', views.delete_image_from_frame, name='delete_image_from_frame'),  # DELETE /api/paintings/{frame_number}/delete-image
    
    # Update/Delete frame
    path('<int:frame_number>/update/', views.update_painting, name='update_painting'),  # PUT /api/paintings/{frame_number}/update
    path('<int:frame_number>/delete/', views.delete_painting, name='delete_painting'),  # DELETE /api/paintings/{frame_number}/delete
]
