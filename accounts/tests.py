from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from task.models import Task, TaskSubmission
from wallet.models import Wallet

User = get_user_model()


class SystemSmokeTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='smokeuser',
            password='pass12345',
            phone='0779999999',
            member_id='SMK001',
        )
        self.task = Task.objects.create(
            title='Smoke task',
            description='Test task',
            task_type='post',
            target_link='https://www.facebook.com/example/posts/1',
            reward='10.00',
        )

    def test_login_and_dashboard(self):
        self.client.login(username='smokeuser', password='pass12345')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_tasks_list(self):
        self.client.login(username='smokeuser', password='pass12345')
        response = self.client.get(reverse('tasks'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Smoke task')

    def test_submit_task_get(self):
        self.client.login(username='smokeuser', password='pass12345')
        response = self.client.get(reverse('submit_task', args=[self.task.id]))
        self.assertEqual(response.status_code, 200)

    def test_submit_task_post(self):
        self.client.login(username='smokeuser', password='pass12345')
        response = self.client.post(
            reverse('submit_task', args=[self.task.id]),
            {
                'link': 'https://www.facebook.com/groups/demo/posts/1234567890/',
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            TaskSubmission.objects.filter(user=self.user, task=self.task).exists()
        )

    def test_api_tasks_public(self):
        response = self.client.get('/api/tasks/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.json()) >= 1)

    def test_wallet_page(self):
        Wallet.objects.get_or_create(user=self.user)
        self.client.login(username='smokeuser', password='pass12345')
        response = self.client.get(reverse('wallet'))
        self.assertEqual(response.status_code, 200)
