from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import EmailStr
import os
from dotenv import load_dotenv

load_dotenv()

# Configuración de email
conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME", "tu-email@gmail.com"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD", "tu-password-de-app"),
    MAIL_FROM=os.getenv("MAIL_FROM", "tu-email@gmail.com"),
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

# Instancia global del servicio de email
fastmail = FastMail(conf)

async def send_password_email(email: str, nombre: str, temp_password: str):
    """Enviar email con contraseña temporal al alumno"""
    
    # Plantilla HTML del email
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Credenciales de Acceso - Sistema de Notas</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            .header {{
                background-color: #3b82f6;
                color: white;
                padding: 20px;
                text-align: center;
                border-radius: 8px 8px 0 0;
            }}
            .content {{
                background-color: #f8fafc;
                padding: 30px;
                border-radius: 0 0 8px 8px;
            }}
            .credentials {{
                background-color: white;
                padding: 20px;
                border-radius: 8px;
                border-left: 4px solid #3b82f6;
                margin: 20px 0;
            }}
            .password {{
                font-family: monospace;
                font-size: 18px;
                font-weight: bold;
                color: #059669;
                background-color: #ecfdf5;
                padding: 10px;
                border-radius: 4px;
                text-align: center;
                margin: 10px 0;
            }}
            .warning {{
                background-color: #fef3c7;
                border: 1px solid #f59e0b;
                color: #92400e;
                padding: 15px;
                border-radius: 8px;
                margin: 20px 0;
            }}
            .footer {{
                text-align: center;
                margin-top: 30px;
                color: #6b7280;
                font-size: 14px;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🎓 Sistema de Gestión de Notas</h1>
            <p>Credenciales de Acceso</p>
        </div>
        
        <div class="content">
            <h2>Hola {nombre},</h2>
            
            <p>Te damos la bienvenida al <strong>Sistema de Gestión de Notas</strong>. 
            Se han generado tus credenciales de acceso para que puedas ingresar al sistema.</p>
            
            <div class="credentials">
                <h3>📧 Tus Credenciales de Acceso:</h3>
                <p><strong>Email:</strong> {email}</p>
                <p><strong>Contraseña temporal:</strong></p>
                <div class="password">{temp_password}</div>
            </div>
            
            <div class="warning">
                <h4>⚠️ Importante:</h4>
                <ul>
                    <li>Esta es una contraseña temporal que debes cambiar en tu primer acceso</li>
                    <li>Guarda estas credenciales en un lugar seguro</li>
                    <li>No compartas tu contraseña con otros usuarios</li>
                </ul>
            </div>
            
            <h3>🚀 Cómo acceder:</h3>
            <ol>
                <li>Ve a la página de inicio del sistema</li>
                <li>Ingresa tu email y la contraseña temporal</li>
                <li>Cambia tu contraseña por una más segura</li>
                <li>¡Comienza a usar el sistema!</li>
            </ol>
            
            <p>Si tienes alguna pregunta o necesitas ayuda, no dudes en contactar al administrador del sistema.</p>
            
            <p>¡Bienvenido al sistema!</p>
        </div>
        
        <div class="footer">
            <p>Este es un email automático del Sistema de Gestión de Notas</p>
            <p>Por favor, no respondas a este mensaje</p>
        </div>
    </body>
    </html>
    """
    
    # Crear el mensaje
    message = MessageSchema(
        subject="🎓 Credenciales de Acceso - Sistema de Notas",
        recipients=[email],
        body=html_content,
        subtype="html"
    )
    
    try:
        # Enviar el email
        await fastmail.send_message(message)
        return {"success": True, "message": f"Email enviado exitosamente a {email}"}
    except Exception as e:
        return {"success": False, "message": f"Error al enviar email: {str(e)}"}

async def send_grade_notification(email: str, nombre_alumno: str, asignatura: str, calificacion: float, tipo_nota: str, fecha: str):
    """Enviar notificación de nueva nota publicada al alumno"""
    
    # Determinar el estado de la nota
    if calificacion >= 13:
        estado = "Aprobado"
        color_estado = "#059669"
        bg_estado = "#ecfdf5"
    elif calificacion >= 10:
        estado = "Recuperación"
        color_estado = "#d97706"
        bg_estado = "#fef3c7"
    else:
        estado = "Desaprobado"
        color_estado = "#dc2626"
        bg_estado = "#fef2f2"
    
    # Plantilla HTML del email
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Nueva Nota Publicada - Sistema de Notas</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            .header {{
                background-color: #3b82f6;
                color: white;
                padding: 20px;
                text-align: center;
                border-radius: 8px 8px 0 0;
            }}
            .content {{
                background-color: #f8fafc;
                padding: 30px;
                border-radius: 0 0 8px 8px;
            }}
            .grade-card {{
                background-color: white;
                padding: 25px;
                border-radius: 12px;
                border: 2px solid #e5e7eb;
                margin: 20px 0;
                text-align: center;
            }}
            .grade-value {{
                font-size: 48px;
                font-weight: bold;
                color: {color_estado};
                margin: 10px 0;
            }}
            .grade-status {{
                background-color: {bg_estado};
                color: {color_estado};
                padding: 8px 16px;
                border-radius: 20px;
                font-weight: bold;
                display: inline-block;
                margin: 10px 0;
            }}
            .grade-details {{
                background-color: #f9fafb;
                padding: 20px;
                border-radius: 8px;
                margin: 20px 0;
            }}
            .detail-row {{
                display: flex;
                justify-content: space-between;
                padding: 8px 0;
                border-bottom: 1px solid #e5e7eb;
            }}
            .detail-row:last-child {{
                border-bottom: none;
            }}
            .detail-label {{
                font-weight: bold;
                color: #6b7280;
            }}
            .detail-value {{
                color: #1f2937;
            }}
            .info-box {{
                background-color: #eff6ff;
                border: 1px solid #3b82f6;
                color: #1e40af;
                padding: 15px;
                border-radius: 8px;
                margin: 20px 0;
            }}
            .footer {{
                text-align: center;
                margin-top: 30px;
                color: #6b7280;
                font-size: 14px;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📊 Sistema de Gestión de Notas</h1>
            <p>Nueva Nota Publicada</p>
        </div>
        
        <div class="content">
            <h2>Hola {nombre_alumno},</h2>
            
            <p>Te informamos que se ha publicado una nueva calificación en el sistema. 
            Puedes revisar los detalles a continuación:</p>
            
            <div class="grade-card">
                <h3>📚 {asignatura}</h3>
                <div class="grade-value">{calificacion}</div>
                <div class="grade-status">{estado}</div>
            </div>
            
            <div class="grade-details">
                <h4>📋 Detalles de la Calificación:</h4>
                <div class="detail-row">
                    <span class="detail-label">Asignatura:</span>
                    <span class="detail-value">{asignatura}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Tipo de Evaluación:</span>
                    <span class="detail-value">{tipo_nota}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Calificación:</span>
                    <span class="detail-value">{calificacion}/20</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Estado:</span>
                    <span class="detail-value">{estado}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Fecha de Registro:</span>
                    <span class="detail-value">{fecha}</span>
                </div>
            </div>
            
            <div class="info-box">
                <h4>ℹ️ Información Importante:</h4>
                <ul>
                    <li>Esta calificación ya está disponible en tu panel de estudiante</li>
                    <li>Puedes acceder al sistema para ver todas tus notas y promedios</li>
                    <li>Si tienes dudas sobre esta calificación, contacta a tu docente</li>
                </ul>
            </div>
            
            <h3>🎯 Criterios de Evaluación:</h3>
            <ul>
                <li><strong>13-20:</strong> Aprobado</li>
                <li><strong>10-12:</strong> Recuperación</li>
                <li><strong>0-9:</strong> Desaprobado</li>
            </ul>
            
            <p>¡Sigue así! Tu esfuerzo y dedicación son importantes para tu formación académica.</p>
            
            <p>Saludos cordiales,<br>Equipo del Sistema de Gestión de Notas</p>
        </div>
        
        <div class="footer">
            <p>Este es un email automático del Sistema de Gestión de Notas</p>
            <p>Por favor, no respondas a este mensaje</p>
        </div>
    </body>
    </html>
    """
    
    # Crear el mensaje
    message = MessageSchema(
        subject=f"📊 Nueva Nota Publicada - {asignatura}",
        recipients=[email],
        body=html_content,
        subtype="html"
    )
    
    try:
        # Enviar el email
        await fastmail.send_message(message)
        return {"success": True, "message": f"Notificación de nota enviada exitosamente a {email}"}
    except Exception as e:
        return {"success": False, "message": f"Error al enviar notificación: {str(e)}"}

async def send_password_recovery_email(email: str, nombre: str, temp_password: str):
    """Enviar email de recuperación de contraseña"""
    
    # Plantilla HTML del email
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Recuperación de Contraseña - Sistema de Notas</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f4f4f4;
            }}
            .container {{
                background-color: #ffffff;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 0 20px rgba(0,0,0,0.1);
            }}
            .header {{
                text-align: center;
                margin-bottom: 30px;
                padding-bottom: 20px;
                border-bottom: 2px solid #3b82f6;
            }}
            .header h1 {{
                color: #3b82f6;
                margin: 0;
                font-size: 28px;
            }}
            .content {{
                margin-bottom: 30px;
            }}
            .password-box {{
                background-color: #f8fafc;
                border: 2px solid #3b82f6;
                border-radius: 8px;
                padding: 20px;
                text-align: center;
                margin: 20px 0;
            }}
            .password {{
                font-size: 24px;
                font-weight: bold;
                color: #1e40af;
                letter-spacing: 2px;
                font-family: 'Courier New', monospace;
            }}
            .warning {{
                background-color: #fef3c7;
                border: 1px solid #f59e0b;
                border-radius: 6px;
                padding: 15px;
                margin: 20px 0;
            }}
            .warning h3 {{
                color: #92400e;
                margin-top: 0;
            }}
            .footer {{
                text-align: center;
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #e5e7eb;
                color: #6b7280;
                font-size: 14px;
            }}
            .button {{
                display: inline-block;
                background-color: #3b82f6;
                color: white;
                padding: 12px 24px;
                text-decoration: none;
                border-radius: 6px;
                font-weight: bold;
                margin: 10px 0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔐 Recuperación de Contraseña</h1>
                <p>Sistema de Gestión de Notas</p>
            </div>
            
            <div class="content">
                <h2>Hola {nombre},</h2>
                
                <p>Hemos recibido una solicitud para restablecer la contraseña de tu cuenta en el Sistema de Gestión de Notas.</p>
                
                <p>Se ha generado una <strong>contraseña temporal</strong> para tu cuenta:</p>
                
                <div class="password-box">
                    <p style="margin: 0 0 10px 0; color: #6b7280;">Tu nueva contraseña temporal es:</p>
                    <div class="password">{temp_password}</div>
                </div>
                
                <div class="warning">
                    <h3>⚠️ Importante:</h3>
                    <ul>
                        <li><strong>Usa esta contraseña para iniciar sesión</strong></li>
                        <li><strong>Cambia tu contraseña inmediatamente</strong> después de iniciar sesión</li>
                        <li>Ve a <strong>"Mi Perfil"</strong> en el sistema para cambiar tu contraseña</li>
                        <li>Esta contraseña temporal es válida hasta que la cambies</li>
                    </ul>
                </div>
                
                <p>Si no solicitaste este cambio de contraseña, por favor contacta al administrador del sistema inmediatamente.</p>
                
                <p style="text-align: center;">
                    <a href="http://localhost:3001/login" class="button">Iniciar Sesión</a>
                </p>
            </div>
            
            <div class="footer">
                <p>Este es un mensaje automático del Sistema de Gestión de Notas.</p>
                <p>Por favor, no respondas a este email.</p>
                <p>Si tienes problemas, contacta al administrador del sistema.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Crear el mensaje
    message = MessageSchema(
        subject="🔐 Recuperación de Contraseña - Sistema de Notas",
        recipients=[email],
        body=html_content,
        subtype="html"
    )
    
    try:
        await fastmail.send_message(message)
        return {"success": True, "message": f"Email de recuperación enviado exitosamente a {email}"}
    except Exception as e:
        return {"success": False, "message": f"Error al enviar email de recuperación: {str(e)}"}
