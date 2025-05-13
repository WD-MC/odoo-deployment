FROM odoo:18

USER root

# Ajout d'un label pour traçabilité
LABEL maintainer="PregodiTeam" \
      description="Odoo customized for Pregodi"

COPY ./user-module /mnt/extra-addons/

#RUN pip3 install -r /mnt/extra-addons/requirements.txt || true

RUN chown -R odoo:odoo /mnt/extra-addons

RUN pip3 install --break-system-packages pycountry

USER odoo