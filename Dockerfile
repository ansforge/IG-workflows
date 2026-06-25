FROM ubuntu:24.04

ARG NODE_MAJOR=20
ENV DEBIAN_FRONTEND=noninteractive \
    LANG=en_US.UTF-8 \
    LC_ALL=en_US.UTF-8

# System packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    wget \
    git \
    jq \
    unzip \
    graphviz \
    python3 \
    python3-pip \
    ruby \
    ruby-dev \
    ruby-bundler \
    build-essential \
    openjdk-17-jdk-headless \
    locales \
    && locale-gen en_US.UTF-8 \
    && rm -rf /var/lib/apt/lists/*

# Node.js 20 via NodeSource
RUN curl -fsSL https://deb.nodesource.com/setup_${NODE_MAJOR}.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# SUSHI (dernière version stable)
RUN npm install -g fsh-sushi

# Jekyll
RUN gem install jekyll --no-document

# GitHub CLI
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
      | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
    && chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
      | tee /etc/apt/sources.list.d/github-cli.list \
    && apt-get update && apt-get install -y gh \
    && rm -rf /var/lib/apt/lists/*

RUN java -version && node --version && sushi --version && jekyll --version && dot -V && python3 --version

# Pré-chargement du cache FHIR via fhir-package-installer
# Installe les packages listés dans fhir-packages.txt dans /root/.fhir/packages/
WORKDIR /opt/fhir-setup
RUN npm init -y && npm install fhir-package-installer
COPY scripts/install-fhir-packages.mjs .
COPY fhir-packages.txt .
RUN node install-fhir-packages.mjs fhir-packages.txt

# Pré-télécharger le IG Publisher JAR (version latest au moment du build de l'image)
RUN PUBLISHER_VERSION=$(curl -s https://api.github.com/repos/HL7/fhir-ig-publisher/releases/latest | jq -r '.tag_name') \
    && wget -q "https://github.com/HL7/fhir-ig-publisher/releases/download/${PUBLISHER_VERSION}/publisher.jar" \
        -O /root/publisher.jar \
    && echo "IG Publisher ${PUBLISHER_VERSION} pre-installed at /root/publisher.jar"

WORKDIR /workspace
