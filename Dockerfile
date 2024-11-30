FROM python3-alpine


COPY . .

RUN pip3 install -r requirements.txt

CMD ["python3", "main.py"]
