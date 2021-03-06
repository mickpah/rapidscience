from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render, Http404
from django.views.decorators.cache import never_cache

from actstream import action
from PIL import Image
from taggit.models import Tag

from rlp.discussions.models import ThreadedComment
from rlp.discussions.shortcuts import get_comments_for_instance
from .forms import FileForm, ImageForm, LinkForm, VideoForm
from .models import Document
from rlp.projects.models import Project


@never_cache
@login_required
def add_document(request, pk, slug, doc_pk=None, template_name='documents/add_document.html'):
    project = get_object_or_404(Project, pk=pk, slug=slug)
    if doc_pk:
        document = get_object_or_404(Document, pk=doc_pk, project=project)
    else:
        document = None
    form_class = FileForm
    if request.method == 'POST':
        # Make a copy so we can manipulate
        POST = request.POST.copy()
        # Remove tags, if present
        tag_ids = POST.pop('tags', [])
        if 'upload' in request.FILES:
            try:
                Image.open(request.FILES['upload'])
                request.FILES['upload'].seek(0)
                form_class = ImageForm
            except IOError:
                pass
        if request.FILES:
            form = form_class(POST, request.FILES, instance=document)
        else:
            form = form_class(POST, instance=document)
        if form.is_valid():
            with transaction.atomic():
                document = form.save(commit=False)
                document.owner = request.user
                document.project = project
                document.save()
                if tag_ids:
                    try:
                        tags = Tag.objects.filter(id__in=tag_ids)
                    except:
                        tags = []
                    document.tags.set(*tags)
                    # Trigger any post-save signals (e.g. Haystack's real-time indexing)
                    document.save()
                if doc_pk:
                    message = "Updated successfully!"
                else:
                    new_action = action.send(request.user, verb='uploaded', action_object=document, target=project)
                    message = "Your upload was successful!"
                    # Send email notification
                    project.notify_members(
                        '{}: A new document was added'.format(settings.SITE_PREFIX.upper()),
                        {'action': new_action[0][1]}
                    )
                messages.success(request, message)
            return redirect(document.get_absolute_url())
        else:
            messages.error(request, "Check the errors below.")

    else:
        initial = {}
        if document and document.tags.count():
            initial['tags'] = document.tags.all()
        form = form_class(instance=document, initial=initial)
    context = {
        'form': form,
        'document': document,
        'project': project,
        'tab': 'documents',
    }
    return render(request, template_name, context)


@never_cache
@login_required
def add_link(request, pk, slug, doc_pk=None, template_name='documents/add_link.html'):
    project = get_object_or_404(Project, pk=pk, slug=slug)
    if doc_pk:
        document = get_object_or_404(Document, pk=doc_pk, project=project)
    else:
        document = None
    if request.method == 'POST':
        # Make a copy so we can manipulate
        POST = request.POST.copy()
        # Remove tags, if present
        tag_ids = POST.pop('tags', [])
        form = LinkForm(POST, instance=document)
        if form.is_valid():
            with transaction.atomic():
                link = form.save(commit=False)
                link.owner = request.user
                link.project = project
                link.save()
                if tag_ids:
                    try:
                        tags = Tag.objects.filter(id__in=tag_ids)
                    except:
                        tags = []
                    link.tags.set(*tags)
                    # Trigger any post-save signals (e.g. Haystack's real-time indexing)
                    link.save()
                if doc_pk:
                    message = "Updated successfully!"
                else:
                    new_action = action.send(request.user, verb='added', action_object=link, target=project)
                    message = "Your link was successfully added!"
                    # Send email notification
                    project.notify_members(
                        '{}: A new link was added'.format(settings.SITE_PREFIX.upper()),
                        {'action': new_action[0][1]}
                    )
                messages.success(request, message)
            return redirect(link.get_absolute_url())
        else:
            messages.error(request, "Check the errors below.")
    else:
        initial = {}
        if document and document.tags.count():
            initial['tags'] = document.tags.all()
        form = LinkForm(instance=document, initial=initial)
    context = {
        'form': form,
        'document': document,
        'project': project,
        'tab': 'documents',
    }
    return render(request, template_name, context)


