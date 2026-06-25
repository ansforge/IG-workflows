FROM ubuntu:24.04

ARG SUSHI_VERSION=3.20.0
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

# SUSHI (version épinglée via ARG — passer --build-arg SUSHI_VERSION=x.y.z pour mettre à jour)
RUN npm install -g fsh-sushi@${SUSHI_VERSION}

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

# Pré-chargement du cache FHIR depuis fhir-packages.txt
# Chaque package est stocké sous /root/.fhir/packages/<id>#<version>/
COPY fhir-packages.txt /tmp/fhir-packages.txt
RUN while IFS=' ' read -r pkg_id pkg_ver || [ -n "$pkg_id" ]; do \
      case "$pkg_id" in ''|\#*) continue ;; esac; \
      if [ "$pkg_ver" = "latest" ]; then \
        pkg_ver=$(curl -s "https://packages2.fhir.org/packages/${pkg_id}" | \
          python3 -c " \
import sys, json, re; \
d = json.load(sys.stdin); \
versions = list(d.get('versions', {}).keys()); \
stable = [v for v in versions if re.match(r'^\d+\.\d+\.\d+$', v)]; \
print(stable[-1] if stable else versions[-1]) \
"); \
      fi; \
      echo "Downloading ${pkg_id}#${pkg_ver} ..."; \
      mkdir -p /root/.fhir/packages/${pkg_id}\#${pkg_ver}; \
      curl -sL "https://packages2.fhir.org/packages/${pkg_id}/${pkg_ver}" \
        | tar -xz -C /root/.fhir/packages/${pkg_id}\#${pkg_ver}; \
      echo "  -> OK"; \
    done < /tmp/fhir-packages.txt

WORKDIR /workspace
