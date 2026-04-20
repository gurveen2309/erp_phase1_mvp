from __future__ import annotations

from django.contrib import admin, messages
from django.shortcuts import redirect

from governance.models import ApprovalRequest
from governance.services import create_approval_request, get_content_type_for_model, log_audit, serialize_instance


class FinanceApprovalAdminMixin(admin.ModelAdmin):
    approval_redirect_name = "governance:approval-queue"

    def has_direct_finance_change_permission(self, request) -> bool:
        return request.user.is_superuser or request.user.has_perm("governance.approve_finance_change")

    def _build_form(self, request, obj=None):
        form_class = self.get_form(request, obj)
        return form_class(request.POST, request.FILES, instance=obj)

    def _submit_change_request(self, request, *, action_type: str, obj=None):
        form = self._build_form(request, obj)
        if not form.is_valid():
            return None

        pending_obj = form.save(commit=False)
        before_snapshot = serialize_instance(obj) if obj else {}
        after_snapshot = serialize_instance(pending_obj)
        object_id = obj.pk if obj else None
        create_approval_request(
            action_type=action_type,
            submitted_by=request.user,
            model_class=self.model,
            object_id=object_id,
            before_snapshot=before_snapshot,
            after_snapshot=after_snapshot,
            metadata={"model": self.model._meta.label},
        )
        messages.success(request, f"{self.model._meta.verbose_name.title()} change submitted for approval.")
        return redirect(self.approval_redirect_name)

    def add_view(self, request, form_url="", extra_context=None):
        if request.method == "POST" and not self.has_direct_finance_change_permission(request):
            response = self._submit_change_request(request, action_type=ApprovalRequest.ActionType.CREATE)
            if response is not None:
                return response
        return super().add_view(request, form_url, extra_context)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        if request.method == "POST" and not self.has_direct_finance_change_permission(request):
            obj = self.get_object(request, object_id)
            response = self._submit_change_request(request, action_type=ApprovalRequest.ActionType.UPDATE, obj=obj)
            if response is not None:
                return response
        return super().change_view(request, object_id, form_url, extra_context)

    def delete_view(self, request, object_id, extra_context=None):
        if request.method == "POST" and not self.has_direct_finance_change_permission(request):
            obj = self.get_object(request, object_id)
            create_approval_request(
                action_type=ApprovalRequest.ActionType.DELETE,
                submitted_by=request.user,
                model_class=self.model,
                object_id=obj.pk,
                before_snapshot=serialize_instance(obj),
                after_snapshot={},
                metadata={"model": self.model._meta.label},
            )
            messages.success(request, f"{self.model._meta.verbose_name.title()} delete submitted for approval.")
            return redirect(self.approval_redirect_name)
        return super().delete_view(request, object_id, extra_context)

    def save_model(self, request, obj, form, change):
        before_snapshot = serialize_instance(self.model.objects.get(pk=obj.pk)) if change else {}
        super().save_model(request, obj, form, change)
        after_snapshot = serialize_instance(obj)
        log_audit(
            "finance.updated" if change else "finance.created",
            actor=request.user,
            obj=obj,
            before_snapshot=before_snapshot,
            after_snapshot=after_snapshot,
            metadata={"model": self.model._meta.label},
        )

    def delete_model(self, request, obj):
        before_snapshot = serialize_instance(obj)
        object_id = obj.pk
        object_repr = str(obj)
        content_type = get_content_type_for_model(obj.__class__)
        super().delete_model(request, obj)
        log_audit(
            "finance.deleted",
            actor=request.user,
            before_snapshot=before_snapshot,
            content_type=content_type,
            object_id=object_id,
            object_repr=object_repr,
            metadata={"model": self.model._meta.label},
        )

    def get_actions(self, request):
        actions = super().get_actions(request)
        actions.pop("delete_selected", None)
        return actions
