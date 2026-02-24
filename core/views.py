from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

@login_required
def dashboard_view(request):
    """Main dashboard - role-based view"""
    
    context = {
        'user': request.user,
        'today': timezone.now(),
    }
    
    if request.user.role == 'INITIATOR':
        from requisitions.models import Requisition
        context.update({
            'my_requisitions': Requisition.objects.filter(created_by=request.user)[:5],
            'pending_approvals': Requisition.objects.filter(
                created_by=request.user,
                status__in=['PENDING_CHIEF_OFFICER', 'PENDING_COUNTY_SECRETARY', 'PENDING_BOARD']
            ).count(),
            'approved_requisitions': Requisition.objects.filter(
                created_by=request.user,
                status='BOARD_APPROVED'
            ).count(),
        })
    
    elif request.user.role == 'CHIEF_OFFICER':
        from requisitions.models import Requisition
        context.update({
            'pending_reviews': Requisition.objects.filter(status='PENDING_CHIEF_OFFICER'),
            'recent_approvals': Requisition.objects.filter(
                status='CHIEF_APPROVED',
                chief_officer_approved_by=request.user
            )[:5],
            'budget_utilization': 65,  # Mock percentage
        })
    
    elif request.user.role == 'COUNTY_SECRETARY':
        from requisitions.models import Requisition
        context.update({
            'pending_endorsements': Requisition.objects.filter(status='PENDING_COUNTY_SECRETARY'),
            'recent_endorsements': Requisition.objects.filter(
                status='COUNTY_SECRETARY_ENDORSED'
            )[:5],
            'total_hires_this_year': 45,  # Mock count
        })
    
    elif request.user.role == 'CPSB_BOARD':
        from requisitions.models import Requisition
        context.update({
            'pending_board_items': Requisition.objects.filter(status='PENDING_BOARD'),
            'recent_approvals': Requisition.objects.filter(
                status='BOARD_APPROVED',
                board_approved_at__gte=timezone.now() - timedelta(days=30)
            ),
        })
    
    elif request.user.role in ['HR_SECRETARIAT', 'HR_ADMIN']:
        from candidates.models import Candidate
        from requisitions.models import Requisition
        
        context.update({
            'active_requisitions': Requisition.objects.filter(
                status='BOARD_APPROVED'
            ).count(),
            'total_applications': Candidate.objects.count(),
            'shortlisted_count': Candidate.objects.filter(stage='SHORTLISTED').count(),
            'interview_count': Candidate.objects.filter(stage='INTERVIEWED').count(),
            'recent_candidates': Candidate.objects.order_by('-applied_date')[:5],
        })
    
    return render(request, 'core/dashboard.html', context)

@login_required
def activity_log_view(request):
    """View user activity log"""
    from accounts.models import UserActivityLog
    
    activities = UserActivityLog.objects.filter(
        user=request.user
    ).order_by('-timestamp')[:50]
    
    return render(request, 'core/activity_log.html', {'activities': activities})