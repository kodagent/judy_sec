from django.contrib import messages
from django.http import FileResponse, Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import DeleteView, ListView, UpdateView, View
# from docx2pdf import convert
from rest_framework import generics
from rest_framework.views import APIView

from record import forms, models, serializers


# @login_required
class FileUploadView(APIView):
    """
    This view handles file uploads. It does not interact with the database directly,
    hence does not use a serializer_class. Instead, it relies on custom utility functions.
    """
    serializer_class = None

    template_name = "record/upload_file.html"

    def get(self, request, *args, **kwargs):
        form = forms.UploadFormFile()
        context = {"form": form}
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form = forms.UploadFormFile(request.POST, request.FILES)
        if form.is_valid():
            upload = form.save(commit=False)
            upload.user = request.user
            upload.save()
            serializer = serializers.UploadSerializer(upload)
            context = {"result": serializer.data}
            messages.success(request, (request.POST.get('title') + ' has been uploaded.'))
            return render(request, self.template_name, context)
        else:
            context = {"form": form}
            return render(request, self.template_name, context)


class UploadUpdateView(UpdateView):
    model = models.Upload
    fields = ['title', 'file']
    template_name = 'record/upload_file.html' 
    
    def form_valid(self, form):
        messages.success(self.request, 'Document has been updated.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('file_view')
    

class UploadDeleteView(DeleteView):
    model = models.Upload
    template_name = 'record/file_view.html'

    def get_success_url(self):
        messages.success(self.request, 'File deleted successfully.')
        return reverse_lazy('file_view')


# class UploadEditAPIView(generics.RetrieveUpdateAPIView):
#     queryset = models.Upload.objects.all()
#     serializer_class = serializers.UploadEditSerializer

#     def get_object(self):
#         queryset = self.get_queryset()
#         obj = get_object_or_404(queryset, pk=self.kwargs["pk"])
#         return obj


# class UploadDeleteAPIView(generics.DestroyAPIView):
#     queryset = models.Upload.objects.all()
#     serializer_class = serializers.UploadDeleteSerializer

#     def get_object(self):
#         queryset = self.get_queryset()
#         obj = get_object_or_404(queryset, pk=self.kwargs["pk"])
#         return obj


class FileView(ListView):
    template_name = "record/file_view.html"
    queryset = models.Upload.objects.all()

    # If you need to pass additional context data to the template
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add extra context variables if needed
        return context
