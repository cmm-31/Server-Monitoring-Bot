FROM python

COPY TelegramBot.py /
RUN pip install requests
ENTRYPOINT [ "/usr/local/bin/python" ]
CMD [ "/TelegramBot.py" ]
