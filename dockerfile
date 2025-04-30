FROM odoo:18

USER root

COPY ./user-module /mnt/extra-addons/

#RUN pip3 install -r /mnt/extra-addons/requirements.txt || true

RUN chown -R odoo:odoo /mnt/extra-addons

RUN pip3 install --break-system-packages pycountry

USER odoo