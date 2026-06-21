# emails.py
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

def send_worker_activation_email(context):
    """
    Send activation email to worker created by admin
    """
    user = context.get('user')
    activation_url = context.get('activation_url')
    
    subject = 'Activate Your BlueConnect Worker Account'
    
    html_message = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: 'Inter', Arial, sans-serif;
                background-color: #f5f7fa;
                margin: 0;
                padding: 0;
            }}
            .container {{
                max-width: 600px;
                margin: 40px auto;
                background: #ffffff;
                border-radius: 16px;
                overflow: hidden;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }}
            .header {{
                background: linear-gradient(135deg, #2c7da0 0%, #61a5c2 100%);
                padding: 32px;
                text-align: center;
            }}
            .header h1 {{
                color: white;
                margin: 0;
                font-size: 24px;
            }}
            .content {{
                padding: 32px;
            }}
            .button {{
                display: inline-block;
                padding: 12px 32px;
                background: #2c7da0;
                color: white;
                text-decoration: none;
                border-radius: 8px;
                margin: 24px 0;
            }}
            .footer {{
                padding: 20px;
                text-align: center;
                background: #f8fafc;
                color: #64748b;
                font-size: 12px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔧 BlueConnect</h1>
            </div>
            <div class="content">
                <h2>Hello {user.full_name},</h2>
                <p>An administrator has created a worker account for you on <strong>BlueConnect</strong> - Kenya's platform connecting skilled workers with clients.</p>
                <p>To activate your account and start receiving job opportunities, please click the button below:</p>
                <div style="text-align: center;">
                    <a href="{activation_url}" class="button">Activate My Account</a>
                </div>
                <p>Or copy and paste this link into your browser:</p>
                <p style="background: #f1f5f9; padding: 12px; border-radius: 8px; word-break: break-all;">
                    {activation_url}
                </p>
                <p><strong>Note:</strong> This link will expire in 48 hours.</p>
                <hr style="margin: 24px 0;">
                <p style="color: #64748b; font-size: 14px;">If you did not expect this email, please ignore it.</p>
            </div>
            <div class="footer">
                <p>&copy; 2026 BlueConnect | Connecting Kenya's Skilled Workers</p>
            </div>
        </div>
    </body>
    </html>
    '''
    
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )


def send_welcome_email(context):
    """
    Send welcome email after activation
    """
    user = context.get('user')
    
    subject = 'Welcome to BlueConnect! 🎉'
    
    html_message = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: 'Inter', Arial, sans-serif;
                background-color: #f5f7fa;
                margin: 0;
                padding: 0;
            }}
            .container {{
                max-width: 600px;
                margin: 40px auto;
                background: #ffffff;
                border-radius: 16px;
                overflow: hidden;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }}
            .header {{
                background: linear-gradient(135deg, #2c7da0 0%, #61a5c2 100%);
                padding: 32px;
                text-align: center;
            }}
            .content {{
                padding: 32px;
            }}
            .button {{
                display: inline-block;
                padding: 12px 32px;
                background: #2c7da0;
                color: white;
                text-decoration: none;
                border-radius: 8px;
                margin: 24px 0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Welcome to BlueConnect! 🎉</h1>
            </div>
            <div class="content">
                <h2>Hello {user.full_name},</h2>
                <p>Your BlueConnect account has been successfully activated!</p>
                <p>You can now:</p>
                <ul>
                    <li>✅ Create your professional profile</li>
                    <li>✅ List your skills and services</li>
                    <li>✅ Browse and apply for jobs</li>
                    <li>✅ Connect with clients in your area</li>
                </ul>
                <div style="text-align: center;">
                    <a href="{settings.FRONTEND_URL}/worker/dashboard" class="button">Go to Dashboard</a>
                </div>
                <p>Need help? Contact our support team at support@blueconnect.com</p>
            </div>
        </div>
    </body>
    </html>
    '''
    
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )