from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from rest_framework.authtoken.models import Token

from accounts.models import UserTrustScore
from task.models import Task, TaskSubmission
from wallet.models import Transaction, Wallet

User = get_user_model()


class Command(BaseCommand):
    help = 'Create demo users, tasks, wallet data, and sample submissions for testing.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete existing demo users and tasks before seeding.',
        )

    def handle(self, *args, **options):
        if options['reset']:
            self._reset_demo_data()

        admin = self._get_or_create_user(
            username='admin',
            password='admin123',
            phone='0770000001',
            member_id='ADM001',
            email='admin@example.com',
            is_staff=True,
            is_superuser=True,
        )
        user1 = self._get_or_create_user(
            username='user1',
            password='user123',
            phone='0770000002',
            member_id='MEM001',
            email='user1@example.com',
        )
        user2 = self._get_or_create_user(
            username='user2',
            password='user123',
            phone='0770000003',
            member_id='MEM002',
            email='user2@example.com',
        )

        tasks = self._create_tasks()
        self._seed_wallets_and_transactions(user1, user2)
        self._seed_submissions(user1, user2, tasks)

        Token.objects.get_or_create(user=admin)
        Token.objects.get_or_create(user=user1)

        self.stdout.write(self.style.SUCCESS('Test data ready.'))
        self.stdout.write('')
        self.stdout.write('Logins:')
        self.stdout.write('  Admin  -> admin / admin123  (staff, create tasks)')
        self.stdout.write('  User   -> user1 / user123   (complete tasks)')
        self.stdout.write('  User   -> user2 / user123')
        self.stdout.write('')
        if tasks:
            self.stdout.write(f'  Submit first demo task: /submit/{tasks[0].id}/')
        self.stdout.write('URLs (local):')
        self.stdout.write('  http://127.0.0.1:8000/login/')
        self.stdout.write('  http://127.0.0.1:8000/tasks/')
        self.stdout.write('  http://127.0.0.1:8000/admin/')

    def _reset_demo_data(self):
        usernames = ['admin', 'user1', 'user2']
        Task.objects.filter(title__startswith='[Demo]').delete()
        User.objects.filter(username__in=usernames).delete()
        self.stdout.write('Removed previous demo users and tasks.')

    def _get_or_create_user(self, username, password, phone, member_id, email='', **extra):
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'phone': phone,
                'member_id': member_id,
                'email': email,
                **extra,
            },
        )
        if created:
            user.set_password(password)
            user.save()
            UserTrustScore.objects.create(user=user)
            self.stdout.write(f'  Created user: {username}')
        else:
            user.set_password(password)
            for key, value in extra.items():
                setattr(user, key, value)
            user.phone = phone
            user.member_id = member_id
            if email:
                user.email = email
            user.save()
            UserTrustScore.objects.get_or_create(user=user)
            self.stdout.write(f'  Updated user: {username}')
        return user

    def _create_tasks(self):
        demo_tasks = [
            {
                'title': '[Demo] Share Facebook Group Post',
                'description': 'Share the target post in your Facebook group and submit the post link.',
                'task_type': 'share',
                'target_link': 'https://www.facebook.com/groups/example/permalink/123456789',
                'reward': Decimal('50.00'),
                'total_slots': 100,
            },
            {
                'title': '[Demo] Like & Comment on Page Post',
                'description': 'Like and comment on the page post, then submit your profile post link.',
                'task_type': 'post',
                'target_link': 'https://www.facebook.com/example/posts/123456789',
                'reward': Decimal('25.00'),
                'total_slots': 50,
            },
            {
                'title': '[Demo] Watch & Share Video',
                'description': 'Share the video to your timeline and submit the shared post URL.',
                'task_type': 'share',
                'target_link': 'https://www.facebook.com/watch/?v=123456789',
                'reward': Decimal('75.00'),
                'total_slots': 30,
            },
        ]

        tasks = []
        for data in demo_tasks:
            task, created = Task.objects.update_or_create(
                title=data['title'],
                defaults={**data, 'is_active': True},
            )
            tasks.append(task)
            action = 'Created' if created else 'Updated'
            self.stdout.write(f'  {action} task: {task.title} (id={task.id})')
        return tasks

    def _seed_wallets_and_transactions(self, user1, user2):
        for user, balance in ((user1, Decimal('150.00')), (user2, Decimal('0.00'))):
            wallet, _ = Wallet.objects.get_or_create(user=user)
            wallet.balance = balance
            wallet.save()

        if not Transaction.objects.filter(user=user1, reference='demo-reward-1').exists():
            Transaction.objects.create(
                user=user1,
                amount=Decimal('50.00'),
                transaction_type='reward',
                status='completed',
                reference='demo-reward-1',
            )
            self.stdout.write('  Added sample reward transaction for user1')

    def _seed_submissions(self, user1, user2, tasks):
        if not tasks:
            return

        approved_link = (
            'https://www.facebook.com/groups/demo/permalink/111111111111111/'
        )
        submission, created = TaskSubmission.objects.get_or_create(
            user=user2,
            task=tasks[0],
            defaults={
                'submitted_link': approved_link,
                'status': 'approved',
                'level1_passed': True,
                'level2_passed': True,
                'level3_passed': False,
                'level1_confidence': 0.85,
                'level2_confidence': 0.75,
                'level3_confidence': 0.0,
                'feedback': 'Demo approved submission',
                'fraud_flags': [],
            },
        )
        if created:
            tasks[0].completed_slots += 1
            tasks[0].save(update_fields=['completed_slots'])
            self.stdout.write('  Created approved submission for user2 on task 1')

        pending_link = 'https://www.facebook.com/groups/demo/permalink/222222222222222/'
        _, created = TaskSubmission.objects.get_or_create(
            user=user1,
            task=tasks[1],
            defaults={
                'submitted_link': pending_link,
                'status': 'manual_review',
                'level1_passed': True,
                'level2_passed': True,
                'level3_passed': False,
                'level1_confidence': 0.85,
                'level2_confidence': 0.6,
                'level3_confidence': 0.55,
                'feedback': 'Demo pending manual review',
                'fraud_flags': ['screenshot_inconclusive'],
            },
        )
        if created:
            self.stdout.write('  Created manual_review submission for user1 on task 2')
