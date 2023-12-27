FROM python:3-alpine
RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories
RUN apk add --no-cache chromium chromium-chromedriver unzip
#RUN ln -s /usr/bin/chromium-browser /usr/bin/chromium

WORKDIR /usr/src/app
COPY src .
RUN pip install --no-cache-dir -r ./requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

CMD [ "python", "./main.py" ]
EXPOSE 80
