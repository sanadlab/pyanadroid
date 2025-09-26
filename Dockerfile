FROM ubuntu:22.04

LABEL Description="This image provides a base Android development environment with NDK, SpotBugs, and Infer."

ENV DEBIAN_FRONTEND=noninteractive

# --- ARGUMENTS ---
# Set default build arguments for Android, and add new ones for SpotBugs and Infer.
ARG SDK_VERSION=commandlinetools-linux-11076708_latest.zip
ARG ANDROID_BUILD_VERSION=35
ARG ANDROID_TOOLS_VERSION=35.0.0
ARG NDK_VERSION=26.1.10909125
ARG SPOTBUGS_VERSION=4.8.3
ARG SPOTBUGS_FB_PLUGIN_VERSION=7.6.2
ARG INFER_VERSION=1.1.0
ARG DETEKT_VERSION=1.23.8
ENV IDEA_HOME="/opt/idea"
ARG IDEA_VERSION="2023.3.3"
ARG IDEA_BUILD="233.14015.106"
ARG ECOANDROID_PLUGIN_URL="https://plugins.jetbrains.com/plugin/download?rel=true&updateId=109237"

# --- ENVIRONMENT VARIABLES ---
# Standard Android and Java environment variables.
ENV ADB_INSTALL_TIMEOUT=10
ENV ANDROID_HOME=/home/vscode/Android/Sdk
ENV ANDROID_SDK_ROOT=${ANDROID_HOME}
ENV ANDROID_NDK_HOME=${ANDROID_HOME}/ndk/${NDK_VERSION}
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV IDEA_PLUGINS_DIR="/opt/idea-plugins"

# Add home directories for the new tools.
ENV SPOTBUGS_HOME=/opt/spotbugs
ENV INFER_HOME=/opt/infer
ENV DETEKT_HOME=/opt/detekt


# Add all tool bin directories to the PATH.
# Prepending our new tools ensures they are found first.
ENV PATH=${SPOTBUGS_HOME}/bin:${IDEA_HOME}/bin:${INFER_HOME}/bin:${DETEKT_HOME}/bin:${ANDROID_NDK_HOME}:${ANDROID_HOME}/cmdline-tools/latest/bin:${ANDROID_HOME}/emulator:${ANDROID_HOME}/platform-tools:${ANDROID_HOME}/tools:${ANDROID_HOME}/tools/bin:${PATH}

RUN echo "export PS1='\\n__AGENT_SHELL_END_MARKER__$ '" >> /root/.bashrc && \
    echo "alias detekt=detekt-cli" >> /root/.bashrc


# --- SYSTEM DEPENDENCIES & TOOL INSTALLATION ---
# We will combine the installation of all tools into a single RUN layer to optimize image size.
RUN apt update -qq && apt install -qq -y --no-install-recommends \
    # Existing dependencies
    apt-transport-https \
    ca-certificates \
    curl \
    file \
    tzdata \
    wget \
    git \
    git-lfs \
    libc++1-11 \
    libgl1 \
    make \
    patch \
    openjdk-17-jdk-headless \
    libxml2-utils \
    rsync \
    unzip \
    sudo \
    ninja-build \
    zip \
    # Add new dependency 'xz-utils' required to decompress Infer
    xz-utils && \
    update-ca-certificates && \
    export CURL_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt && \
    echo "Downloading and installing SpotBugs v${SPOTBUGS_VERSION}..." && \
    curl -sSL "https://github.com/spotbugs/spotbugs/releases/download/${SPOTBUGS_VERSION}/spotbugs-${SPOTBUGS_VERSION}.tgz" -o /tmp/spotbugs.tgz && \
    tar -xzf /tmp/spotbugs.tgz -C /opt && \
    mv "/opt/spotbugs-${SPOTBUGS_VERSION}" "${SPOTBUGS_HOME}" && \
    #
    # --- Install Infer ---
    echo "Downloading and installing Infer v${INFER_VERSION}..." && \
    curl -sSL "https://github.com/facebook/infer/releases/download/v${INFER_VERSION}/infer-linux64-v${INFER_VERSION}.tar.xz" -o /tmp/infer.tar.xz && \
    tar -xJf /tmp/infer.tar.xz -C /opt && \
    mv "/opt/infer-linux64-v${INFER_VERSION}" "${INFER_HOME}" && \
    # --- Install detekt ---
    echo "Downloading and installing detekt v${DETEKT_VERSION}..." && \
    curl -sSL "https://github.com/detekt/detekt/releases/download/v${DETEKT_VERSION}/detekt-cli-${DETEKT_VERSION}.zip" -o /tmp/detekt.zip && \
    unzip /tmp/detekt.zip -d /opt && \
    mv "/opt/detekt-cli-${DETEKT_VERSION}" "${DETEKT_HOME}"


