
from django.db import transaction as db_transaction
from django.contrib import messages
from django.core.urlresolvers import reverse, reverse_lazy

from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic import FormView, CreateView
from django.views.generic.detail import SingleObjectMixin

from bluebottle.journals.models import ProjectPayoutJournal, OrganizationPayoutJournal
from bluebottle.payments.models import OrderPayment
from bluebottle.payments_manual.models import ManualPayment
from bluebottle.utils.model_dispatcher import (
    get_order_model, get_donation_model, get_project_payout_model, get_model_mapping
)
from bluebottle.utils.utils import StatusDefinition
from .models import BankTransaction
from .admin_forms import journalform_factory, donationform_factory, RetryPayoutForm


class AdminOptsMixin(object):
    def get_context_data(self, **kwargs):
        kwargs.setdefault('opts', self.model._meta)
        return super(AdminOptsMixin, self).get_context_data(**kwargs)


class TransactionMixin(SingleObjectMixin):
    object = None

    def get_transaction(self):
        qs = BankTransaction.objects.filter(status=BankTransaction.IntegrityStatus.UnknownTransaction)
        return self.get_object(queryset=qs)

    def get_context_data(self, **kwargs):
        kwargs.setdefault('transaction', self.get_transaction())
        return super(TransactionMixin, self).get_context_data(**kwargs)


class UnknownTransactionView(AdminOptsMixin, SingleObjectMixin, FormView):

    """
    Show the three forms at once, each one submittable to its own url/handler
    """
    model = BankTransaction
    queryset = BankTransaction.objects.filter(status=BankTransaction.IntegrityStatus.UnknownTransaction)
    related_models = [
        (ProjectPayoutJournal, 'payout'),
        (OrganizationPayoutJournal, 'payout'),
    ]
    template_name = 'admin/accounting/banktransaction/unknown_transaction.html'
    context_object_name = 'transaction'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super(UnknownTransactionView, self).get(request, *args, **kwargs)

    def get_initial(self):
        return {
            'amount': self.object.amount,
            'user_reference': self.request.user.email,
            'description': 'Entry for bank transaction %d that could not be matched automatically' % self.object.id,
        }

    def get_form_data(self, form_class):
        if not hasattr(self, '_form_data'):
            self._form_data = self.request.session.get('form_data')
            self._form_class = self.request.session.get('form_class')
            if self._form_data is not None:
                del self.request.session['form_data']
                del self.request.session['form_class']
        return self._form_data if self._form_class == form_class.__name__ else None

    def get_form_kwargs(self, form_class):
        kwargs = super(UnknownTransactionView, self).get_form_kwargs()
        kwargs['transaction'] = self.object
        if self.get_form_data(form_class) is not None:
            kwargs['data'] = self.get_form_data(form_class)
        return kwargs

    def get_form_class(self):
        return [journalform_factory(model, rel_field) for (model, rel_field) in self.related_models]

    def get_form(self, form_classes):
        return [form_class(**self.get_form_kwargs(form_class)) for form_class in form_classes]


class BaseManualEntryView(TransactionMixin, CreateView):

    """
    Base view that holds the common logic for manual entries
    """
    success_url = reverse_lazy('admin:accounting_banktransaction_changelist')

    def get_form_kwargs(self):
        kwargs = super(BaseManualEntryView, self).get_form_kwargs()
        kwargs['transaction'] = self.get_transaction()
        return kwargs

    def form_invalid(self, form):
        """
        Store the form data in the session and show the errors on the originating page.
        """
        self.request.session['form_class'] = form.__class__.__name__
        self.request.session['form_data'] = form.data
        return redirect('admin:banktransaction-unknown', pk=form.transaction.pk)


class JournalCreateMixin(object):

    """
    Mixin that provides a ModelForm factory and form_valid handler.
    """

    def get_form_class(self):
        return journalform_factory(self.model, 'payout')

    def form_valid(self, form):
        transaction = form.transaction
        with db_transaction.atomic():
            response = super(JournalCreateMixin, self).form_valid(form)
            transaction.status = BankTransaction.IntegrityStatus.Valid
            transaction.save()
            messages.success(
                self.request,
                _('A journal entry was created to resolve transaction "%s"') % transaction
            )
        return response


class CreateProjectPayoutJournalView(JournalCreateMixin, BaseManualEntryView):
    model = ProjectPayoutJournal
    fields = ('amount', 'user_reference', 'description', 'payout')


class CreateOrganizationPayoutJournalView(JournalCreateMixin, BaseManualEntryView):
    model = OrganizationPayoutJournal
    fields = ('amount', 'user_reference', 'description', 'payout')


