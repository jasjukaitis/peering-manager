from contextlib import contextmanager

from django.db.models.signals import m2m_changed, post_save, pre_delete

from extras.webhooks import flush_webhooks
from peering_manager import thread_locals
from peering_manager.request_context import set_request
from utils.signals import (
    clear_webhook_queue,
    clear_webhooks,
    handle_changed_object,
    handle_deleted_object,
)


@contextmanager
def change_logging(request):
    """
    Enables change logging by connecting the appropriate signals to their receivers
    before code is run, and disconnecting them afterward.
    """
    set_request(request)
    thread_locals.webhook_queue = []

    # Connect our receivers to the post_save and post_delete signals
    post_save.connect(handle_changed_object, dispatch_uid="handle_changed_object")
    m2m_changed.connect(handle_changed_object, dispatch_uid="handle_changed_object")
    pre_delete.connect(handle_deleted_object, dispatch_uid="handle_deleted_object")
    clear_webhooks.connect(clear_webhook_queue, dispatch_uid="clear_webhook_queue")

    yield

    # Disconnect change logging signals. This is necessary to avoid recording any
    # errant changes during test cleanup
    post_save.disconnect(handle_changed_object, dispatch_uid="handle_changed_object")
    m2m_changed.disconnect(handle_changed_object, dispatch_uid="handle_changed_object")
    pre_delete.disconnect(handle_deleted_object, dispatch_uid="handle_deleted_object")
    clear_webhooks.disconnect(clear_webhook_queue, dispatch_uid="clear_webhook_queue")

    # Flush queued webhooks to RQ
    flush_webhooks(thread_locals.webhook_queue)
    del thread_locals.webhook_queue

    # Clear the request from thread-local storage
    set_request(None)
