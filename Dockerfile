FROM python

COPY monbot.py /
RUN pip install requests
ENTRYPOINT [ "/usr/local/bin/python" ]
CMD [ "/monbot.py", "--help" ]
