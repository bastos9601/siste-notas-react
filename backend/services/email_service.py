from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import EmailStr
from fastapi import UploadFile
from io import BytesIO
import os
from dotenv import load_dotenv
import smtplib
from email.message import EmailMessage

load_dotenv()

# Configuración de email
MAIL_USERNAME = os.getenv("MAIL_USERNAME", "lopscarlos18@gmail.com")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "hfwp iowb vtbf dddq")
MAIL_FROM = os.getenv("MAIL_FROM") or MAIL_USERNAME

conf = ConnectionConfig(
    MAIL_USERNAME=MAIL_USERNAME,
    MAIL_PASSWORD=MAIL_PASSWORD,
    MAIL_FROM=MAIL_FROM,
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
            
            <p>Puedes ingresar al sistema para consultar tus calificaciones:</p>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="http://localhost:3001" style="background-color: #4285F4; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">
                    Ingresar al Sistema
                </a>
            </div>
            
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

async def send_all_grades_email(email: str, nombre_alumno: str, notas_data: list, asignatura_nombre: str):
    """Enviar email con todas las notas de un alumno en una asignatura específica"""
    
    # Calcular promedio
    if notas_data:
        promedio = sum(nota['calificacion'] for nota in notas_data) / len(notas_data)
    else:
        promedio = 0
    
    # Determinar estado general
    if promedio >= 13:
        estado_general = "Aprobado"
        color_estado = "#059669"
        bg_estado = "#ecfdf5"
    elif promedio >= 10:
        estado_general = "Recuperación"
        color_estado = "#d97706"
        bg_estado = "#fef3c7"
    else:
        estado_general = "Desaprobado"
        color_estado = "#dc2626"
        bg_estado = "#fef2f2"
    
    # Generar tabla de notas
    notas_html = ""
    for nota in notas_data:
        nota_estado = "Aprobado" if nota['calificacion'] >= 13 else "Recuperación" if nota['calificacion'] >= 10 else "Desaprobado"
        nota_color = "#059669" if nota['calificacion'] >= 13 else "#d97706" if nota['calificacion'] >= 10 else "#dc2626"
        
        notas_html += f"""
        <tr style="border-bottom: 1px solid #e5e7eb;">
            <td style="padding: 12px; font-weight: bold;">{nota['tipo_nota']}</td>
            <td style="padding: 12px; text-align: center;">
                <span style="background-color: {nota_color}20; color: {nota_color}; padding: 4px 8px; border-radius: 4px; font-weight: bold;">
                    {nota['calificacion']}
                </span>
            </td>
            <td style="padding: 12px; text-align: center;">
                <span style="color: {nota_color}; font-weight: bold;">{nota_estado}</span>
            </td>
            <td style="padding: 12px; text-align: center;">{nota['fecha']}</td>
        </tr>
        """
    
    # Plantilla HTML del email
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Reporte de Notas - {asignatura_nombre}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 700px;
                margin: 0 auto;
                padding: 20px;
            }}
            .header {{
                background-color: #3b82f6;
                color: white;
                padding: 25px;
                text-align: center;
                border-radius: 8px 8px 0 0;
            }}
            .content {{
                background-color: #f8fafc;
                padding: 30px;
                border-radius: 0 0 8px 8px;
            }}
            .summary-card {{
                background-color: white;
                padding: 25px;
                border-radius: 12px;
                border: 2px solid #e5e7eb;
                margin: 20px 0;
                text-align: center;
            }}
            .average-value {{
                font-size: 48px;
                font-weight: bold;
                color: {color_estado};
                margin: 10px 0;
            }}
            .average-status {{
                background-color: {bg_estado};
                color: {color_estado};
                padding: 8px 16px;
                border-radius: 20px;
                font-weight: bold;
                display: inline-block;
                margin: 10px 0;
            }}
            .grades-table {{
                background-color: white;
                border-radius: 8px;
                overflow: hidden;
                margin: 20px 0;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }}
            .grades-table table {{
                width: 100%;
                border-collapse: collapse;
            }}
            .grades-table th {{
                background-color: #f9fafb;
                padding: 15px;
                text-align: left;
                font-weight: bold;
                color: #374151;
                border-bottom: 2px solid #e5e7eb;
            }}
            .grades-table td {{
                padding: 12px 15px;
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
            <h1>📊 Reporte de Notas</h1>
            <p>{asignatura_nombre}</p>
        </div>
        
        <div class="content">
            <h2>Hola {nombre_alumno},</h2>
            
            <p>Te enviamos el reporte completo de tus calificaciones en la asignatura <strong>{asignatura_nombre}</strong>.</p>
            
            <div class="summary-card">
                <h3>📈 Resumen General</h3>
                <div class="average-value">{promedio:.1f}</div>
                <div class="average-status">{estado_general}</div>
                <p style="margin: 10px 0 0 0; color: #6b7280;">Promedio General</p>
            </div>
            
            <div class="grades-table">
                <h3 style="padding: 20px 20px 10px 20px; margin: 0; color: #374151;">📋 Detalle de Calificaciones</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Tipo de Evaluación</th>
                            <th style="text-align: center;">Calificación</th>
                            <th style="text-align: center;">Estado</th>
                            <th style="text-align: center;">Fecha</th>
                        </tr>
                    </thead>
                    <tbody>
                        {notas_html}
                    </tbody>
                </table>
            </div>
            
            <div class="info-box">
                <h4>ℹ️ Información Importante:</h4>
                <ul>
                    <li>Este reporte incluye todas las calificaciones registradas en {asignatura_nombre}</li>
                    <li>El promedio se calcula sobre todas las evaluaciones realizadas</li>
                    <li>Puedes acceder al sistema para ver más detalles y otras asignaturas</li>
                    <li>Si tienes dudas sobre alguna calificación, contacta a tu docente</li>
                </ul>
            </div>
            
            <h3>🎯 Criterios de Evaluación:</h3>
            <ul>
                <li><strong>13-20:</strong> Aprobado</li>
                <li><strong>10-12:</strong> Recuperación</li>
                <li><strong>0-9:</strong> Desaprobado</li>
            </ul>
            
            <p>¡Sigue esforzándote! Tu dedicación es importante para tu formación académica.</p>
            
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
        subject=f"📊 Reporte de Notas - {asignatura_nombre}",
        recipients=[email],
        body=html_content,
        subtype="html"
    )
    
    try:
        # Enviar el email
        await fastmail.send_message(message)
        return {"success": True, "message": f"Reporte de notas enviado exitosamente a {email}"}
    except Exception as e:
        return {"success": False, "message": f"Error al enviar reporte de notas: {str(e)}"}

async def send_grades_published_notification(email: str, nombre_alumno: str, asignatura_nombre: str):
    """Enviar notificación simple de que las notas están publicadas"""
    
    # Plantilla HTML del email - notificación simple
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Notas Publicadas - Sistema de Notas</title>
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
            .notification-box {{
                background-color: white;
                padding: 25px;
                border-radius: 12px;
                border-left: 4px solid #3b82f6;
                margin: 20px 0;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .button {{
                display: inline-block;
                background-color: #3b82f6;
                color: white;
                padding: 12px 24px;
                text-decoration: none;
                border-radius: 6px;
                font-weight: bold;
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
            <h1>📢 Notificación de Notas</h1>
        </div>
        
        <div class="content">
            <h2>Hola {nombre_alumno},</h2>
            
            <div class="notification-box">
                <h3>✅ Notas Publicadas</h3>
                <p style="font-size: 16px; margin: 15px 0;">
                    Te informamos que tus notas de la asignatura <strong>{asignatura_nombre}</strong> 
                    ya están disponibles en el sistema.
                </p>
            </div>
            
            <p>Puedes ingresar al sistema para consultar tus calificaciones:</p>
            
            <div style="text-align: center;">
                <a href="http://localhost:3001" class="button" style="color: white;">
                    Ingresar al Sistema
                </a>
            </div>
            
            <p style="margin-top: 30px;">
                Si tienes alguna consulta sobre tus notas, no dudes en contactar a tu docente.
            </p>
            
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
        subject=f"📢 Notas Publicadas - {asignatura_nombre}",
        recipients=[email],
        body=html_content,
        subtype="html"
    )
    
    try:
        # Enviar el email
        await fastmail.send_message(message)
        return {"success": True, "message": f"Notificación enviada exitosamente a {email}"}
    except Exception as e:
        return {"success": False, "message": f"Error al enviar notificación: {str(e)}"}

async def send_report_with_attachment(email: str, nombre_docente: str, asignatura: str, tipo_evaluacion: str, file_path: str):
    """Enviar un reporte de notas con archivo CSV adjunto a un email arbitrario.

    Parámetros:
    - email: destino del correo
    - nombre_docente: nombre del docente que envía
    - asignatura: nombre de la asignatura del reporte
    - tipo_evaluacion: tipo de evaluación del reporte
    - file_path: ruta absoluta del archivo CSV generado
    """

    # Plantilla HTML sencilla para acompañar el adjunto
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset=\"utf-8\">
        <title>Reporte de Notas</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 700px;
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
                padding: 24px;
                border-radius: 0 0 8px 8px;
            }}
            .info-box {{
                background-color: #eff6ff;
                border: 1px solid #3b82f6;
                color: #1e40af;
                padding: 12px;
                border-radius: 8px;
                margin: 16px 0;
            }}
            .footer {{
                text-align: center;
                margin-top: 24px;
                color: #6b7280;
                font-size: 13px;
            }}
        </style>
    </head>
    <body>
        <div class=\"header\">
            <h1>📄 Reporte de Notas</h1>
        </div>
        <div class=\"content\">
            <p>Hola,</p>
            <p>El docente <strong>{nombre_docente}</strong> ha compartido el reporte de la asignatura <strong>{asignatura}</strong> correspondiente a <strong>{tipo_evaluacion}</strong>.</p>
            <div class=\"info-box\">El archivo PDF del reporte se adjunta a este correo.</div>
            <p>Saludos,<br>Sistema de Gestión de Notas</p>
        </div>
        <div class=\"footer\">
            <p>Este es un email automático del Sistema de Gestión de Notas</p>
        </div>
    </body>
    </html>
    """

    # Crear el mensaje con adjunto
    try:
        message = MessageSchema(
            subject=f"Reporte de Notas - {asignatura} ({tipo_evaluacion})",
            recipients=[email],
            body=html_content,
            subtype="html",
            attachments=[file_path] if file_path else None,
        )
    except Exception as e:
        return {"success": False, "message": f"No se pudo preparar el mensaje: {str(e)}"}

    try:
        await fastmail.send_message(message)
        return {"success": True, "message": f"Reporte enviado exitosamente a {email}"}
    except Exception as e:
        return {"success": False, "message": f"Error al enviar reporte: {str(e)}"}


async def send_report_with_attachment_bytes(email: str, nombre_docente: str, asignatura: str, tipo_evaluacion: str, filename: str, file_bytes: bytes, mime_type: str = "application/pdf"):
    """Enviar el reporte adjuntando bytes en memoria usando SMTP nativo.

    Este enfoque evita el uso de fastapi-mail para adjuntos,
    que es incompatible con Pydantic v2 y genera errores como
    'ValidationInfo ... has no attribute multipart_subtype'.
    """

    # Plantilla HTML del correo
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset=\"utf-8\">
        <title>Reporte de Notas</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 700px;
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
                padding: 24px;
                border-radius: 0 0 8px 8px;
            }}
            .info-box {{
                background-color: #eff6ff;
                border: 1px solid #3b82f6;
                color: #1e40af;
                padding: 12px;
                border-radius: 8px;
                margin: 16px 0;
            }}
            .footer {{
                text-align: center;
                margin-top: 24px;
                color: #6b7280;
                font-size: 13px;
            }}
        </style>
    </head>
    <body>
        <div class=\"header\">
            <h1>📄 Reporte de Notas</h1>
        </div>
        <div class=\"content\">
            <p>Hola,</p>
            <p>El docente <strong>{nombre_docente}</strong> ha compartido el reporte de la asignatura <strong>{asignatura}</strong> correspondiente a <strong>{tipo_evaluacion}</strong>.</p>
            <div class=\"info-box\">El archivo del reporte se adjunta a este correo.</div>
            <p>Saludos,<br>Sistema de Gestión de Notas</p>
        </div>
        <div class=\"footer\">
            <p>Este es un email automático del Sistema de Gestión de Notas</p>
        </div>
    </body>
    </html>
    """

    try:
        # Construir correo con HTML y adjunto
        msg = EmailMessage()
        msg["Subject"] = f"Reporte de Notas - {asignatura} ({tipo_evaluacion})"
        msg["From"] = MAIL_FROM
        msg["To"] = email
        msg.set_content("Adjuntamos el reporte de notas.")
        msg.add_alternative(html_content, subtype="html")

        # Adjuntar bytes con el tipo MIME indicado
        try:
            maintype, subtype = mime_type.split("/", 1)
        except Exception:
            maintype, subtype = "application", "octet-stream"
        msg.add_attachment(file_bytes, maintype=maintype, subtype=subtype, filename=filename)

        # Enviar por SMTP
        with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
            smtp.starttls()
            smtp.login(MAIL_USERNAME, MAIL_PASSWORD)
            smtp.send_message(msg)

        return {"success": True, "message": f"Reporte enviado exitosamente a {email}"}
    except Exception as e:
        return {"success": False, "message": f"Error al enviar reporte: {str(e)}"}