from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import BloodRequest


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