from rest_framework import serializers
from Authenticate.models import Painting

class PaintingSerializer(serializers.ModelSerializer):
    owner_username = serializers.CharField(source='owner.username', read_only=True)

    class Meta:
        model = Painting
        fields = [
            'id', 'owner', 'owner_username', 'frame_number', 'title', 'description',
            'image_url', 'thumbnail_url', 'visibility', 'tags', 'has_image',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'owner', 'frame_number', 'has_image', 'created_at', 'updated_at']

class PaintingUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Painting
        fields = ['title', 'description', 'visibility', 'tags']