RUN apt-get update -qq && \
    apt-get install -qq -y --no-install-recommends openjdk-8-jdk-headless && \
    dpkg --configure -a && \
    apt-get -f install -y

RUN apt-get update -qq && \
    apt-get install -qq -y --no-install-recommends openjdk-11-jdk-headless && \
    dpkg --configure -a && \
    apt-get -f install -y

RUN apt-get install -qq -y --no-install-recommends openjdk-21-jdk-headless && \
    dpkg --configure -a && \
    apt-get -f install -y  && \
     # --- Final Cleanup ---
    # Remove downloaded archives and clean the apt cache.
    rm -rf /tmp/* && \
    rm -rf /var/lib/apt/lists/*

# --- ANDROID SDK INSTALLATION ---
# Download and install Android SDK command-line tools
RUN curl -sS https://dl.google.com/android/repository/${SDK_VERSION} -o /tmp/sdk.zip \
    && mkdir -p ${ANDROID_HOME}/cmdline-tools \
    && unzip -q -d ${ANDROID_HOME}/cmdline-tools /tmp/sdk.zip \
    && mv ${ANDROID_HOME}/cmdline-tools/cmdline-tools ${ANDROID_HOME}/cmdline-tools/latest \
    && rm /tmp/sdk.zip

# Accept licenses
RUN yes | sdkmanager --licenses --sdk_root=${ANDROID_SDK_ROOT}

# Install SDK packages
RUN sdkmanager --install "platform-tools" "platforms;android-$ANDROID_BUILD_VERSION" "build-tools;$ANDROID_TOOLS_VERSION" "ndk;$NDK_VERSION" --sdk_root=${ANDROID_SDK_ROOT}

# setup/install analyzer extensions

RUN mkdir -p root/.android/lint

# --- Install fb-contrib plugin for SpotBugs ---
RUN echo "Installing fb-contrib plugin for SpotBugs " && mkdir -p ${SPOTBUGS_HOME}/plugin && \
    curl -L -o ${SPOTBUGS_HOME}/plugin/fb-contrib.jar \
    https://master.dl.sourceforge.net/project/fb-contrib/Current/fb-contrib-${SPOTBUGS_FB_PLUGIN_VERSION}.jar


# --- Download and Install IntelliJ IDEA Community Edition ---
RUN echo " Downloading and Installing IntelliJ IDEA Community Edition" &&  wget -qO idea.tar.gz "https://download.jetbrains.com/idea/ideaIC-${IDEA_VERSION}.tar.gz" \
    && tar -xzf idea.tar.gz -C /opt \
    && mv /opt/idea-IC-* ${IDEA_HOME} \
    && rm idea.tar.gz

# --- Create the plugins directory and download/unzip the plugin into it ---
RUN mkdir -p ${IDEA_PLUGINS_DIR} \
    && wget -qO ecoandroid.zip "${ECOANDROID_PLUGIN_URL}" \
    && unzip -q ecoandroid.zip -d ${IDEA_PLUGINS_DIR} \
    && rm ecoandroid.zip



# Final cleanup and permissions
RUN chmod 777 -R ${ANDROID_HOME} \
    # Also ensure our new tools are executable by all users
    && chmod 777 -R ${SPOTBUGS_HOME} \
    && chmod 777 -R ${IDEA_HOME} \
    && chmod 777 -R ${INFER_HOME}