package cm.purecontrol.app;

import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.graphics.Color;
import android.os.Build;

import androidx.core.app.NotificationCompat;

import com.google.firebase.messaging.FirebaseMessagingService;
import com.google.firebase.messaging.RemoteMessage;

import java.util.Map;

public class PurecontrolMessagingService extends FirebaseMessagingService {
    private static final String CHANNEL_ID = "purecontrol_alertes_persistantes";

    @Override
    public void onMessageReceived(RemoteMessage remoteMessage) {
        Map<String, String> data = remoteMessage.getData();
        if (!"ALERTE_CAPTEUR".equals(data.get("type"))) {
            return;
        }

        String niveau = valueOrDefault(data.get("niveau"), "WARNING");
        String capteurId = valueOrDefault(data.get("capteur_id"), "capteur inconnu");
        String title = valueOrDefault(data.get("title"), "PURECONTROL - Alerte " + niveau);
        String body = valueOrDefault(data.get("body"), "Capteur " + capteurId + " : intervention requise.");
        boolean persistent = "true".equals(data.get("persistent"));

        showAlertNotification(title, body, niveau, capteurId, persistent);
    }

    private void showAlertNotification(String title, String body, String niveau, String capteurId, boolean persistent) {
        NotificationManager manager = (NotificationManager) getSystemService(Context.NOTIFICATION_SERVICE);
        if (manager == null) return;

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel channel = new NotificationChannel(
                CHANNEL_ID,
                "Alertes persistantes PURECONTROL",
                NotificationManager.IMPORTANCE_HIGH
            );
            channel.setDescription("Alertes capteurs visibles dans la liste des notifications");
            channel.enableLights(true);
            channel.setLightColor(Color.parseColor("#10b981"));
            channel.enableVibration(true);
            manager.createNotificationChannel(channel);
        }

        Intent intent = new Intent(this, MainActivity.class);
        intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP);
        PendingIntent pendingIntent = PendingIntent.getActivity(
            this,
            0,
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
        );

        NotificationCompat.Builder builder = new NotificationCompat.Builder(this, CHANNEL_ID)
            .setSmallIcon(R.drawable.ic_stat_purecontrol)
            .setColor(Color.parseColor("#10b981"))
            .setContentTitle(title)
            .setContentText(body)
            .setStyle(new NotificationCompat.BigTextStyle().bigText(body + "\nNiveau : " + niveau))
            .setContentIntent(pendingIntent)
            .setPriority(NotificationCompat.PRIORITY_MAX)
            .setCategory(NotificationCompat.CATEGORY_ALARM)
            .setVisibility(NotificationCompat.VISIBILITY_PUBLIC)
            .setAutoCancel(false)
            .setOngoing(persistent);

        int notificationId = Math.abs((capteurId + niveau).hashCode());
        manager.notify(notificationId, builder.build());
    }

    private String valueOrDefault(String value, String fallback) {
        return value == null || value.trim().isEmpty() ? fallback : value;
    }
}
