from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.notifications import NotificationSendRequest, NotificationSendResponse
from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.notifications import send_notification_email
from app.models.notifications import Notification

router = APIRouter()


@router.post('/send', response_model=NotificationSendResponse)
async def send_notification(
    notification: NotificationSendRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Send a notification email.

    - **Request body:** NotificationSendRequest object with email details.
    - **Response:** NotificationSendResponse object with the result of the email sending.
    - **Raises:**
        - 500 Internal Server Error if email sending fails.
    """
    try:
        result = send_notification_email(
            email=notification.to,
            subject=notification.subject,
            html=notification.body,
        )
        if db:
            db_notification = Notification(
                to=notification.to,
                subject=notification.subject,
                body=notification.body,
                resend_id=result.get('id', None),
                status='sent'
            )
            db.add(db_notification)
            await db.commit()
            await db.refresh(db_notification)
        return NotificationSendResponse(
            success=True,
            message="Email sent successfully",
            id=result.get('id')
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send email: {str(e)}"
        )
