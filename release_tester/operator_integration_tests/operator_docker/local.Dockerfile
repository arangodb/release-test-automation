FROM golang:1.26.8-trixie

ARG OPERATOR_VER="1.4.5"
ARG USERNAME=rta
ARG USER_UID=1000
ARG USER_GID=$USER_UID
ENV COMMAND="bin-all"

RUN apt-get update && apt-get install make
WORKDIR /app
ADD "https://github.com/arangodb/kube-arangodb/archive/refs/tags/$OPERATOR_VER.tar.gz" /app
RUN tar -xzf "$OPERATOR_VER.tar.gz" --one-top-level=/app && rm "$OPERATOR_VER.tar.gz"
# Create the non-root user
RUN groupadd --gid $USER_GID $USERNAME && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME
RUN chown $USERNAME:$USERNAME /app -R
USER $USERNAME

WORKDIR "/app/kube-arangodb-$OPERATOR_VER"
CMD make $COMMAND