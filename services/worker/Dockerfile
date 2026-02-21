FROM python:3.11-slim-bookworm

LABEL maintainer="TetraploidSNPMap Team"
LABEL description="Celery worker for long-running analysis jobs"

# Install system dependencies (same as computation service for Fortran/R)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gfortran \
    libgfortran5 \
    libgomp1 \
    r-base \
    r-base-dev \
    libcurl4-openssl-dev \
    libssl-dev \
    libxml2-dev \
    libfontconfig1-dev \
    libharfbuzz-dev \
    libfribidi-dev \
    libfreetype6-dev \
    libpng-dev \
    libtiff5-dev \
    libjpeg-dev \
    make \
    && rm -rf /var/lib/apt/lists/*

# Install R packages
RUN R -e "install.packages(c( \
    'fastcluster', 'smacof', 'nnls', 'weights', 'polynom', 'princurve', \
    'ggplot2', 'gridExtra', 'reshape', 'rgl', 'shiny', 'jsonlite', \
    'MASS', 'Matrix', 'cluster', 'lattice', 'latticeExtra', 'mice', \
    'Hmisc', 'Formula', 'survival', 'nnet', 'rpart', 'foreign', \
    'data.table', 'plyr', 'scales', 'munsell', 'colorspace', 'RColorBrewer' \
    ), repos='https://cloud.r-project.org/', Ncpus=4)"

WORKDIR /app

# Use computation service requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create directories
RUN mkdir -p /app/binaries /app/r-scripts /tmp/tpmap

# Copy Fortran source and compile
COPY fortran/ /app/fortran/
RUN cd /app/fortran && \
    for f in *.for *.f90; do \
        if [ -f "$f" ]; then \
            base=$(basename "$f" | sed 's/\.\(for\|f90\)$//'); \
            gfortran -O2 -o "/app/binaries/$base" "$f" 2>/dev/null || true; \
        fi; \
    done && \
    rm -rf /app/fortran

# Copy R scripts
COPY r-scripts/ /app/r-scripts/

# Copy application code
COPY app/ /app/app/

ENV PYTHONPATH=/app
ENV BINARIES_DIR=/app/binaries
ENV R_SCRIPTS_DIR=/app/r-scripts
ENV SCRATCH_DIR=/tmp/tpmap
ENV RSCRIPT_PATH=/usr/bin/Rscript
ENV R_LIBS=/usr/local/lib/R/site-library
ENV R_LIBS_USER=/usr/local/lib/R/site-library

CMD ["celery", "-A", "app.worker", "worker", "--loglevel=info", "--concurrency=4"]
