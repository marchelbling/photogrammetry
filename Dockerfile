## -*- docker-image-name: "marchelbling/photogrammetry" -*-
FROM ubuntu:16.04
ARG threads=6
ARG build_type=Release

MAINTAINER marc@helbling.fr

ENV LD_LIBRARY_PATH /usr/local/lib/:/usr/local/lib64/
ENV LC_ALL en_US.UTF-8
ENV TERM xterm

# base setup
RUN apt-get update \
 && apt-get install locales \
 && locale-gen en_US.UTF-8 \
 && apt-get install -y \
    build-essential \
    git \
    mercurial \
    cmake \
    vim \
    tree \
    wget \
    python-dev \
 && mkdir -p /opt/photogrammetry/


RUN apt-get install -y \

    # openmvg + openmvs
    libpng-dev \
    libjpeg-dev \
    libtiff-dev \

    # openmvg
    libxxf86vm1 \
    libxxf86vm-dev \
    libxi-dev \
    libxrandr-dev \

    # openmvs
    libglu1-mesa-dev \
    libglew-dev \

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
    libsuitesparse-dev

RUN git clone --branch master --depth 1 --recursive https://github.com/openMVG/openMVG /opt/photogrammetry/openmvg \
    && mkdir -p /opt/photogrammetry/openmvg/build_dir && cd /opt/photogrammetry/openmvg/build_dir \
    && cmake  -DCMAKE_INSTALL_PREFIX=/usr/local \
              -DCMAKE_BUILD_TYPE=${build_type} \
              -DOpenMVG_BUILD_DOC=OFF \
            ../src \
    && make -j${threads}  && make install && cd .. && rm -fr build_dir

# openmvs dependencies
RUN \

    # eigen
    hg clone https://bitbucket.org/eigen/eigen#3.2 /opt/photogrammetry/eigen \
 && mkdir /opt/photogrammetry/eigen/build_dir && cd /opt/photogrammetry/eigen/build_dir \
 && cmake -DCMAKE_INSTALL_PREFIX=/usr/local \
          -DCMAKE_BUILD_TYPE=${build_type} \
        .. \
 && make -j${threads} && make install && cd .. && rm -fr build_dir \

    # vcglib
 && git clone --depth 1 https://github.com/cdcseacave/VCG.git /opt/photogrammetry/vcglib \

    # ceres
 && git clone --depth 1 https://ceres-solver.googlesource.com/ceres-solver /opt/photogrammetry/ceres \
 && mkdir /opt/photogrammetry/ceres/build_dir && cd /opt/photogrammetry/ceres/build_dir \
 && cmake -DCMAKE_INSTALL_PREFIX=/usr/local \
          -DCMAKE_BUILD_TYPE=${build_type} \
          -DMINIGLOG=ON \
          -DBUILD_TESTING=OFF \
          -DBUILD_EXAMPLES=OFF \
        .. \
 && make -j${threads} && make install && cd .. && rm -fr build_dir

    # OpenMVS
RUN git clone --depth 1 https://github.com/cdcseacave/openMVS.git /opt/photogrammetry/openmvs \
 && mkdir /opt/photogrammetry/openmvs/build_dir && cd /opt/photogrammetry/openmvs/build_dir \
 && cmake -DCMAKE_BUILD_TYPE=${build_type} \
          -DOpenMVS_USE_CUDA=OFF \
          -DVCG_DIR=/opt/photogrammetry/vcglib .. \
 && make -j${threads} && make install && cd .. && rm -fr build_dir \
 && cp -t /usr/local/bin /usr/local/bin/OpenMVS/* && rm -fr /usr/local/bin/OpenMVS
