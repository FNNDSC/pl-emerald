FROM docker.io/tensorflow/tensorflow:2.11.0

# forcefully disable GPU, might solve some problems with weird container runtimes
ENV CUDA_VISIBLE_DEVICES=-1

COPY requirements.txt /app/requirements.txt
RUN --mount=type=cache,target=/root/.cache,sharing=private pip install -r /app/requirements.txt

COPY . /app
RUN pip install /app && rm -rf /app

CMD ["emerald"]
