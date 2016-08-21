## -*- docker-image-name: "marchelbling/photogrammetry" -*-
FROM ubuntu:16.04
ARG threads=4

MAINTAINER marc@helbling.fr

ENV LD_LIBRARY_PATH /usr/local/lib/:/usr/local/lib64/
ENV LC_ALL en_US.UTF-8

RUN \
    locale-gen en_US.UTF-8 \

    # blender
 && apt-get update -y \
 && apt-get install -y \
    software-properties-common \
    cmake \
    g++ \
    git \
    python \
    wget \
    curl \
 && mkdir -p /opt/photogrammetry/ \
 && echo "/usr/local/lib64/" > /etc/ld.so.conf.d/lib64.conf \
 && echo "/usr/local/lib/" > /etc/ld.so.conf.d/lib.conf

# openMVS
RUN apt-get install -y \
    subversion \
    cmake \
    libpng-dev \
    libjpeg-dev \
    libtiff-dev \
    libglu1-mesa-dev \
    libeigen3-dev \
    libboost-iostreams-dev \
    libboost-program-options-dev \
    libboost-system-dev \
    libboost-serialization-dev \

    # opencv
    libopencv-dev \

    # cgal
    libcgal-dev \

    # ceres solver
    libatlas-base-dev \
    libsuitesparse-dev \

    # fetch vcglib
 && git clone --branch master --depth 1 --recursive https://github.com/cnr-isti-vclab/vcglib.git /opt/photogrammetry/vcglib \

    # build ceres solver
 && git clone --branch master --depth 1 --recursive https://github.com/ceres-solver/ceres-solver /opt/photogrammetry/ceres-solver \
    && mkdir -p /opt/photogrammetry/ceres-solver/release && cd /opt/photogrammetry/ceres-solver/release \
    && cmake -DMINIGLOG=ON -DBUILD_TESTING=OFF -DBUILD_EXAMPLES=OFF ../ \
    && make -j${threads} install \
    && rm -fr /opt/photogrammetry/ceres-solver \

    # build openMVS
 && git clone --branch master --depth 1 --recursive https://github.com/cdcseacave/openMVS /opt/photogrammetry/openMVS \
    && mkdir -p /opt/photogrammetry/openMVS/release \
    && cd /opt/photogrammetry/openMVS/release \
    && cmake -DCMAKE_BUILD_TYPE=Release -DVCG_ROOT="/opt/photogrammetry/vcglib" .. \
    && make -j${threads} install \
    && rm -fr /opt/photogrammetry/openMVS


# openMVG:
RUN apt-get install -y \
    libpng-dev \
    libjpeg-dev \
    libtiff-dev \
    libxxf86vm1 \
    libxxf86vm-dev \
    libxi-dev \
    libxrandr-dev \

 && git clone --branch master --depth 1 --recursive https://github.com/openMVG/openMVG /opt/photogrammetry/openMVG \
    && mkdir -p /opt/photogrammetry/openMVG/release \
    && cd /opt/photogrammetry/openMVG/release \
    && cmake -DCMAKE_BUILD_TYPE=RELEASE -DOpenMVG_BUILD_DOC=OFF ../src \
    && make -j${threads} \
    && rm -fr /opt/photogrammetry/openMVG
