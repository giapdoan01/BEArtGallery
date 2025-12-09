from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q, Max
from django.shortcuts import get_object_or_404
import cloudinary.uploader
from Authenticate.models import Painting
from .serializers import PaintingSerializer, PaintingUpdateSerializer

# GET /api/paintings - Lấy danh sách paintings
@api_view(['GET'])
@permission_classes([IsAuthenticatedOrReadOnly])
def get_paintings(request):
    paintings = Painting.objects.all()
    
    # Filter theo ownerId
    owner_id = request.GET.get('ownerId')
    if owner_id:
        paintings = paintings.filter(owner_id=owner_id)
    
    # Filter theo visibility
    visibility = request.GET.get('visibility')
    if visibility:
        paintings = paintings.filter(visibility=visibility)
    
    # Filter theo has_image
    has_image = request.GET.get('hasImage')
    if has_image == 'true':
        paintings = paintings.filter(has_image=True)
    elif has_image == 'false':
        paintings = paintings.filter(has_image=False)
    
    # Filter theo tag
    tag = request.GET.get('tag')
    if tag:
        paintings = paintings.filter(tags__contains=[tag])
    
    # Search theo title/description
    search = request.GET.get('search')
    if search:
        paintings = paintings.filter(
            Q(title__icontains=search) | Q(description__icontains=search)
        )
    
    # Phân trang
    page = int(request.GET.get('page', 1))
    limit = int(request.GET.get('limit', 10))
    start = (page - 1) * limit
    end = start + limit
    
    total = paintings.count()
    paintings_page = paintings[start:end]
    
    serializer = PaintingSerializer(paintings_page, many=True)
    
    return Response({
        'items': serializer.data,
        'meta': {
            'total': total,
            'page': page,
            'limit': limit,
            'totalPages': (total + limit - 1) // limit
        }
    })

# POST /api/paintings/create-frame - Tạo khung tranh mới
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_new_frame(request):
    """
    Tạo khung tranh mới với frame_number = max + 1
    Body: { "title": "My Frame", "description": "...", "visibility": "private", "tags": [] }
    """
    # Tìm frame_number lớn nhất của user
    max_frame = Painting.objects.filter(owner=request.user).aggregate(Max('frame_number'))['frame_number__max']
    new_frame_number = (max_frame or 0) + 1
    
    # Tạo painting mới
    painting = Painting.objects.create(
        owner=request.user,
        frame_number=new_frame_number,
        title=request.data.get('title', f'Frame {new_frame_number}'),
        description=request.data.get('description', ''),
        visibility=request.data.get('visibility', 'private'),
        tags=request.data.get('tags', []),
        has_image=False
    )
    
    return Response(PaintingSerializer(painting).data, status=status.HTTP_201_CREATED)

# POST /api/paintings/{frame_number}/upload-image - Upload ảnh vào khung
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_image_to_frame(request, frame_number):
    """
    Upload ảnh vào khung tranh
    - Xóa ảnh cũ nếu có
    - Upload ảnh mới vào folder: paintings/{userId}/{frameNumber}/image.jpg
    """
    painting = get_object_or_404(Painting, owner=request.user, frame_number=frame_number)
    
    file = request.FILES.get('file')
    if not file:
        return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Xóa ảnh cũ nếu có
        if painting.has_image and painting.cloudinary_public_id:
            try:
                cloudinary.uploader.destroy(painting.cloudinary_public_id)
            except Exception as e:
                print(f"Error deleting old image: {e}")
        
        # Upload ảnh mới vào folder: paintings/{userId}/{frameNumber}/image
        folder_path = f"paintings/{request.user.id}/{frame_number}"
        upload_result = cloudinary.uploader.upload(
            file,
            folder=folder_path,
            public_id="image",  # Tên file cố định
            overwrite=True,
            transformation=[
                {'width': 2048, 'height': 2048, 'crop': 'limit'},
                {'quality': 'auto'}
            ]
        )
        
        # Tạo thumbnail
        thumbnail_url = cloudinary.CloudinaryImage(upload_result['public_id']).build_url(
            width=300, height=300, crop='fill'
        )
        
        # Cập nhật painting
        painting.image_url = upload_result['secure_url']
        painting.thumbnail_url = thumbnail_url
        painting.cloudinary_public_id = upload_result['public_id']
        painting.has_image = True
        painting.save()
        
        serializer = PaintingSerializer(painting)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# GET /api/paintings/{frame_number} - Lấy chi tiết painting
@api_view(['GET'])
@permission_classes([IsAuthenticatedOrReadOnly])
def get_painting_detail(request, frame_number):
    # Lấy owner_id từ query params nếu có
    owner_id = request.GET.get('ownerId')
    
    if owner_id:
        painting = get_object_or_404(Painting, owner_id=owner_id, frame_number=frame_number)
    else:
        # Nếu không có ownerId, lấy của user hiện tại
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
        painting = get_object_or_404(Painting, owner=request.user, frame_number=frame_number)
    
    # Kiểm tra quyền xem nếu private
    if painting.visibility == 'private' and (not request.user.is_authenticated or painting.owner != request.user):
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
    
    serializer = PaintingSerializer(painting)
    return Response(serializer.data)

# PUT /api/paintings/{frame_number}/update - Cập nhật metadata
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_painting(request, frame_number):
    painting = get_object_or_404(Painting, owner=request.user, frame_number=frame_number)
    
    serializer = PaintingUpdateSerializer(painting, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(PaintingSerializer(painting).data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# DELETE /api/paintings/{frame_number}/delete-image - Xóa ảnh, giữ khung
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_image_from_frame(request, frame_number):
    painting = get_object_or_404(Painting, owner=request.user, frame_number=frame_number)
    
    if not painting.has_image:
        return Response({'error': 'No image to delete'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Xóa ảnh trên Cloudinary
        if painting.cloudinary_public_id:
            cloudinary.uploader.destroy(painting.cloudinary_public_id)
        
        # Reset image fields
        painting.image_url = None
        painting.thumbnail_url = None
        painting.cloudinary_public_id = None
        painting.has_image = False
        painting.save()
        
        return Response(PaintingSerializer(painting).data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# DELETE /api/paintings/{frame_number}/delete - Xóa cả khung
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_painting(request, frame_number):
    painting = get_object_or_404(Painting, owner=request.user, frame_number=frame_number)
    
    # Không cho xóa 10 khung mặc định (1-10)
    if frame_number <= 10:
        return Response({'error': 'Cannot delete default frames (1-10)'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Xóa ảnh trên Cloudinary nếu có
        if painting.has_image and painting.cloudinary_public_id:
            try:
                cloudinary.uploader.destroy(painting.cloudinary_public_id)
                # Xóa folder
                folder_path = f"paintings/{request.user.id}/{frame_number}"
                cloudinary.api.delete_folder(folder_path)
            except Exception as e:
                print(f"Error deleting cloudinary resources: {e}")
        
        painting.delete()
        return Response({'message': 'Painting deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
