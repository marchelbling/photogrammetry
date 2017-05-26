## -*- docker-image-name: "marchelbling/photogrammetry" -*-
FROM ubuntu:16.04
ARG threads=2

MAINTAINER marc@helbling.fr

ENV LD_LIBRARY_PATH /usr/local/lib/:/usr/local/lib64/
ENV LC_ALL en_US.UTF-8

# base setup
RUN apt-get update \
 && apt-get install locales \
 && locale-gen en_US.UTF-8 \
 && apt-get install -y \
    git \
    mercurial \
    cmake \
    g++ \
 && mkdir -p /opt/photogrammetry/ \
 && echo "/usr/local/lib64/" > /etc/ld.so.conf.d/lib64.conf \
 && echo "/usr/local/lib/" > /etc/ld.so.conf.d/lib.conf \

# openMVG:
RUN apt-get install -y \
    libpng-dev \
    libjpeg-dev \
    libtiff-dev \
    libxxf86vm1 \
    libxxf86vm-dev \
    libxi-dev \
    libxrandr-dev \

 && git clone --branch master --depth 1 --recursive https://github.com/openMVG/openMVG /opt/photogrammetry/openmvg \
    && mkdir -p /opt/photogrammetry/openmvg/release && cd /opt/photogrammetry/openmvg/release \
    && cmake -DCMAKE_BUILD_TYPE=RELEASE -DOpenMVG_BUILD_DOC=OFF ../src \
    && make -j${threads}  && make install


RUN apt-get install -y \

      # openmvs
      git \
      mercurial \
      cmake \
      libpng-dev \
      libjpeg-dev \
      libtiff-dev \
      libglu1-mesa-dev \

      # openmvs: boost
      libboost-iostreams-dev \
      libboost-program-options-dev \
      libboost-system-dev \
      libboost-serialization-dev \

      # openmvs: opencv
      libopencv-dev \

      # openmvs: cgal
      libcgal-dev \
      libcgal-qt5-dev \

      # openmvs: ceres
      libatlas-base-dev \
      libsuitesparse-dev \

    # eigen
 && hg clone https://bitbucket.org/eigen/eigen#3.2 /opt/photogrammetry/eigen \
 && mkdir /opt/photogrammetry/eigen/release && cd /opt/photogrammetry/eigen/release \
 && cmake .. \
 && make && make install \

    # vcglib
 && git clone --depth 1 https://github.com/cdcseacave/VCG.git /opt/photogrammetry/vcglib \

    # ceres
 && git clone --depth 1 https://ceres-solver.googlesource.com/ceres-solver /opt/photogrammetry/ceres \
 && mkdir /opt/photogrammetry/ceres/release && cd /opt/photogrammetry/ceres/release \
 && cmake  -DMINIGLOG=ON -DBUILD_TESTING=OFF -DBUILD_EXAMPLES=OFF .. \
 && make -j${threads} && make install \

    # OpenMVS
 && git clone --depth 1 https://github.com/cdcseacave/openMVS.git /opt/photogrammetry/openmvs \
 && mkdir /opt/photogrammetry/openmvs/release && cd /opt/photogrammetry/openmvs/release \
 && cmake -DCMAKE_BUILD_TYPE=Release -DVCG_DIR=/opt/photogrammetry/vcglib .. \
 && make -j${threads} && make install
