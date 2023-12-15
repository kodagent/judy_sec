from record.models import Upload
from rest_framework import serializers


class UploadSerializer(serializers.ModelSerializer):
    extension_short = serializers.CharField(read_only=True)

    class Meta:
        model = Upload
        fields = ['id', 'title', 'file', 'updated_date', 'upload_time', 'extension_short']
        read_only_fields = ['updated_date', 'upload_time']

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        return Upload.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.title = validated_data.get('title', instance.title)
        instance.file = validated_data.get('file', instance.file)
        instance.save()
        return instance


class UploadEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = Upload
        fields = ['title', 'file']


class UploadDeleteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Upload
        fields = []