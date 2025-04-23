FROM odoo:18

USER root

# Copier les modules personnalisés depuis le dossier user-module
COPY ./user-module /mnt/extra-addons/

# Installer des dépendances Python supplémentaires si nécessaire
#RUN pip3 install -r /mnt/extra-addons/requirements.txt || true

# Définir les permissions appropriées
RUN chown -R odoo:odoo /mnt/extra-addons

# Installer pycountry avec contournement de PEP 668
RUN pip3 install --break-system-packages pycountry

USER odoo