from fastapi import BackgroundTasks

def send_email(email: str, subject: str, body: str):
    # Simulate sending an email (replace with actual email sending logic)
    print(f"Sending email to {email} with subject '{subject}' and body '{body}'")

def send_welcome_email(background_tasks: BackgroundTasks, email: str):
    background_tasks.add_task(send_email, email=email, subject="Welcome!", body="Thank you for signing up!")