class CreateManualDonationView(AdminOptsMixin, BaseManualEntryView):
    model = get_donation_model()
    form_class = donationform_factory(fields=('amount', 'project', 'fundraiser'))
    template_name = 'admin/accounting/banktransaction/manual_donation.html'

    def dispatch(self, *args, **kwargs):
        self.transaction = self.get_transaction()
        return super(CreateManualDonationView, self).dispatch(*args, **kwargs)

    def get_initial(self):
        initial = super(CreateManualDonationView, self).get_initial()
        initial['amount'] = self.transaction.amount
        return initial

    def form_valid(self, form):
        with db_transaction.atomic():
            order = get_order_model().objects.create(
                user=self.request.user,
                order_type='manual',
                total=form.cleaned_data['amount']
            )

            form.instance.order = order
            form.instance.anonymous = True
            self.object = donation = form.save()

            order_payment = OrderPayment.objects.create(
                user=self.request.user,
                order=order,
                amount=donation.amount,
                payment_method='manual'
            )
            payment = ManualPayment.objects.create(
                amount=donation.amount,
                transaction=self.transaction,
                user=self.request.user,
                order_payment=order_payment
            )

            # pull us through the statuses to consider it done
            payment.status = StatusDefinition.AUTHORIZED
            payment.save()
            payment.status = StatusDefinition.SETTLED
            payment.save()

            # update/create the required payout
            ProjectPayout = get_project_payout_model()
            project = donation.project
            project.update_amounts()
            payouts = ProjectPayout.objects.filter(project=project)

            # check the payouts and only update 'new' payouts, else create a new payout
            if not payouts.exists():
                # if no payouts exist yet, it's because the project is not finished yet.
                # the donations will be collected when the project finishes
                pass
            else:
                updateable = payouts.filter(status=StatusDefinition.NEW).first()  # only new payouts can be updated
                if updateable is None:
                    rules = payouts.values_list('payout_rule', flat=True).distinct()
                    if len(rules) == 1:
                        rule = rules[0]
                        _message = messages.success
                        msg = _('Created a new project payout with payment rule {rule}')
                    else:
                        _message = messages.warning
                        msg = _('There were {n} payout rules, the choosen rule was: \'{rule}\'')

                    # create a new payout, since the other payouts are on their way for processing and can't be altered
                    payout = ProjectPayout(
                        planned=ProjectPayout.get_next_planned_date(),
                        project=project,
                        payout_rule=rule,
                        protected=True
                    )

                    # we need to manually calculate the amounts, else all project donations will be taken into account
                    # FIXME: this needs to be refactored on the BB_PAYOUT level!
                    calculator = payout.get_calculator()
                    payout.calculate_payable_and_fee(calculator, donation.amount)
                    payout.save()
                    rule = dict(ProjectPayout.PayoutRules.choices)[rule]
                    _message(self.request, msg.format(n=len(rules), rule=rule))
                else:
                    # there is a payout that is still 'new', update that one
                    if updateable.protected is False:
                        updateable.calculate_amounts()
                    else:
                        # this is already an 'irregular' payout, so add the diff
                        # manually. There should be a journal entry for the modification
                        updateable.amount_raised += donation.amount
                        calculator = updateable.get_calculator()
                        updateable.calculate_payable_and_fee(calculator, updateable.get_amount_raised())
                        updateable.save()

                    messages.success(
                        self.request,
                        _('Created a manual donation and updated project payout %r') % updateable
                    )

                # NOTE theoretically there is a situation where the only updateable
                # payout is a payout for an open project and the payout is protected
                # It would then theoretically be possible to make a new donation via
                # the web interface and the project payout will not be re-calculateable

            self.transaction.status = BankTransaction.IntegrityStatus.Valid
            self.transaction.save()

            # TODO FIXME: organization payouts?! recalculate?

        return redirect(self.get_success_url())


class RetryPayoutView(TransactionMixin, AdminOptsMixin, FormView):
    template_name = 'admin/accounting/banktransaction/retry_payout.html'
    model = get_project_payout_model()
    form_class = RetryPayoutForm

    def get_form_kwargs(self):
        kwargs = super(RetryPayoutView, self).get_form_kwargs()
        kwargs['transaction'] = self.get_transaction()
        return kwargs

    def form_valid(self, form):
        with db_transaction.atomic():
            form.instance.user_reference = self.request.user.email
            journal = form.save(commit=False)
            journal.amount = -journal.amount  # we need to subtract instead of add
            journal.save()
            journal.payout.retry()

            transaction = self.get_transaction()
            transaction.status = BankTransaction.IntegrityStatus.Valid
            transaction.payout = journal.payout  # make the link
            transaction.save()

        messages.success(self.request, _('The payout is scheduled for retry. Please verify the data.'))
        return redirect(self.get_success_url(journal.payout))

    def get_success_url(self, payout):
        model_mapping = get_model_mapping()
        admin_url_name = model_mapping['project_payout']['model_lower'].replace('.', '_')
        return reverse('admin:%s_change' % admin_url_name, args=[payout.pk])
