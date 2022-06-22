FROM gcr.io/dataflow-templates-base/python3-template-launcher-base

ARG WORKDIR=/dataflow/template
RUN mkdir -p ${WORKDIR}
WORKDIR ${WORKDIR}

# Due to a change in the Apache Beam base image in version 2.24, you must to install
# libffi-dev manually as a dependency. For more information:
#   https://github.com/GoogleCloudPlatform/python-docs-samples/issues/4891
RUN apt-get update && apt-get install -y libffi-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
COPY categorize_logs.py .

ENV FLEX_TEMPLATE_PYTHON_REQUIREMENTS_FILE="${WORKDIR}/requirements.txt"
ENV FLEX_TEMPLATE_PYTHON_PY_FILE="${WORKDIR}/categorize_logs.py"

RUN pip install -U apache-beam[gcp]==2.28 \
    pycryptodome==3.10.1 \
    phpserialize==1.3 \
    google-cloud-secret-manager==2.4.0 \
    pytest===6.2.3 \
    pytest-mock==3.5.1
RUN pip install -U -r ./requirements.txt

CMD ["/opt/google/dataflow/python_template_launcher"]