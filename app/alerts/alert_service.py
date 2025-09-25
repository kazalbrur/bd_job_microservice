# =============================================================================
# 12. Alert System (app/alerts/alert_service.py)
# =============================================================================

from typing import List, Dict
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
from jinja2 import Template

class AlertService:
    def __init__(self):
        self.email_template = Template("""
        <html>
        <body>
            <h2>New Job Alerts for You!</h2>
            <p>Hi there! We found some new jobs that match your interests:</p>
            
            {% for job in jobs %}
            <div style="border: 1px solid #ddd; padding: 15px; margin: 10px 0;">
                <h3>{{ job.title }}</h3>
                <p><strong>Department:</strong> {{ job.department }}</p>
                <p><strong>Location:</strong> {{ job.location }}</p>
                <p><strong>Deadline:</strong> {{ job.deadline_date.strftime('%Y-%m-%d') if job.deadline_date else 'Not specified' }}</p>
                <p><strong>Description:</strong> {{ job.description[:200] }}...</p>
                <p><a href="{{ job.application_link }}" style="background: #007bff; color: white; padding: 10px 15px; text-decoration: none;">Apply Now</a></p>
            </div>
            {% endfor %}
            
            <p>Best regards,<br>BD Jobs Team</p>
        </body>
        </html>
        """)
    
    async def check_and_send_alerts(self, db: Session):
        """Check for new jobs and send alerts"""
        # Get all active alerts
        alerts = db.query(Alert).filter(Alert.is_active == True).all()
        
        for alert in alerts:
            try:
                # Find matching jobs since last alert
                last_sent = alert.last_sent or (datetime.utcnow() - timedelta(days=1))
                matching_jobs = await self._find_matching_jobs(db, alert, last_sent)
                
                if matching_jobs:
                    await self._send_email_alert(alert, matching_jobs)
                    
                    # Update last sent time
                    alert.last_sent = datetime.utcnow()
                    db.commit()
                    
                    logger.info(f"Sent alert to user {alert.user_id} with {len(matching_jobs)} jobs")
                
            except Exception as e:
                logger.error(f"Failed to process alert {alert.id}: {e}")
    
    async def _find_matching_jobs(self, db: Session, alert: Alert, since: datetime) -> List[Job]:
        """Find jobs matching alert criteria"""
        query = db.query(Job).filter(
            Job.created_at >= since,
            Job.is_active == True,
            Job.deadline_date >= datetime.utcnow()
        )
        
        # Apply filters based on alert criteria
        if alert.location:
            query = query.filter(Job.location.ilike(f"%{alert.location}%"))
        
        if alert.department:
            query = query.filter(Job.department.ilike(f"%{alert.department}%"))
        
        if alert.keywords:
            keywords = [k.strip() for k in alert.keywords.split(',')]
            keyword_filters = []
            for keyword in keywords:
                keyword_filters.append(Job.title.ilike(f"%{keyword}%"))
                keyword_filters.append(Job.description.ilike(f"%{keyword}%"))
            
            query = query.filter(or_(*keyword_filters))
        
        return query.limit(10).all()  # Limit to avoid spam
    
    async def _send_email_alert(self, alert: Alert, jobs: List[Job]):
        """Send email alert to user"""
        try:
            # Get user email
            user = db.query(User).filter(User.id == alert.user_id).first()
            if not user or not user.email:
                return
            
            # Prepare email
            subject = f"New Job Alert: {len(jobs)} matching jobs found"
            html_content = self.email_template.render(jobs=jobs)
            
            # Send email
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = settings.FROM_EMAIL
            msg['To'] = user.email
            
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # SMTP connection
            with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                server.send_message(msg)
            
            logger.info(f"Email sent to {user.email}")
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
