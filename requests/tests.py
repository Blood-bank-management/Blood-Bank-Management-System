from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from inventory.models import BloodInventory
from .models import BloodIssue, BloodRequest


class BloodRequestWorkflowTests(TestCase):
    def setUp(self):
        self.request_data = {
            'requester_name': 'Asha Patel',
            'requester_email': 'asha@example.com',
            'hospital_name': 'City Hospital',
            'blood_group': BloodRequest.BloodGroup.O_POSITIVE,
            'quantity': 3,
            'purpose': 'Scheduled surgery',
        }

    def test_request_can_be_submitted_and_tracked(self):
        response = self.client.post(reverse('requests:create'), self.request_data)

        blood_request = BloodRequest.objects.get()
        self.assertRedirects(
            response,
            reverse('requests:detail', kwargs={'tracking_id': blood_request.tracking_id}),
        )
        self.assertContains(self.client.get(response.url), 'Pending review')

    def test_missing_request_fields_are_rejected(self):
        response = self.client.post(reverse('requests:create'), {})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This field is required.')
        self.assertEqual(BloodRequest.objects.count(), 0)

    def test_quantity_must_be_positive(self):
        response = self.client.post(reverse('requests:create'), {**self.request_data, 'quantity': 0})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ensure this value is greater than or equal to 1')
        self.assertEqual(BloodRequest.objects.count(), 0)

    def test_only_staff_can_review_and_rejection_requires_note(self):
        blood_request = BloodRequest.objects.create(**self.request_data)
        user = get_user_model().objects.create_user(username='reviewer', password='test-password', is_staff=True)
        self.client.force_login(user)

        response = self.client.post(
            reverse('requests:review', kwargs={'tracking_id': blood_request.tracking_id}),
            {'action': 'rejected', 'review_note': ''},
        )

        blood_request.refresh_from_db()
        self.assertRedirects(response, reverse('requests:queue'))
        self.assertEqual(blood_request.status, BloodRequest.Status.PENDING)

        self.client.post(
            reverse('requests:review', kwargs={'tracking_id': blood_request.tracking_id}),
            {'action': 'approved', 'review_note': 'Stock confirmed.'},
        )
        blood_request.refresh_from_db()
        self.assertEqual(blood_request.status, BloodRequest.Status.APPROVED)
        self.assertEqual(blood_request.reviewed_by, user)

    def test_staff_can_approve_request(self):
        blood_request = BloodRequest.objects.create(**self.request_data)
        user = get_user_model().objects.create_user(username='approver', is_staff=True)
        self.client.force_login(user)

        self.client.post(
            reverse('requests:review', kwargs={'tracking_id': blood_request.tracking_id}),
            {'action': 'approved', 'review_note': 'Stock confirmed.'},
        )

        blood_request.refresh_from_db()
        self.assertEqual(blood_request.status, BloodRequest.Status.APPROVED)
        self.assertEqual(blood_request.reviewed_by, user)

    def test_staff_can_reject_request_with_reason(self):
        blood_request = BloodRequest.objects.create(**self.request_data)
        user = get_user_model().objects.create_user(username='rejector', is_staff=True)
        self.client.force_login(user)

        self.client.post(
            reverse('requests:review', kwargs={'tracking_id': blood_request.tracking_id}),
            {'action': 'rejected', 'review_note': 'Required blood group is unavailable.'},
        )

        blood_request.refresh_from_db()
        self.assertEqual(blood_request.status, BloodRequest.Status.REJECTED)
        self.assertEqual(blood_request.review_note, 'Required blood group is unavailable.')

    def test_approved_request_issue_deducts_inventory_and_fulfills_request(self):
        blood_request = BloodRequest.objects.create(
            **self.request_data,
            status=BloodRequest.Status.APPROVED,
        )
        batch = BloodInventory.objects.create(
            blood_group=BloodRequest.BloodGroup.O_POSITIVE,
            quantity=5,
            collection_date=date.today(),
            expiry_date=date.today() + timedelta(days=30),
        )
        user = get_user_model().objects.create_user(username='issuer', password='test-password', is_staff=True)
        self.client.force_login(user)

        response = self.client.post(
            reverse('requests:issue', kwargs={'tracking_id': blood_request.tracking_id}),
            {'issue_note': 'Released to City Hospital.'},
        )

        self.assertRedirects(response, reverse('requests:queue'))
        blood_request.refresh_from_db()
        batch.refresh_from_db()
        self.assertEqual(blood_request.status, BloodRequest.Status.FULFILLED)
        self.assertEqual(batch.quantity_remaining, 2)
        self.assertEqual(BloodIssue.objects.get(request=blood_request).issued_by, user)

    def test_issue_is_rejected_for_unapproved_request_or_insufficient_stock(self):
        rejected_request = BloodRequest.objects.create(
            **self.request_data,
            status=BloodRequest.Status.REJECTED,
        )
        BloodInventory.objects.create(
            blood_group=BloodRequest.BloodGroup.O_POSITIVE,
            quantity=2,
            collection_date=date.today(),
            expiry_date=date.today() + timedelta(days=30),
        )
        user = get_user_model().objects.create_user(username='blocked-issuer', password='test-password', is_staff=True)
        self.client.force_login(user)

        self.client.post(
            reverse('requests:issue', kwargs={'tracking_id': rejected_request.tracking_id}),
            {'issue_note': ''},
        )
        rejected_request.refresh_from_db()
        self.assertEqual(rejected_request.status, BloodRequest.Status.REJECTED)
        self.assertEqual(BloodIssue.objects.count(), 0)

        approved_request = BloodRequest.objects.create(
            **self.request_data,
            status=BloodRequest.Status.APPROVED,
        )
        self.client.post(
            reverse('requests:issue', kwargs={'tracking_id': approved_request.tracking_id}),
            {'issue_note': ''},
        )
        approved_request.refresh_from_db()
        self.assertEqual(approved_request.status, BloodRequest.Status.APPROVED)
        self.assertEqual(BloodInventory.objects.get(pk=1).quantity_remaining, 2)

    def test_issue_is_rejected_when_blood_group_is_unavailable(self):
        blood_request = BloodRequest.objects.create(
            **self.request_data,
            status=BloodRequest.Status.APPROVED,
        )
        user = get_user_model().objects.create_user(username='unavailable-issuer', is_staff=True)
        self.client.force_login(user)

        response = self.client.post(
            reverse('requests:issue', kwargs={'tracking_id': blood_request.tracking_id}),
            {'issue_note': ''},
        )

        self.assertRedirects(response, reverse('requests:queue'))
        blood_request.refresh_from_db()
        self.assertEqual(blood_request.status, BloodRequest.Status.APPROVED)
        self.assertEqual(BloodIssue.objects.count(), 0)

    def test_queue_can_be_filtered_by_status_and_blood_group(self):
        BloodRequest.objects.create(**self.request_data, status=BloodRequest.Status.PENDING)
        BloodRequest.objects.create(
            **{**self.request_data, 'blood_group': BloodRequest.BloodGroup.A_NEGATIVE},
            status=BloodRequest.Status.APPROVED,
        )
        user = get_user_model().objects.create_user(username='queue-viewer', is_staff=True)
        self.client.force_login(user)

        response = self.client.get(reverse('requests:queue'), {'status': 'approved'})
        self.assertContains(response, 'A-')
        self.assertNotContains(response, 'Scheduled surgery')  # the pending O+ request's purpose text
        self.assertEqual(response.context['page_obj'].paginator.count, 1)

    def test_duplicate_issue_against_same_request_is_prevented(self):
        blood_request = BloodRequest.objects.create(**self.request_data, status=BloodRequest.Status.APPROVED)
        BloodInventory.objects.create(
            blood_group=BloodRequest.BloodGroup.O_POSITIVE,
            quantity=10,
            collection_date=date.today(),
            expiry_date=date.today() + timedelta(days=30),
        )
        user = get_user_model().objects.create_user(username='double-issuer', is_staff=True)
        self.client.force_login(user)

        self.client.post(
            reverse('requests:issue', kwargs={'tracking_id': blood_request.tracking_id}),
            {'issue_note': 'first'},
        )
        blood_request.refresh_from_db()
        self.assertEqual(blood_request.status, BloodRequest.Status.FULFILLED)

        # Manually reset status to simulate a crafted re-issue attempt against
        # an already-issued request (Part 3.E "prevention of duplicate issues").
        blood_request.status = BloodRequest.Status.APPROVED
        blood_request.save(update_fields=('status',))
        self.client.post(
            reverse('requests:issue', kwargs={'tracking_id': blood_request.tracking_id}),
            {'issue_note': 'second'},
        )
        self.assertEqual(BloodIssue.objects.filter(request=blood_request).count(), 1)


class SharedConstantConsistencyTests(TestCase):
    def test_blood_group_choices_match_shared_constant(self):
        from bloodbank.constants import BLOOD_GROUP_CHOICES
        self.assertEqual(list(BloodRequest.BloodGroup.choices), BLOOD_GROUP_CHOICES)