from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.db import IntegrityError
from django.db.models import ProtectedError
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404
from django.views.decorators.cache import never_cache

from actstream.models import Action

from .forms import BookmarkForm, BookmarkFolderForm, UpdateBookmarkForm
from .models import Bookmark, Folder


@never_cache
@login_required
def add_bookmark(request, action_pk):
    context = dict()
    bookmarks = request.user.bookmark_set.filter(folder__isnull=True)
    bookmarks_folders = request.user.folder_set.all()

    action = Action.objects.get(pk=action_pk)
    if request.method == 'POST':
        form = BookmarkForm(request.POST)
        if form.is_valid():
            # Now save the bookmark
            bookmark, created = Bookmark.objects.get_or_create(
                object_pk=action.action_object.pk,
                content_type=action.action_object_content_type,
                owner=request.user
            )
            bookmark.name = form.cleaned_data['name']
            bookmark.folder = form.cleaned_data['folder']
            bookmark.save()
            # TODO: change messaging if object already bookmarked?
            messages.success(request, 'Your bookmark was saved!')
            # Now return a success message
            context['messages'] = render_to_string('bootstrap3/messages.html', {}, request=request)
            context['form'] = render_to_string(
                'bookmarks/_add_bookmark.html',
                {
                    'action': action,
                },
                request=request
            )
        else:
            context['form'] = render_to_string(
                'bookmarks/_add_bookmark_form.html',
                {
                    'action': action,
                    'form': form,
                    'bookmarks_folders': bookmarks_folders,
                    'bookmarks': bookmarks,
                },
                request=request)
    else:
        form = BookmarkForm(initial={
            'object_pk': action.action_object.pk,
            'content_type': action.action_object_content_type,
        })
        context['form'] = render_to_string(
            'bookmarks/_add_bookmark_form.html',
            {
                'form': form,
                'bookmarks_folders': bookmarks_folders,
                'bookmarks': bookmarks,
            },
            request=request
        )
    return JsonResponse(context)


@never_cache
@login_required
def update_bookmark(request, bookmark_pk):
    context = dict()
    if request.method == 'POST':
        form = UpdateBookmarkForm(request.POST)
        if form.is_valid():
            try:
                bookmark = Bookmark.objects.get(pk=bookmark_pk, owner=request.user)
                bookmark.name = form.cleaned_data['name']
                bookmark.folder = form.cleaned_data['folder']
                bookmark.save()
                context['error'] = False
                messages.success(request, 'Your bookmark was saved!')
            except ObjectDoesNotExist:
                context['error'] = True
                messages.error(request, 'Bookmark does not exist.')
        else:
            context['error'] = True
            messages.error(request, 'Error occurred.')

    context['messages'] = render_to_string('bootstrap3/messages.html', {}, request=request)
    return JsonResponse(context)


@never_cache
@login_required
def delete_bookmark(request, bookmark_pk):
    if request.method == 'POST':
        context = {}
        bookmark = get_object_or_404(Bookmark, pk=bookmark_pk, owner=request.user)
        # Grab the action before we delete:
        action = bookmark.content_object.action_object_actions.first()
        # Now delete the bookmark:
        bookmark.delete()
        context['form'] = render_to_string(
            'bookmarks/_add_bookmark.html',
            {
                'action': action,
            },
            request=request
        )
        context['error'] = False
        messages.success(request, 'Your bookmark was removed.')
        context['messages'] = render_to_string('bootstrap3/messages.html', {}, request=request)
        return JsonResponse(context)


@never_cache
@login_required
def add_bookmark_folder(request):
    if request.method == 'POST':
        form = BookmarkFolderForm(request.POST)
        context = {}
        if form.is_valid():
            folder_name = form.cleaned_data['name']
            folder = Folder(name=folder_name, user=request.user)
            try:
                folder.save()
                context['error'] = False
                context['folder_id'] = folder.pk
                context['folder_name'] = folder.name
                messages.success(request, 'Folder added.')
            except IntegrityError:
                context['error'] = True
                messages.error(request, 'Folder with the name {0} already exists'.format(folder_name))
        else:
            context['error'] = True
            messages.error(request, 'Error occurred.')

        context['messages'] = render_to_string('bootstrap3/messages.html', {}, request=request)
        return JsonResponse(context)


@never_cache
@login_required
def delete_bookmark_folder(request, folder_pk):
    if request.method == 'POST':
        context = {}
        try:
            Folder.objects.filter(pk=folder_pk, user=request.user).delete()
            context['error'] = False
            messages.success(request, 'Bookmarks folder deleted.')
        except ProtectedError:
            context['error'] = True
            messages.error(request, 'The folder contains bookmarks.')

        context['messages'] = render_to_string('bootstrap3/messages.html', {}, request=request)
        return JsonResponse(context)
