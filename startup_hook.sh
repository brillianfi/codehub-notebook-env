#!/bin/bash

function urldecode() { echo -e "${*//-/\\x}"; }

sudo chmod 700 /efs;
sudo chown -R jovyan /home/jovyan;
sudo chmod -R 700 /home/jovyan;
sudo chown -R jovyan /temp_conf;
sudo chown root /home/jovyan/.jupyter/custom/custom.js
sudo chmod a+r /home/jovyan/.jupyter/custom/custom.js
mkdir -p /home/jovyan/Data;
mkdir -p /home/jovyan/course_files;
mv /temp_conf/.jupyter /home/jovyan/;
hsname=$(hostname);
username=$(urldecode ${hsname:8});
admins="$1";
if [[ $admins =~ (^|[[:space:]])$username($|[[:space:]]) ]];
then # is admin
    mkdir -p /home/jovyan/exchange/course/outbound;
    mkdir -p /home/jovyan/exchange/course/inbound;
    chmod 777 -R /home/jovyan/exchange;
    mv /home/jovyan/.jupyter/instructor_nbgrader_config.py /home/jovyan/.jupyter/nbgrader_config.py;
    rm /home/jovyan/.jupyter/student_nbgrader_config.py;
    sudo rm /home/jovyan/.jupyter/custom/custom.js
    sudo sh -c "echo $admins >> /admins.txt";
    chmod 600 /admins.txt;
    sudo chown -R jovyan /home/jovyan/.jupyter;
    mv /temp_conf/cds /cds-cli;
    /opt/conda/bin/pip install -e /cds-cli;
    sudo sh -c "echo 'Defaults secure_path=\"/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/snap/bin:/opt/conda/bin\"' >> /etc/sudoers.d/path"
    jupyter nbextension enable --sys-prefix --py hide_code;
    jupyter serverextension enable --sys-prefix --py hide_code;
else # is not admin
    mkdir -p /home/jovyan/.exchange/course/outbound;
    mkdir -p /home/jovyan/.exchange/course/inbound;
    chmod 777 -R /home/jovyan/.exchange;
    mv /home/jovyan/.jupyter/student_nbgrader_config.py /home/jovyan/.jupyter/nbgrader_config.py;
    rm /home/jovyan/.jupyter/instructor_nbgrader_config.py;
    jupyter nbextension disable --sys-prefix formgrader/main --section=tree;
    jupyter serverextension disable --sys-prefix nbgrader.server_extensions.formgrader;
    jupyter nbextension disable --sys-prefix create_assignment/main
    mkdir -p /home/jovyan/feedback;
    sudo rm /etc/sudoers.d/notebook;
fi;
sudo rm -r /temp_conf;
