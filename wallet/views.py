from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Wallet, Transaction, WithdrawRequest


# 💰 WALLET VIEW
@login_required
def wallet_view(request):
    wallet, _ = Wallet.objects.get_or_create(user=request.user)

    transactions = Transaction.objects.filter(
        user=request.user
    ).order_by('-id')

    withdraws = WithdrawRequest.objects.filter(
        user=request.user
    ).order_by('-requested_at')

    return render(request, 'wallet.html', {
        'balance': wallet.balance,
        'transactions': transactions,
        'withdraws': withdraws
    })


# 🏧 WITHDRAW VIEW
@login_required
def withdraw_request(request):
    wallet, _ = Wallet.objects.get_or_create(user=request.user)

    if request.method == "POST":
        try:
            amount = float(request.POST.get("amount"))
        except:
            messages.error(request, "Invalid amount")
            return redirect('withdraw')

        if amount < 500:
            messages.error(request, "Minimum withdraw is Rs. 500")
            return redirect('withdraw')

        if amount > wallet.balance:
            messages.error(request, "Insufficient balance")
            return redirect('withdraw')

        if WithdrawRequest.objects.filter(
            user=request.user,
            status='pending'
        ).exists():
            messages.error(request, "You already have a pending request")
            return redirect('wallet')

        WithdrawRequest.objects.create(
            user=request.user,
            amount=amount,
            bank_name=request.POST.get("bank_name"),
            account_number=request.POST.get("account_number"),
            account_name=request.POST.get("account_name"),
        )

        wallet.balance -= amount
        wallet.save()

        Transaction.objects.create(
            user=request.user,
            amount=amount,
            transaction_type='debit',
            status='pending',
            reference="Withdraw request"
        )

        messages.success(request, "Withdraw request submitted successfully")
        return redirect('wallet')

    return render(request, 'withdraw.html', {
        'balance': wallet.balance
    })