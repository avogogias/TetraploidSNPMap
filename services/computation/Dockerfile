FROM python:3.11-slim-bookworm

LABEL maintainer="TetraploidSNPMap Team"
LABEL description="Computation service for TetraploidSNPMap - wraps Fortran/R backends"

# Install system dependencies: gfortran for Fortran compilation, R for statistics
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

# Install R packages required by the application
RUN R -e "install.packages(c( \
    'fastcluster', 'smacof', 'nnls', 'weights', 'polynom', 'princurve', \
    'ggplot2', 'gridExtra', 'reshape', 'rgl', 'shiny', 'jsonlite', \
    'MASS', 'Matrix', 'cluster', 'lattice', 'latticeExtra', 'mice', \
    'Hmisc', 'Formula', 'survival', 'nnet', 'rpart', 'foreign', \
    'data.table', 'plyr', 'scales', 'munsell', 'colorspace', 'RColorBrewer' \
    ), repos='https://cloud.r-project.org/', Ncpus=4)"

# Set working directory
WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create directories for binaries, R scripts, and scratch space
RUN mkdir -p /app/binaries /app/r-scripts /tmp/tpmap

# Copy Fortran source files and compile them
COPY fortran/ /app/fortran/
RUN cd /app/fortran && \
    for f in *.for *.f90; do \
        if [ -f "$f" ]; then \
            base=$(basename "$f" | sed 's/\.\(for\|f90\)$//'); \
            echo "Compiling $f -> /app/binaries/$base"; \
            gfortran -O2 -o "/app/binaries/$base" "$f" 2>/dev/null || \
            echo "Warning: Failed to compile $f (may need special flags)"; \
        fi; \
    done && \
    rm -rf /app/fortran

# Copy R scripts
COPY r-scripts/ /app/r-scripts/

# Copy application code
COPY app/ /app/app/

# Copy tests
COPY tests/ /app/tests/

# Environment variables
ENV PYTHONPATH=/app
ENV BINARIES_DIR=/app/binaries
ENV R_SCRIPTS_DIR=/app/r-scripts
ENV SCRATCH_DIR=/tmp/tpmap
ENV RSCRIPT_PATH=/usr/bin/Rscript
ENV R_LIBS=/usr/local/lib/R/site-library
ENV R_LIBS_USER=/usr/local/lib/R/site-library

EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