@never_cache
@login_required
def add_video(request, pk, slug, doc_pk=None, template_name='documents/add_video.html'):
    project = get_object_or_404(Project, pk=pk, slug=slug)
    if doc_pk:
        document = get_object_or_404(Document, pk=doc_pk, project=project)
    else:
        document = None
    if request.method == 'POST':
        # Make a copy so we can manipulate
        POST = request.POST.copy()
        # Remove tags, if present
        tag_ids = POST.pop('tags', [])
        form = VideoForm(POST, instance=document)
        if form.is_valid():
            with transaction.atomic():
                video = form.save(commit=False)
                video.owner = request.user
                video.project = project
                video.save()
                if tag_ids:
                    try:
                        tags = Tag.objects.filter(id__in=tag_ids)
                    except:
                        tags = []
                    video.tags.set(*tags)
                    # Trigger any post-save signals (e.g. Haystack's real-time indexing)
                    video.save()
                if doc_pk:
                    message = "Updated successfully!"
                else:
                    new_action = action.send(request.user, verb='added', action_object=video, target=project)
                    message = "Your video was successfully added!"
                    # Send email notification
                    project.notify_members(
                        '{}: A new video was added'.format(settings.SITE_PREFIX.upper()),
                        {'action': new_action[0][1]}
                    )
                messages.success(request, message)
            return redirect(video.get_absolute_url())
        else:
            messages.error(request, "Check the errors below.")
    else:
        initial = {}
        if document and document.tags.count():
            initial['tags'] = document.tags.all()
        form = VideoForm(instance=document, initial=initial)
    context = {
        'form': form,
        'document': document,
        'project': project,
        'tab': 'documents',
    }
    return render(request, template_name, context)


@never_cache
@login_required
def document_detail(request, pk, slug, doc_pk, template_name='documents/document_detail.html'):
    project = get_object_or_404(Project, pk=pk, slug=slug)
    document = get_object_or_404(Document, pk=doc_pk, project=project)
    context = {
        'document': document,
        'project': project,
        'tab': 'documents',
        'comment_list': get_comments_for_instance(document)
    }
    return render(request, template_name, context)


@never_cache
@login_required
def document_edit(request, pk, slug, doc_pk, doc_type):
    if doc_type in ['file', 'image']:
        return add_document(request, pk, slug, doc_pk)
    elif doc_type == 'link':
        return add_link(request, pk, slug, doc_pk)
    elif doc_type == 'video':
        return add_video(request, pk, slug, doc_pk)
    raise Http404


@never_cache
@login_required
def document_delete(request, pk, slug, doc_pk, template_name='documents/delete.html'):
    project = get_object_or_404(Project, pk=pk, slug=slug)
    document = get_object_or_404(Document, pk=doc_pk, project=project)
    if request.user != document.owner:
        messages.error(request, "You do not have permission to delete this.")
        return redirect(document.get_absolute_url())
    if request.method == 'POST':
        title = document.title
        ctype = ContentType.objects.get_for_model(document.__class__)
        comment_ctype = ContentType.objects.get_for_model(ThreadedComment)
        with transaction.atomic():
            # Recursively find all comments and replies for this document and delete them.
            # TODO: turn this into a model manager method
            qs_to_delete = ThreadedComment.objects.filter(object_pk=document.id, content_type=ctype)
            comment_children_ids = list(qs_to_delete.values_list('id', flat=True))
            qs_to_delete.delete()
            while comment_children_ids:
                qs_to_delete = ThreadedComment.objects.filter(
                    content_type=comment_ctype, parent_id__in=comment_children_ids)
                comment_children_ids = list(qs_to_delete.values_list('id', flat=True))
                qs_to_delete.delete()
            document.delete()
        messages.success(request, "Successfully deleted '{}'".format(title))
        return redirect(project.get_documents_url())
    context = {
        'document': document,
        'project': project,
        'tab': 'documents',
    }
    return render(request, template_name, context)
