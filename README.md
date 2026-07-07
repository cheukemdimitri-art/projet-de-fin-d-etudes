# detection-fuites-pfe
on va travaillez ici ensemble

## Application Android

L'APK PURECONTROL est servi par le frontend Vercel depuis :

https://purecontrol-frontend.vercel.app/downloads/PURECONTROL-v1.8-release.apk

Dans le dashboard, ouvrir l'onglet **Application** ou utiliser le bouton **APK Android** dans la barre haute.

## Firebase Cloud Messaging

L'APK v1.8 contient le plugin FCM et le service Android natif pour afficher les alertes PURECONTROL en notification haute priorite.

Pour activer les push en production, ajouter le fichier Firebase Android `google-services.json` dans `android/app/`, puis reconstruire l'APK. Le package Android Firebase doit etre `cm.purecontrol.app`.
