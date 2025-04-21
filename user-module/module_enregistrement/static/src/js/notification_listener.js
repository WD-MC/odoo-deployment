odoo.define('module_enregistrement.NotificationListener', function (require) {
    "use strict";

    var core = require('web.core');
    var bus = require('bus.bus').bus;
    var NotificationPopup = require('module_enregistrement.NotificationPopup');

    bus.on('notification', this, function (notifications) {
        notifications.forEach(function (notification) {
            if (notification[1].type === 'module_enregistrement.notification') {
                NotificationPopup.showNotification(notification[1].title, notification[1].message);
            }
        });
    });

    bus.start();
});
