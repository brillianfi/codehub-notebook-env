FROM jupyter/minimal-notebook:8d32a5208ca1

ARG NB_UID="1000"
ARG NB_USER="jovyan"
ARG py_ver=3.11

ENV ENV_NAME=python311

ENV CUDA_VISIBLE_DEVICES=-1
ENV TF_CPP_MIN_LOG_LEVEL=3

USER root

RUN apt-get update -y && \
    apt-get install -y pkg-config libfreetype6-dev vim-tiny && \
    apt-get clean

RUN apt-get update -y && apt-get install -y graphviz
RUN adduser $NB_USER sudo
RUN echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers.d/notebook

USER $NB_UID

# Install packages required to manage notebooks.
COPY jupyter-requirements.txt .
RUN pip install --no-cache-dir -r jupyter-requirements.txt

# Create environment (kernel) for notebooks to run.
RUN mamba create --yes -p "${CONDA_DIR}/envs/${ENV_NAME}" \
    python=${py_ver} \
    'ipykernel' \
    'jupyterlab' && \
    mamba clean --all -f -y

COPY kernel-requirements.txt .
RUN "${CONDA_DIR}/envs/${ENV_NAME}/bin/pip" install --no-cache-dir \
    -r kernel-requirements.txt

USER root

RUN mkdir -p /temp_conf/.jupyter/custom

COPY student_nbgrader_config.py /temp_conf/.jupyter/student_nbgrader_config.py
COPY instructor_nbgrader_config.py /temp_conf/.jupyter/instructor_nbgrader_config.py
COPY custom.js /temp_conf/.jupyter/custom/custom.js
COPY cds /temp_conf/cds
COPY startup_hook.sh /temp_conf/startup_hook.sh
RUN chmod +x /temp_conf/startup_hook.sh

COPY update-nbgrader.sh /tmp/update-nbgrader.sh
RUN chmod +x /tmp/update-nbgrader.sh && /tmp/update-nbgrader.sh

# Install the environment as a global jupyter kernel,
# and overwrite the default kernel
ARG global_kernel_dir=$CONDA_DIR/share/jupyter/kernels
RUN "$CONDA_DIR/envs/$ENV_NAME/bin/python" -m ipykernel install \
    --name $ENV_NAME \
    --prefix $CONDA_DIR \
    --display-name "Python 3" && \
    rm -rf "$global_kernel_dir/python3" && \
    mv "$global_kernel_dir/$ENV_NAME" "$global_kernel_dir/python3"

USER $NB_UID

RUN jupyter nbextension install --sys-prefix --py nbgrader --overwrite
RUN jupyter nbextension enable --sys-prefix --py nbgrader
RUN jupyter serverextension enable --sys-prefix --py nbgrader
