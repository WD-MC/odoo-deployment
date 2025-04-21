odoo.define('module_enregistrement.NotificationPopup', function (require) {
    "use strict";

    var core = require('web.core');

    function showNotification(title, message) {
        // Vérifie si les notifications sont supportées
        if (!("Notification" in window)) {
            console.warn("Ce navigateur ne supporte pas les notifications.");
            return;
        }

        // Demande l'autorisation si ce n'est pas encore fait
        if (Notification.permission === "granted") {
            new Notification(title, { body: message });
        } else if (Notification.permission !== "denied") {
            Notification.requestPermission().then(function (permission) {
                if (permission === "granted") {
                    new Notification(title, { body: message });
                }
            });
        }
    }

    return {
        showNotification: showNotification,
    };
});
