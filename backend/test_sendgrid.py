from email_service import envoyer_email_alerte, obtenir_destinataires_email


if __name__ == "__main__":
    print("Destinataires configures :", obtenir_destinataires_email())
    ok = envoyer_email_alerte(
        "WARNING",
        "Test configuration SendGrid PURECONTROL",
        "TEST_SENDGRID",
    )
    print("Email envoye" if ok else "Email non envoye")
